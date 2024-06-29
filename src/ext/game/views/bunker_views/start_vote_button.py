from __future__ import annotations
from typing import TYPE_CHECKING
import disnake

from src.logger import get_logger
from src.translation import get_translator

if TYPE_CHECKING:
    from src.ext.game.views.game_interfaces.bunker import MasterPanelInterface

logger = get_logger()
t = get_translator(route='ext.games')

class StartVoteButton(disnake.ui.Button):
    view: MasterPanelInterface

    def __init__(self):
        super().__init__(
            label=t('start_vote_button'),
            style=disnake.ButtonStyle.red,
            row=4
        )

    async def callback(self, interaction: disnake.GuildCommandInteraction) -> None:
        view = self.view
        accepted = view.game.accept_start_vote()
        if not accepted:
            await interaction.response.send_message(t('no_players_to_vote'), ephemeral=True) 
            return

        await view.vote_interface.create_message(interaction.channel)
        await interaction.response.edit_message(view=view)

        
    


