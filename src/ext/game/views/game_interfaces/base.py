from typing import TypeVar, Generic
import asyncio
from abc import abstractmethod

import disnake

from src.bot import SEBot
from src.logger import get_logger
from src.translation import get_translator
from src.discord_views.embeds import DefaultEmbed
from src.ext.economy.services import change_balances
from src.formatters import ordered_list, to_mention
from src.ext.game.services.calculate_win_amount import calculate_win_amount
from src.ext.game.services.statistic import count_wins
from src.ext.game.services.games.classes import Game, GameState
from src.ext.game.utils import user_to_player

T = TypeVar('T', bound='Game')
logger = get_logger()
t = get_translator(route='ext.games')


class DiscordInterface(Generic[T], disnake.ui.View):
    def __init__(  # pylint: disable=too-many-arguments
        self,
        bot: SEBot,
        guild: disnake.Guild,
        message: disnake.Message,
        game: T,
        bet: int,
        *,
        timeout: int = 180,
    ) -> None:
        super().__init__(timeout=timeout)
        self.game = game
        self.guild = guild
        self.message = message
        self.bet = bet
        self._bot = bot
        game.on_state_change(self._end_game_listener)

    @classmethod
    async def start_from(
        cls,
        inter: disnake.MessageInteraction,
        game: T,
        bet: int,
    ) -> None:
        instance = cls(inter.bot, inter.guild, inter.message, game, bet)  # type: ignore
        await inter.response.edit_message(embed=instance.create_embed(), view=instance)

    @abstractmethod
    def create_embed(self) -> disnake.Embed:
        ...

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        if user_to_player(interaction.author) not in self.game.players:
            await interaction.response.send_message(t('not_a_player'), ephemeral=True)
            return False
        return True

    def _end_game_listener(self, game: Game, state: GameState) -> None:
        if state is not GameState.END:
            logger.debug("TableListener: Game not in END state")
            return
        logger.debug("TableListener: Game in END state")
        result = game.result
        win_amount = calculate_win_amount(len(result.winners), len(game.players), self.bet)

        self.stop()
        asyncio.create_task(self._end_game_update(win_amount))
        self._give_rewards(win_amount)
        count_wins(
            self.guild.id,
            [player.player_id for player in result.winners if not player.bot],
            win_amount - self.bet,
        )

    async def _end_game_update(self, win_amount: int) -> None:
        await asyncio.sleep(3)
        await self.message.edit(  # type: ignore <- message is not None here
            embed=self._create_end_game_embed(win_amount), view=None
        )
        del self.game

    def _create_end_game_embed(self, win_amount: int) -> disnake.Embed:
        results = self.game.result
        winners_str = ordered_list(
            results.winners,
            lambda winner: f"{to_mention(winner.player_id)} — **{win_amount - self.bet:+}**"
        )
        losers_str = ordered_list(
            results.losers,
            lambda winner: f"{to_mention(winner.player_id)} — **{-self.bet}**"
        )
        if len(results.losers) == 0:
            desc = t('no_winners')
        else:
            desc = f'{winners_str}\n\n{losers_str}'
        return DefaultEmbed(
            title=t('game_results'),
            description=desc,
        )

    def _give_rewards(self, win_amount: int) -> None:
        result = self.game.result
        change_balances(
            self.guild.id,
            [player.player_id for player in result.winners],
            win_amount,
        )
