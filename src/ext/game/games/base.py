from typing import Callable, Union, TypeVar, Generic, Sequence
import asyncio
from enum import Enum, auto
from abc import abstractmethod, ABC
from dataclasses import dataclass

import disnake

from src.bot import SEBot
from src.logger import get_logger
from src.translation import get_translator
from src.logger import log_calls
from src.discord_views.base_view import BaseView
from src.discord_views.embeds import DefaultEmbed
from src.ext.economy.services import change_balances
from src.formatters import ordered_list, to_mention
from src.ext.game.services import calculate_win_amount


VisionChangeCallback = Callable[[tuple['Player']], None]
StateChangeCallback = Callable[['Game', 'GameState'], None]
T = TypeVar('T', bound='Game')
logger = get_logger()
t = get_translator(route='ext.games')


@dataclass(frozen=True)
class Player:
    player_id: int
    bot: bool


def user_to_player(user: Union[disnake.User, disnake.Member]) -> Player:
    return Player(user.id, user.bot)


class GameState(Enum):
    # TODO move state logic to state machine
    WAIT_FOR_PLAYER = auto()
    WAIT_FOR_INPUT = auto()
    END = auto()


@dataclass(frozen=True)
class GameResult:
    winners: list[Player]
    losers: list[Player]


class WrongState(Exception):
    pass


class Game(ABC):
    _players: list[Player]

    def __init__(self) -> None:
        self._vision_change_callbacks: list[VisionChangeCallback] = []
        self._state_change_callbacks: list[StateChangeCallback] = []

    # TODO move events logic somewhere else
    def on_vision_change(self, callback: VisionChangeCallback) -> None:
        self._vision_change_callbacks.append(callback)

    def on_state_change(self, callback: StateChangeCallback) -> None:
        self._state_change_callbacks.append(callback)

    def add_players(self, players: Sequence[Player]) -> None:
        for player in players:
            self._players.append(player)

    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def force_end(self) -> None:
        raise NotImplementedError

    @property
    def state(self) -> GameState:
        return self._state

    @state.setter
    @log_calls()
    def state(self, value) -> None:
        self._state = value
        for callback in self._state_change_callbacks:
            callback(self, self.state)

    @property
    def players(self) -> tuple[Player]:
        return tuple(self._players)

    @property
    @abstractmethod
    def result(self) -> GameResult:
        raise NotImplementedError


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


class SingleDiscordInterface(DiscordInterface[T]):
    async def on_timeout(self) -> None:
        self.game.force_end()

    @abstractmethod
    def create_embed(self) -> disnake.Embed:
        raise NotImplementedError


class MultipleDiscordInterface(Generic[T], BaseView):
    def __init__(self, bot: SEBot, game: T, bet: int) -> None:
        super().__init__()
        self.game = game
        self.bet = bet
        self._bot = bot

        def state_change_callback(game: Game, state: GameState) -> None:
            bot.loop.create_task(self._state_update_handler(game, state))

        def vision_update_callback(players: tuple[Player]) -> None:
            bot.loop.create_task(self._update_vision_handler(players))

        game.on_state_change(state_change_callback)
        game.on_vision_change(vision_update_callback)

    @abstractmethod
    def create_embed(self) -> disnake.Embed:
        raise NotImplementedError

    async def _state_update_handler(self, game: Game, state: GameState) -> None:
        pass

    async def _update_vision_handler(self, players: tuple[Player]) -> None:
        pass

    async def _response(self, inter: disnake.ApplicationCommandInteraction) -> None:
        await inter.response.send_message(embed=self.create_embed(), ephemeral=True)
