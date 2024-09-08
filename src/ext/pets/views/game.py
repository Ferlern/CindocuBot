import disnake
from typing import Optional
import asyncio

from src.bot import SEBot
from src.logger import get_logger
from src.translation import get_translator
from src.ext.pets.classes import PetsGame, Pet
from src.ext.pets.services import award_winner
from src.ext.pets.views.journal_paginator import JournalPaginator
from src.ext.pets.utils import GameEmbed, exp_display
from src.ext.game.utils import user_to_player
from src.ext.game.services.games.classes import GameState, Game
from src.formatters import to_mention
from src.utils.experience import pet_lvl_to_exp
from .dice_roll import DiceRollView
from .skill_use import SkillUseView
    

logger = get_logger()
t = get_translator(route='ext.pet_battle')


MONEY_FOR_WIN = 200
MONEY_FOR_LOSE = 100


class PetsGameView(disnake.ui.View):
    def __init__(
        self,
        bot: SEBot,
        game: PetsGame,
        thread: disnake.Thread,
        journal: JournalPaginator
    ) -> None:
        super().__init__(timeout=900)
        self.bot = bot
        self.game = game
        self.thread = thread
        self.journal = journal
        self.message: Optional[disnake.Message] = None

        self.game.initialize_journal(self.journal)
        game.on_state_change(self._end_game_listener)

        self.add_item(AttackButton())
        self.add_item(SkillsButton())

    async def on_timeout(self) -> None:
        await self.game.force_end()

    async def interaction_check(
        self,
        interaction: disnake.MessageInteraction
    ) -> bool:
        if user_to_player(interaction.user) not in self.game._players:
            await interaction.response.send_message(
                t("your_not_in_the_game_err"),
                ephemeral=True
            )
            return False
        return True

    def create_embed(self) -> disnake.Embed:
        desc = self._create_embed_desc()
        embed = GameEmbed(
            title = t("battle_field"),
            description=desc,
        )
        return embed
    
    def _create_embed_desc(self) -> str:
        attacker, defender = self.game.get_pets()
        return (f"```xl\n" + 
        f"'{attacker.name}'\n" +
        f"{t('health')}: {attacker.health} / {attacker.max_health}\n\n\n" +
        f"          '{defender.name}'\n" +
        f"          {t('health')}: {defender.health} / {defender.max_health}\n```")

    async def _create_message(
        self
    ) -> None:
        self.message = await self.thread.send(
            embed=self.create_embed(),
            view=self
        )

    async def start_from(self) -> None:
        await self._create_message()

    async def update_view(self) -> None:
        if not self.message:
            return

        await self.message.edit(
            embed=self.create_embed(),
            view=self
        )

    def _end_game_listener(self, game: Game, state: GameState) -> None:
        if state is not GameState.END:
            logger.debug("PetGameListener: Game not in END state")
            return
        logger.debug("PetGameListener: Game in END state")
        self.stop()
        asyncio.create_task(self._end_game_update())
    
    async def _end_game_update(self) -> None:
        thread = self.thread
        results = self.game.result()

        if not self.define_draw(results):
            award_winner(
                self.thread.guild.id,
                results.winners[0].player_id,
                MONEY_FOR_WIN
            )
            award_winner(
                self.thread.guild.id,
                results.losers[0].player_id,
                MONEY_FOR_LOSE
            )

        
        await thread.send(
            embed=self._create_end_game_embed(results)
        )
        await self._show_pets_updates(results)
        await self.thread.edit(locked=True, archived=True)

    def _create_end_game_embed(self, results) -> disnake.Embed:
        is_draw = self.define_draw(results)
        if is_draw:
            embed = disnake.Embed(
                title = t('game_results'),
                description = t("draw"),
                color=0x7B68EE
            )
            embed.set_image(url = self.game.end_game_art_url)
            return embed

        winners_str = to_mention(results.winners[0].player_id)
        losers_str = to_mention(results.losers[0].player_id)

        embed = disnake.Embed(
            title=t('game_results'),
            description=t('game_end',
                           winners=winners_str,
                           losers=losers_str,
                           amount_win=MONEY_FOR_WIN,
                           amount_lose=MONEY_FOR_LOSE),
            color=0x7B68EE
        )
        embed.set_image(url=self.game.end_game_art_url)
        return embed
    
    def define_draw(self, results) -> bool:
        if len(results.losers) != len(results.winners):
            return True
        return False
    
    async def _show_pets_updates(self, results) -> None:
        pets = self.game.get_pets()
        for pet in pets:
            await self.thread.send(
                embed = self._create_pet_updates_embed(pet, results)
            )

    def _create_pet_updates_embed(self, pet: Pet, results) -> disnake.Embed:
        is_lvl_up = pet.has_leveled_up
        exp_for_game = pet.define_exp(pet.is_alive)
        exp_gain = int(exp_for_game * pet._exp_scale)
        if self.define_draw(results):
            exp_gain = 0
        current_exp_display = exp_display(
            pet.exp, pet_lvl_to_exp(pet.level + 1) - pet_lvl_to_exp(pet.level))
        
        desc = (t("exp_gained", exp=exp_gain) +
            t("current_exp", exp=current_exp_display))
        
        if is_lvl_up:
            desc += t("lvl_gained", lvl=pet.level)
            desc += t("bonus_characteristics",
                      max_health=pet.delta['max_health'],
                      strength=pet.delta['strength'],
                      dexterity=pet.delta['dexterity'],
                      intellect=pet.delta['intellect'])
        
        embed = GameEmbed(title=pet.name, description=desc)
        return embed

class AttackButton(disnake.ui.Button):
    view: PetsGameView

    def __init__(self):
        super().__init__(
            label=t("attack_button"),
            style=disnake.ButtonStyle.red
        )

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        roll_view = DiceRollView(
            self.view.game, interaction.user, self.view
        )
        await roll_view.start_from(interaction)


class SkillsButton(disnake.ui.Button):
    view: PetsGameView

    def __init__(self):
        super().__init__(
            label=t("use_skill_button"),
            style=disnake.ButtonStyle.gray
        )

    async def callback(
        self,
        interaction: disnake.MessageInteraction
    ) -> None:
        skills = self.view.game.get_skills(user_to_player(interaction.user))
        skills_view = SkillUseView(
            self.view.game, interaction.user, self.view, skills
        )
        await skills_view.start_from(interaction)


