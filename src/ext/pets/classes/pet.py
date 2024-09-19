from random import randint

from src.ext.pets.services import update_pet
from .specialization import Specialization, SpecUtils
from .skill import Skill
from src.utils.experience import pet_lvl_to_exp


HIT_MULTIPLIER = 0.11   
DODGE_MULTIPLIER = 0.1
CRIT_MULTIPLIER = 0.2
BASE_CRIT_CHANCE = 0.1
BASE_HIT_CHANCE = 0.3
MAX_HIT_CHANCE = 0.80
MAX_CRIT_CHANCE = 0.85
MIN_DAMAGE = 1
MAX_DAMAGE = 8

UNDER_SHIELD_REDUCTION = 5

WINNER_EXP = 10
LOSER_EXP = 5

class Pet:
    def __init__(
        self,
        id: int,
        name: str,
        level: int,
        experience: int,
        exp_scale: float,
        spec: str,
        max_health: int,
        health: int, 
        strength: int,
        dexterity: int,
        intellect: int
    ) -> None:
        self._id = id
        self._name = name
        self._level = level
        self._exp = experience
        self._exp_scale = exp_scale
        self._max_health = max_health
        self._health = health
        self._spec = SpecUtils.get_spec_by_prefix(spec)
        self._strength = strength
        self._dexterity = dexterity
        self._intellect = intellect

        self._skills: dict[str, Skill] = {}
        self._spec.add_skills(self) # type: ignore

        self._last_taken_damage: dict[int, int] = {} # turn: damage
        self._last_turn_health: int = self._health

        self.poison_damage: int = 0

        self.status_effects = {
            "in_rage": 0,
            "under_shield": 0,
            "in_bubble": 0,
            "poisoned": 0,
        }

        self.delta: dict[str, int] = {}

    @property
    def name(self) -> str:
        return self._name
    
    @property
    def level(self) -> int:
        return self._level
    
    @property
    def exp(self) -> int:
        return self._exp
    
    @property
    def max_health(self) -> int:
        return self._max_health

    @property
    def health(self) -> int:
        return self._health
    
    @health.setter
    def health(self, health) -> None:
        self._health = health
    
    @property
    def spec(self) -> Specialization:
        return self._spec # type: ignore
    
    @property
    def strength(self) -> int:
        return self._strength
    
    @property
    def dexterity(self) -> int:
        return self._dexterity
    
    @property
    def intellect(self) -> int:
        return self._intellect
    
    @property
    def skills(self) -> dict[str, Skill]:
        return self._skills
    
    @property
    def under_shield(self) -> bool:
        return self.status_effects["under_shield"] > 0
    
    @property
    def in_bubble(self) -> bool:
        return self.status_effects["in_bubble"] > 0
    
    @in_bubble.setter
    def in_bubble(self, duration: int) -> None:
        self.status_effects["in_bubble"] = duration
    
    @property
    def in_rage(self) -> bool:
        return self.status_effects["in_rage"] > 0
    
    @property
    def rage_started(self) -> bool:
        return self.status_effects["in_rage"] == 2
    
    @property
    def poisoned(self) -> bool:
        return self.status_effects["poisoned"] > 0
    
    @property
    def has_leveled_up(self) -> bool:
        return len(self.delta) > 0

    def take_damage(self, damage: int) -> int:
        # self._last_taken_damage = {turn: damage}

        if self.under_shield:
            damage_reduction = self.calculate_damage_reduction()
            damage = max(0, damage-damage_reduction)

        if self.in_bubble:
            damage = 0
            self.in_bubble = 0

        self._health = max(0, self._health - damage)
        return damage

    def attack_target(self, target: 'Pet', damage: int) -> int:
        return target.take_damage(damage)

    def reverse_last_hp(self) -> None:
        self._health = self._last_turn_health

    def take_poison_damage(self, callback) -> None:
        if self.poisoned:
            damage = self.poison_damage
            if self.in_bubble:
                damage = 0
            callback(self.name, damage)
            self.take_damage(self.poison_damage)

        else:
            callback(None, 0)
        
    def calculate_chances(
        self, target: 'Pet'
    ) -> tuple[int, int, tuple[int, int]]:
        hit_chance = self._calculate_hit_chance(target.dexterity)
        crit_chance = self._calculate_crit_chance(target.intellect)
        crit_damage_chance = round(hit_chance * crit_chance)
        damage_range = self._calculate_damage_range()

        return (
            100 - hit_chance,
            100 - crit_damage_chance,
            damage_range
        )
    
    def use_skill(
        self,
        skill_id: str,
        turn: int,
        defender: 'Pet',
        damage: int
    ) -> tuple[Skill, bool]:
        skill = self._skills[skill_id]
        success = skill.apply(
            turn=turn, attacker=self,
            defender=defender, damage=damage
        )
        return skill, success
    
    def _calculate_hit_chance(self, target_dexterity: int) -> int:
        hit_chance = (
            (self._strength * HIT_MULTIPLIER) -
            (target_dexterity * DODGE_MULTIPLIER)
        )

        if self.in_rage:
            hit_chance = MAX_HIT_CHANCE

        hit_chance = min(hit_chance, MAX_HIT_CHANCE)
        return int(max(hit_chance * 100, BASE_HIT_CHANCE * 100))
    
    def _calculate_crit_chance(self, target_intellect: int) -> float:
        crit_chance = (self._intellect - target_intellect) / 10  + CRIT_MULTIPLIER

        if self.in_rage:
            crit_chance = MAX_CRIT_CHANCE

        crit_chance = min(MAX_CRIT_CHANCE, crit_chance)
        return max(crit_chance, BASE_CRIT_CHANCE)

    def _calculate_damage_range(self) -> tuple[int, int]:
        modifier = self.calculate_modifier()
        min_damage = MIN_DAMAGE + modifier

        if self.in_rage:
            min_damage = int(MAX_DAMAGE / 2 + modifier)

        max_damage = MAX_DAMAGE + modifier
        return (min_damage, max_damage)
    
    def calculate_modifier(self) -> int:
        main_attr = getattr(self, self.spec.main_attr)
        return int((main_attr - 10) / 2)
        
    def calculate_damage_reduction(self) -> int:
        return UNDER_SHIELD_REDUCTION + self.calculate_modifier()
    
    def update_skill_cooldowns(self) -> None:
        for skill in list(self._skills.values()):
            skill.update_cooldown()

    def _remove_affects(self) -> None:
        for affect, value in self.status_effects.items():
            self.status_effects[affect] = max(value - 1, 0)

    def start_turn(self, callback) -> None:
        self.take_poison_damage(callback)
        self.update_skill_cooldowns()

    def end_turn(self) -> None:
        self._last_turn_health = self._health
        self._remove_affects()

    @property
    def is_alive(self) -> bool:
        return self._health > 0
    
    def heal(self, amount: int) -> None:
        self._health = min(self._health + amount, self._max_health)
    
    def update(self) -> None:
        is_winner = self.is_alive
        if not self._level >= 20:
            self._exp += int(self.define_exp(is_winner) * self._exp_scale)
        is_lvl_up = self._check_for_level()

        update_pet(
            self._id, self._level, self._exp, self._max_health,
            self._health, self._strength, self._dexterity,
            self._intellect, is_winner
        )

    def define_exp(self, is_winner: bool) -> int:
        return {
            False: LOSER_EXP,
            True: WINNER_EXP
        }[is_winner]

    def _check_for_level(self) -> bool:
        level = self._level
        exp = self._exp

        required_exp = pet_lvl_to_exp(level + 1) - pet_lvl_to_exp(level)
        if exp >= required_exp:
            self._level += 1
            self._exp -= required_exp
            self._update_stats()
            return True
        
        return False
    
    def _update_stats(self) -> None:
        bonus_health = randint(4, 9)

        old_stats = {
            "max_health": self._max_health,
            "strength": self._strength,
            "dexterity": self._dexterity,
            "intellect": self._intellect,
        }

        self._max_health += bonus_health
        self._health += bonus_health if self._health > 0 else 0
        self._strength += 1
        self._dexterity += 1
        self._intellect += 1

        if self._level % 4 == 0:
            main_attr = self.spec.main_attr
            setattr(self, f"_{main_attr}", getattr(self, main_attr) + 1)

        self.delta = {
            stat: getattr(self, stat) - old_stats[stat]
            for stat in ("max_health", "strength", "dexterity", "intellect")
        }