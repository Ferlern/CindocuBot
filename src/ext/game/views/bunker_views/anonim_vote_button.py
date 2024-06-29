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

class AnonimVoteButton(disnake.ui.Button):
    view: VoteInterface
    
    def __init__(self):
        super().__init__(
            label=t('anonim_vote_button'),
            style=disnake.ButtonStyle.green
        )

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        view = self.view
        accepted = view.game.accept_anonim_vote(user_to_player(interaction.user))
        if not accepted:
            await interaction.response.send_message(t('master_restricted'), ephemeral=True) 
            return

        vote_select = view.vote_select

        await interaction.response.defer()
        await interaction.followup.send(
            embed=vote_select.create_embed(), 
            ephemeral=True,
            view=vote_select
        )