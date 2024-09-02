from __future__ import annotations
from typing import TYPE_CHECKING
import disnake

from src.logger import get_logger
from src.translation import get_translator
from src.ext.pets.classes import PetsGame
from src.ext.game.utils import user_to_player
from src.ext.pets.utils import GameEmbed

if TYPE_CHECKING:
    from .game import PetsGameView


logger = get_logger()
t = get_translator(route='ext.pet_battle')

DICE_ROLL_GIF = "https://media.tenor.com/BZGKCKH8Wp4AAAAi/dice-roll-dice.gif"


class DiceRollView(disnake.ui.View):
    def __init__(self,
        game: PetsGame,
        user: disnake.Member | disnake.User,
        game_view: PetsGameView
    ) -> None:
        super().__init__(timeout=180)
        self.user = user
        self.game = game
        self.game_view = game_view
        self.rolled = False

        (self.hit_chance,
        self.crit_hit_chance,
        self.damage_range) = (
            self.game.calculate_chances(
            user_to_player(self.user)
        ))
        self.damage: int
        self.dices_roll: tuple[int, int]
        self.success: str

        self.add_item(RollButton())

    def _create_embed(self) -> disnake.Embed:
        desc = self._create_embed_desc()
        embed = GameEmbed(
            title = t("dices"),
            description = desc
        )
        embed.set_thumbnail(DICE_ROLL_GIF)
        return embed
    
    def _create_embed_desc(self) -> str:
        if not self.rolled:
            return t(
                'roll_desc',
                hit_chance=self.hit_chance,
                crit_hit_chance=self.crit_hit_chance,
                min_damage=self.damage_range[0],
                max_damage=self.damage_range[1]
            )
        
        return t(
            'rolled_desc',
            hit_chance=self.hit_chance,
            crit_hit_chance=self.crit_hit_chance,
            damage=self.damage,
            d10_1 = self.dices_roll[0],
            d10_2 = self.dices_roll[1],
            success = self.success
        )
    
    async def update_view(
        self,
        interaction: disnake.MessageInteraction
    ) -> None:
        self.rolled = True
        self.clear_items()
        await interaction.response.edit_message(
            embed=self._create_embed(),
            view=self
        )

    async def start_from(
        self,
        interaction: disnake.MessageInteraction
    ):
        await interaction.response.send_message(
            embed=self._create_embed(),
            view=self,
            ephemeral=True
        )
    

class RollButton(disnake.ui.Button):
    view: DiceRollView

    def __init__(self) -> None:
        super().__init__(
            label=t("roll_dices"),
            style=disnake.ButtonStyle.blurple
        )

    async def callback(
        self,
        interaction: disnake.MessageInteraction
    ) -> None:
        view = self.view
        if not view.game.is_your_turn(user_to_player(interaction.user)):
            await interaction.response.send_message(
                t("not_your_turn"), ephemeral=True)
            return

        dices_roll, damage = self._roll_dices()
        success = self._define_success(dices_roll)
        view.damage = damage = view.game.check_for_crit(
            success, damage,
            view.damage_range
        )

        await view.update_view(interaction)
        await view.game.attack_handler(
            success, damage,
            user_to_player(view.user)
        )
        await self.view.game_view.update_view()

    def _roll_dices(self):
        view = self.view

        roll = view.game.roll_dices(view.damage_range)
        view.dices_roll = dices_roll = roll[0:2]
        view.damage = damage = roll[2]
        return dices_roll, damage
    
    def _define_success(self, dices_roll: tuple[int, int]):
        view = self.view

        success = view.game.define_attack_success(
            view.hit_chance,
            view.crit_hit_chance,
            dices_roll
        )
        view.success = success.value
        return success