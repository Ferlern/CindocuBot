from typing import Generic
from abc import abstractmethod
import disnake
from src.bot import SEBot
from src.discord_views.base_view import BaseView
from src.ext.game.services.games.classes import Game, GameState, Player
from .base import T


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
