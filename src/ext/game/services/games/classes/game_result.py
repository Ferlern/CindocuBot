from dataclasses import dataclass
from .player import Player


@dataclass(frozen=True)
class GameResult:
    winners: list[Player]
    losers: list[Player]
