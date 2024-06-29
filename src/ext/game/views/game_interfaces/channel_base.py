from typing import TypeVar, Generic, Optional
import asyncio
from abc import abstractmethod

import disnake

from src.bot import SEBot
from src.logger import get_logger
from src.translation import get_translator
from src.ext.game.services.games.classes import Game, GameState
from src.formatters import ordered_list, to_mention
from src.ext.game.utils import user_to_player

T = TypeVar('T', bound='Game')
logger = get_logger()
t = get_translator(route='ext.games')

AFTER_GAME_CHANNEL_DELETE_TIME = 180

class ChannelGameInterface(Generic[T], disnake.ui.View):
    def __init__(  # pylint: disable=too-many-arguments
        self,
        bot: SEBot,
        guild: disnake.Guild,
        message: disnake.Message,
        game: T,
        *,
        timeout: Optional[int],
    ) -> None:
        super().__init__(timeout=timeout)
        self.game = game
        self.guild = guild
        self.message = message
        self._bot = bot
        game.on_state_change(self._end_game_listener)

    @classmethod
    async def start_from(
        cls,
        inter: disnake.MessageInteraction,
        game: T,
    ) -> None:
        instance = cls(inter.bot, inter.guild, inter.message, game)  # type: ignore
        await inter.response.edit_message(embed=instance.create_embed(), view=instance)

    @abstractmethod
    def create_embed(self) -> disnake.Embed:
        raise NotImplementedError

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        if user_to_player(interaction.author) not in self.game.players:
            await interaction.response.send_message(t('not_a_player'), ephemeral=True)
            return False
        return True

    def _end_game_listener(self, game: Game, state: GameState) -> None:
        if state is not GameState.END:
            logger.debug("ChannelGameListener: Game not in END state")
            return
        logger.debug("ChannelGameListener: Game in END state")
        self.stop()
        asyncio.create_task(self._end_game_update())

    async def _end_game_update(self) -> None:
        message = self.message
        channel = message.channel
        await message.edit(embed=self._create_end_game_embed(), view=None)
        await channel.send(t('end_game_message', jump_url=message.jump_url))
        await asyncio.sleep(AFTER_GAME_CHANNEL_DELETE_TIME)
        if isinstance(channel, disnake.VoiceChannel):
            try:
                await channel.delete()
            except:
                logger.error('channel %s not found or deleted already', channel.name)
                return

    def _create_end_game_embed(self) -> disnake.Embed:
        results = self.game.result
        winners_str = ordered_list(
            results.winners,
            lambda winner: f"{to_mention(winner.player_id)}"
        )
        losers_str = ordered_list(
            results.losers,
            lambda winner: f"{to_mention(winner.player_id)}"
        )
        embed = disnake.Embed(
            title=t('game_results'),
            description=t('voice_game_end', winners=winners_str, losers=losers_str),
            color=0x7B68EE
        )
        embed.set_image(url=self.game.end_game_art_url)
        return embed

    async def on_timeout(self) -> None:
        self.game.force_end()

