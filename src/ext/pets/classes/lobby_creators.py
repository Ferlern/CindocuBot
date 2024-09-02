from src.ext.game.services.games.classes import Player

class Lobbies:
    creators: set[Player] = set()

    @staticmethod
    def has_creator(player: Player) -> bool:
        return player in Lobbies.creators