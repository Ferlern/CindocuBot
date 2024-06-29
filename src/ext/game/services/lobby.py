from src.ext.game.services.games.classes import Player

from src.ext.economy.services import change_balance, change_balances
from src.ext.game.services.games import Game
from src.ext.game.services.game_ticket import ensure_ticket


class Lobby:
    def __init__(self, guild_id: int, bet: int, game: Game, creator: Player) -> None:
        self.open = True
        self._players = set[Player]()
        self._invited = set[Player]()
        self._creator = creator
        self._guild_id = guild_id
        self._bet = bet
        self._game = game

    @property
    def full(self) -> bool:
        return len(self._players) >= (self._game.max_players or 10)
        
    @property
    def not_enough_players(self) -> bool:
        return len(self._players) < (self._game.min_players or 2)
 
    @property
    def creator(self) -> Player:
        return self._creator

    @property
    def players(self) -> tuple[Player]:
        return tuple(self._players)

    @property
    def bet(self) -> int:
        return self._bet

    @property
    def game(self) -> Game:
        return self._game

    @property
    def invited(self) -> tuple[Player]:
        return tuple(self._invited)

    def start_game(self) -> None:
        self._game.add_players(self.players)
        self._game.start()

    def has(self, player: Player) -> bool:
        return player in self._players

    def is_invited(self, player: Player) -> bool:
        return player in self._invited

    def can_join(self, player: Player) -> bool:
        if self.has(player):
            return False
        if self.full:
            return False
        if not self.open and not self.is_invited(player):
            return False
        return True

    def add(self, player: Player) -> None:
        if not self.can_join(player):
            raise ValueError("This player can't join")

        if not player.bot:
            ensure_ticket(self._guild_id, player.player_id)
            change_balance(self._guild_id, player.player_id, -self._bet)
        else:
            return
        self._players.add(player)

    def remove(self, player: Player) -> None:
        if not player.bot:
            change_balance(self._guild_id, player.player_id, self._bet)
        self._players.remove(player)

    def remove_many(self, players: list[Player]) -> None:
        change_balances(self._guild_id, [player.player_id for player in players], self._bet)
        for player in players:
            self._players.remove(player)

    def clear(self) -> None:
        if len(self._players) > 0:
            change_balances(
                self._guild_id,
                [player.player_id for player in self._players],
                self._bet,
            )
        self._players.clear()

    def invite(self, player: Player) -> None:
        if player.bot:
            return
            self.add(player)
        else:
            self._invited.add(player)

    def __len__(self) -> int:
        return len(self._players)

    def __contains__(self, player: Player) -> bool:
        return player in self._players
