from __future__ import annotations
from typing import TYPE_CHECKING
import disnake

from src.translation import get_translator
from src.logger import get_logger
from src.ext.game.utils import user_to_player

if TYPE_CHECKING:
    from src.ext.game.views.game_interfaces import BunkerDiscordInterface

logger = get_logger()
t = get_translator(route='ext.games')

class CardsSelect(disnake.ui.Select):
    view: BunkerDiscordInterface

    def __init__(self) -> None:
        super().__init__(placeholder=t('info_cards'))


    def update(self) -> None:
        options = [
            disnake.SelectOption(
                label=name
            ) for name in self.view.cards_map
        ]
        self.options = options
        self.placeholder = t('info_cards')

    async def callback(
        self,
        interaction: disnake.MessageInteraction,
        /
    ) -> None:
        if not user_to_player(interaction.user) == self.view.game.master:
            await interaction.response.send_message(
                t('only_for_master'),
                ephemeral=True
            )
            return

        name = self.values[0]
        self.placeholder = name
        self.view.current_card = name
        await interaction.response.edit_message(
            embed=self.view.cards_map[name],
            view=self.view,
        )

    