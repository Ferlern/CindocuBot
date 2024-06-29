from __future__ import annotations
from typing import TYPE_CHECKING
import disnake

from src.logger import get_logger
from src.translation import get_translator

if TYPE_CHECKING:
    from src.ext.game.views.game_interfaces.bunker import MasterPanelInterface

logger = get_logger()
t = get_translator(route='ext.games')

class SubmitAttributeButton(disnake.ui.Button):
    view: MasterPanelInterface

    def __init__(self):
        super().__init__(
            label=t('submit_button'),
            style=disnake.ButtonStyle.green
        )

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        view = self.view
        accepted = view.game.accept_submit_attribute(view.current_player, view.current_attribute)

        if not accepted:
            await interaction.response.send_message(t('no_chosen_attribute'), ephemeral=True)
            return
        
        self.view.current_attribute = (None, None)
        await view.main_interface.message_update()
        await view.update_using(interaction)