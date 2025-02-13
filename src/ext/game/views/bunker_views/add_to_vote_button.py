from __future__ import annotations
from typing import TYPE_CHECKING
import disnake

from src.logger import get_logger
from src.translation import get_translator

if TYPE_CHECKING:
    from src.ext.game.views.game_interfaces.bunker import MasterPanelInterface

logger = get_logger()
t = get_translator(route='ext.games')

class AddPlayerToVote(disnake.ui.Button):
    view: MasterPanelInterface

    def __init__(self) -> None:
        super().__init__(
            label=t('add_to_vote_button'),
            style=disnake.ButtonStyle.blurple,
            row=4
        )
    
    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        view = self.view
        vote_player = view.current_player
        accepted = view.game.accept_add_to_vote(vote_player)
        
        if not accepted:
            await interaction.response.send_message(t('already_in_exclude'), ephemeral=True)
            return

        game_data = view.game.game_data
        await interaction.response.send_message(
                t('added_to_vote', player_id=vote_player.player_id)
                + ', '.join([f"<@{player.player_id}>" for player in list(game_data.players_to_exclude)]),
                ephemeral=True
            )
