from dataclasses import dataclass
from typing import Optional
from .base_game import Game


@dataclass
class GameSettings:
    game_type: type[Game]
    channel_art: str
    rules: str
    max_players: Optional[int]
    min_players: Optional[int]
