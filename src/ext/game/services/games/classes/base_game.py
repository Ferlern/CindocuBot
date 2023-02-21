from typing import Callable, Optional, Sequence
from abc import ABC, abstractmethod
from .player import Player
from .game_state import GameState
from .game_result import GameResult


VisionChangeCallback = Callable[[tuple['Player']], None]
StateChangeCallback = Callable[['Game', 'GameState'], None]


class Game(ABC):
    _players: list[Player]

    def __init__(self) -> None:
        self._vision_change_callbacks: list[VisionChangeCallback] = []
        self._state_change_callbacks: list[StateChangeCallback] = []
        self.max_players: Optional[int] = None

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
