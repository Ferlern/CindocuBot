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


class VotePlayerSelect(disnake.ui.Select):
    view: VoteSelectInterface 

    def __init__(self) -> None:
        super().__init__(placeholder=t('players_to_exclude'))

    def update(self) -> None:
        options = [
            disnake.SelectOption(
                label=name
            ) for name in self.view.vote_players_map
        ]
        self.options = options

    async def callback(
        self,
        interaction: disnake.MessageInteraction,
        /
    ) -> None:
        view = self.view
        name = self.values[0]
        data = view.vote_players_map
        game_data = view.game.game_data
        
        game_data.users_votes[user_to_player(interaction.user)] = data.get(name)
        await interaction.response.edit_message(view=view)