from __future__ import annotations
from typing import TYPE_CHECKING
import disnake

from src.logger import get_logger
from src.translation import get_translator

if TYPE_CHECKING:
    from src.ext.game.views.game_interfaces.bunker import MasterPanelInterface

logger = get_logger()
t = get_translator(route='ext.games')


class ExcludeButton(disnake.ui.Button):
    view: MasterPanelInterface

    def __init__(self):
        super().__init__(
            label=t('exclude_button'),
            style=disnake.ButtonStyle.red   
        )

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        view = self.view
        exclude_player = view.current_player
        accepted = view.game.accept_exclude(exclude_player)

        if not accepted:
            await interaction.response.send_message(t('wait_to_vote_end'), ephemeral=True)
            return

        await view.main_interface.message_update()
        await view.update_using(interaction)