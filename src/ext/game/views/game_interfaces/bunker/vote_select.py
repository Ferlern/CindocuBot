from __future__ import annotations
from typing import TYPE_CHECKING
import disnake

from src.bot import SEBot
from src.logger import get_logger
from src.translation import get_translator
from src.ext.game.utils import player_to_member
from .bunker_base import BunkerGameInterface
from src.ext.game.services.games import BunkerGame
from src.ext.game.views.bunker_views import MakeVoteButton, VotePlayerSelect

if TYPE_CHECKING:
    from .vote import VoteInterface

logger = get_logger()
t = get_translator(route='ext.games')

class VoteSelectInterface(BunkerGameInterface):
    def __init__(
        self,
        bot: SEBot,
        guild: disnake.Guild,
        message: disnake.Message,
        game: BunkerGame,
        vote_view: VoteInterface,
        *,
        timeout = None,
    ) -> None:
        super().__init__(bot, guild, message, game, timeout=timeout)
        self.vote_view = vote_view
        self.create_vote_players_map()

        vote_player_select = VotePlayerSelect()
        self.add_item(vote_player_select)
        self.add_item(MakeVoteButton())

        self._updateable_components = [vote_player_select]
        self._update_components()

    def create_embed(self) -> disnake.Embed:
        self.create_vote_players_map()
        self._update_components()
        return disnake.Embed(
            title=t('vote'),
            description=t('vote_desc'),
            color=0xF3940B,
        )

    def create_vote_players_map(self):
        game_data = self.game.game_data
        self.vote_players_map = {
            player_to_member(self.guild, player).display_name: player # type: ignore
                for player in list(game_data.players_to_exclude)
        }

    async def update_using(self, inter: disnake.MessageInteraction):
        self.create_vote_players_map()
        self._update_components()
        await inter.response.edit_message(embed=self.create_embed(), view=self)

    def _update_components(self) -> None:
        for component in self._updateable_components:
            component.update()
