from src.ext.game.services.games import BunkerGame
from src.ext.game.services.games.classes.game_settings import GameSettings
from .bunker_info import CHANNEL_ART, RULES


class BunkerSettings(GameSettings):
    def __init__(self, game_type: type[BunkerGame]) -> None:
        self.max_players = 16 # 1 master + 15 players
        self.min_players = 1 # 1 master + 4 players
        self.channel_art = CHANNEL_ART
        self.rules = RULES
        self.game_type = game_type