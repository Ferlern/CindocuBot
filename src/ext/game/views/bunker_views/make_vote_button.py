from __future__ import annotations
from typing import TYPE_CHECKING
import disnake

from src.logger import get_logger
from src.translation import get_translator
from src.ext.game.utils import user_to_player

if TYPE_CHECKING:
    from src.ext.game.views.game_interfaces.bunker import VoteSelectInterface

logger = get_logger()
t = get_translator(route='ext.games')

class MakeVoteButton(disnake.ui.Button):
    view: VoteSelectInterface 

    def __init__(self) -> None:
        super().__init__(
            label=t('make_vote_button'),
            style=disnake.ButtonStyle.green,
        )

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        view = self.view   
        accepted = view.game.accept_make_vote(user_to_player(interaction.user))

        if not accepted:
            await interaction.response.send_message(t('already_voted'), ephemeral=True)
            return 
        
        await view.vote_view.update_message()
        await view.update_using(interaction)