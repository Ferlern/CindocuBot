import disnake

from src.bot import SEBot
from src.logger import get_logger
from src.translation import get_translator
from .bunker_base import BunkerGameInterface
from src.ext.game.services.games import BunkerGame
from src.ext.game.views.bunker_views import AnonimVoteButton, EndVoteButton
from .vote_select import VoteSelectInterface

logger = get_logger()
t = get_translator(route='ext.games')

class VoteInterface(BunkerGameInterface):
    def __init__(
        self,
        bot: SEBot,
        guild: disnake.Guild,
        game: BunkerGame,
        message: disnake.Message,
        *,
        timeout = None,
    ) -> None:
        super().__init__(bot, guild, message, game, timeout=timeout)
        self.vote_select = VoteSelectInterface(bot, guild, message, game, self)
        self.vote_message: disnake.Message

        self.add_item(AnonimVoteButton())
        self.add_item(EndVoteButton())

    def create_embed(self) -> disnake.Embed:
        desc = self.create_desc()
        return disnake.Embed(
            title=t('vote'),
            description=t('vote_desc') + desc,
            colour=0xF3940B,
        )

    def create_end_embed(self) -> disnake.Embed:
        desc = self.create_desc()
        return disnake.Embed(
            title=t('vote_ended'),
            description=desc,
            colour=0xF3940B,
        )
    
    def create_desc(self) -> str:
        game_data = self.game.game_data
        players_to_exclude = game_data.players_to_exclude
        formatter = lambda vote_player: f"<@{vote_player.player_id}> — {t('bunker_votes', count=players_to_exclude[vote_player])}"
        return '\n'.join([formatter(vote_player) for vote_player in list(players_to_exclude)])

    async def update_message(self):
        await self.vote_message.edit(embed=self.create_embed(), view=self)

    async def create_message(self, channel: disnake.abc.Messageable) -> None:
        message = await channel.send(embed=self.create_embed(), view=self)
        self.vote_message = message
