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

class MasterPanelButton(disnake.ui.Button):
    view: BunkerDiscordInterface

    def __init__(self):
        super().__init__(
            label=t('master_panel'),
            style=disnake.ButtonStyle.danger
        )

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        view = self.view
        accepted = view.game.accept_master_panel(user_to_player(interaction.user))
            
        if not accepted:
            await interaction.response.send_message(t('only_for_master'), ephemeral=True) 
            return

        master_panel_view = view.master_panel_view

        await interaction.response.defer()
        await interaction.followup.send(
            embed=master_panel_view.create_embed(), 
            ephemeral=True,
            view=master_panel_view
        )

                