from __future__ import annotations
from typing import TYPE_CHECKING
import random
from enum import Enum

from src.ext.game.services.games.classes.game_state import WrongState
from src.ext.game.services.games.classes import Game, GameState, GameResult, Player
from src.ext.pets.services import get_main_pet
from src.database.models import Pets
from src.translation import get_translator

from .pet import Pet
from .skill import Skill
from .actions import Actions

if TYPE_CHECKING:
    from src.ext.pets.views.journal_paginator import JournalPaginator
    
t = get_translator(route='ext.pet_battle')


class AttackSuccess(Enum):
    SUCCESS = t("success")
    CRIT_SUCCESS = t("crit_success")
    FAILURE = t("failure")


class PetsGame(Game):
    def __init__(self):
        super().__init__()
        self._players = []
        self._pets: dict[Player, Pet] = {}
        self.state = GameState.WAIT_FOR_PLAYER
        self.max_players = 2
        self.min_players = 2
        self.end_game_art_url = "https://i.imgur.com/qljlSvm.png"

        self._turn: int = 0
        self._current_pet: Pet
        self._journal: JournalPaginator | None = None

        self.is_any_poison: tuple[str, int] | None = None


    async def start(self, guild_id: int) -> None:
        self.state = GameState.WAIT_FOR_INPUT
        self._turn += 1
        for player in self._players:
            player_id = player.player_id
            self._pets[player] = self._create_battle_pet(guild_id, player_id)

        cur_pet = self._switch_pets()
        await self._journal_start(cur_pet.name)

    def get_pets(self) -> list[Pet]:
        return list(self._pets.values())
    
    def is_your_turn(self, player: Player) -> bool:
        return self._pets[player] == self._current_pet
        
    async def _journal_start(self, pet_name: str) -> None:
        journal = self._journal
        if not journal:
            return

        await journal.add_row(Actions.START)
        await journal.add_row(Actions.NEW_TURN,
            number=self._turn, pet_name=pet_name)

    def _create_battle_pet(self, guild_id: int, player_id: int) -> Pet:
        pet: Pets = get_main_pet(guild_id, player_id) # type: ignore
        return Pet(
            id = pet.id,
            name = pet.name,
            level = pet.level,
            experience = pet.experience,
            exp_scale = pet.exp_scale,
            spec = pet.spec,
            max_health = pet.max_health,
            health = pet.health,
            strength = pet.strength,
            dexterity = pet.dexterity,
            intellect = pet.intellect
        )
    
    def initialize_journal(self, journal: JournalPaginator) -> None:
        self._journal = journal

    def calculate_chances(
        self,
        player: Player
    ) -> tuple[int, int, tuple[int, int]]:
        attacker = self._pets[player]
        defender = self._get_defender(player)
        return attacker.calculate_chances(defender)
    
    def define_attack_success(
        self,
        hit_chance: int,
        crit_hit_chance: int,
        dices: tuple[int, int]
    ) -> AttackSuccess:
        roll = self._rebuild_dice_rolls(*dices)
        if roll >= hit_chance:
            if roll >= crit_hit_chance:
                return AttackSuccess.CRIT_SUCCESS
            return AttackSuccess.SUCCESS
        return AttackSuccess.FAILURE

    def roll_dices(
        self,
        damage_range: tuple[int, int]
    ) -> tuple[int, int, int]:
        d10_1 = random.randint(0, 9)
        d10_2 = random.randint(0, 9)

        d8 = random.randint(*damage_range)
        return d10_1, d10_2, d8
    
    def _rebuild_dice_rolls(self, dice1: int, dice2: int) -> int:
        if dice1 == 0 and dice2 == 0:
            final_dices = 100
        else:
            final_dices = int(f"{dice1}{dice2}")
        return final_dices
    
    def roll_extra_attack_dices(self, pet: Pet) -> int:
        chance = random.randint(0, 100) >= 50

        if chance:
            modifier = pet.calculate_modifier()
            d_1 = random.randint(1, 3+modifier)
            d_2 = random.randint(1, 3+modifier)
            return d_1 + d_2
        else:
            return 0
        
    def roll_poison_damage_dices(self, pet: Pet) -> int:
        return 1 + pet.calculate_modifier()
    
    async def accept_use_skill(self, skill_id: str, player: Player) -> bool:
        if not self.state == GameState.WAIT_FOR_INPUT:
            raise WrongState("The game is not in playable state")

        attacker = self._pets[player]
        defender = self._get_defender(player)

        damage_skills = {
            "s5": self.roll_poison_damage_dices,
            "s6": self.roll_extra_attack_dices
        }

        damage_skill = damage_skills.get(skill_id)
        if damage_skill:
            damage = damage_skill(attacker)
        else:
            damage = 0

        skill_data, success = attacker.use_skill(
            skill_id=skill_id,
            turn=self._turn,
            defender=defender,
            damage=damage
        )
        if not success:
            return False
        
        await self._journal_skill_use(attacker.name, skill_data)

        if attacker.rage_started:
            await self._next_turn()

        if not defender.is_alive:
            await self._next_turn()

        return True

    def get_skills(self, player: Player) -> list[Skill]:
        pet = self._pets[player]
        return list(pet.skills.values())

    async def attack_handler(
        self,
        success: AttackSuccess,
        damage: int,
        player: Player
    ) -> None:
        if not self.state == GameState.WAIT_FOR_INPUT:
            raise WrongState("The game is not in playable state")

        attacker = self._pets[player]
        defender = self._get_defender(player)

        await self._journal_prepare_attack(attacker.name, defender.name)
        damage = self._handle_hit(success, attacker, defender, damage)
        await self._journal_attack_result(success, defender.name, damage)
        await self._next_turn()

    def check_for_crit(
        self,
        success: AttackSuccess,
        damage: int,
        damage_range: tuple[int, int]
    ) -> int:
        if success is AttackSuccess.CRIT_SUCCESS:
            damage += random.randint(*damage_range)
        return damage

    def _get_defender(self, attacker_player: Player) -> Pet:
        keys = list(self._pets.keys())
        defender_player = keys[1 - keys.index(attacker_player)]
        return self._pets[defender_player]

    async def _journal_prepare_attack(
        self,
        attacker_name: str,
        defender_name: str
    ) -> None:
        await self._journal.add_row( # type: ignore
            Actions.ATTACK,
            attacker=attacker_name,
            defender=defender_name
        )

    async def _journal_attack_success(
        self,
        defender_name: str,
        damage: int
    ) -> None:
        await self._journal.add_row( # type: ignore
            Actions.HIT,
            defender=defender_name,
            damage=damage
        )

    async def _journal_attack_failure(
        self,
        defender_name: str,
    ) -> None:
        await self._journal.add_row( # type: ignore
            Actions.DODGE,
            defender=defender_name
        )

    async def _journal_attack_result(
        self,
        success: AttackSuccess,
        defender_name: str,
        damage: int
    ) -> None:
        match success:
            case AttackSuccess.SUCCESS | AttackSuccess.CRIT_SUCCESS:
                await self._journal_attack_success(
                    defender_name=defender_name,
                    damage=damage
                )
            case AttackSuccess.FAILURE:
                await self._journal_attack_failure(
                    defender_name=defender_name,
                )

    async def _journal_start_turn(
        self,
        pet_name: str
    ) -> None:
        await self._journal.add_row( # type: ignore
            Actions.NEW_TURN, 
            number=self._turn,
            pet_name=pet_name
        )

    async def _journal_skill_use(
        self,
        attacker_name: str,
        skill: Skill
    ) -> None:
        await self._journal.add_row( # type: ignore
            Actions.SKILL_USAGE,
            pet = attacker_name,
            skill = skill.name,
            description = skill.journal_desc
        )

    async def _journal_end(self):
        await self._journal.add_row(Actions.END) # type: ignore

    def _handle_hit(
        self,
        success: AttackSuccess, attacker: Pet,
        defender: Pet, damage: int
    ) -> int:
        if success in (AttackSuccess.SUCCESS, AttackSuccess.CRIT_SUCCESS):
            damage = attacker.attack_target(defender, damage)
            return damage
        
        else:
            return 0

    async def _end_turn(self) -> None:
        self._current_pet.end_turn()

    async def _start_turn(self) -> None:
        self._turn += 1
        cur_pet = self._switch_pets()
        await self._journal_start_turn(cur_pet.name)
        await self._pet_start_turn()

        if self._check_state():
            await self._journal_end()

    async def _next_turn(self) -> None:
        await self._end_turn()
        await self._start_turn()

    async def _pet_start_turn(self) -> None:
        self._current_pet.start_turn(self.poison_callback)
        if self.is_any_poison:
            await self._journal_poison()

    def _switch_pets(self) -> Pet:
        self._current_pet = list(
            self._pets.values()
        )[(self._turn + 1) % 2]

        return self._current_pet

    def poison_callback(
        self, name: str | None, damage: int
    ) -> None:
        if name:
            self.is_any_poison = (name, damage)
            return
        self.is_any_poison = None

    async def _journal_poison(self) -> None:
        if self.is_any_poison:
            name, damage = self.is_any_poison
            await self._journal.add_row( # type: ignore
                Actions.POISON,
                pet = name,
                damage = damage
            )

    def level_up_pets(self) -> None:
        pets = self.get_pets()
        if any(pet.is_alive for pet in pets):
            for pet in pets: pet.update()

    async def force_end(self) -> None:
        await self._journal_end()
        self.state = GameState.END

    def result(self) -> GameResult:
        if self.state is not GameState.END:
            raise WrongState("Can't get results for game that not in END state")
        winners: list[Player] = []
        losers: list[Player] = []
        for player, pet in self._pets.items():
            if not pet.is_alive: losers.append(player)
            else: winners.append(player)
        return GameResult(winners, losers)

    def _check_state(self) -> bool:
        if any(not pet.is_alive for pet in self._pets.values()):
            self.state = GameState.END
            self.level_up_pets()
            return True
        
        return False