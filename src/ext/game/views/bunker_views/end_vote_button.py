from __future__ import annotations
from typing import TYPE_CHECKING
import disnake

from src.logger import get_logger
from src.translation import get_translator
from src.ext.game.utils import user_to_player

if TYPE_CHECKING:
    from src.ext.game.views.game_interfaces.bunker import VoteInterface

logger = get_logger()
t = get_translator(route='ext.games')

class EndVoteButton(disnake.ui.Button):
    view: VoteInterface 

    def __init__(self):
        super().__init__(
            label=t('end_vote_button'),
            style=disnake.ButtonStyle.blurple
        )

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        view = self.view
        accepted = view.game.accept_end_vote(user_to_player(interaction.user))
        
        if not accepted:
            await interaction.response.send_message(t('only_for_master'), ephemeral=True)
            return

        await view.vote_message.edit(embed=view.create_end_embed(), view=None)
        view.game.game_data.clear_vote_data()

            