import random
from typing import Sequence
from src.translation import get_translator
from .classes import Player, GameResult, Game, GameState, WrongState


t = get_translator(route='ext.games')


class DiceGame(Game):
    def __init__(self) -> None:
        super().__init__()
        self._players = []
        self.state = GameState.WAIT_FOR_PLAYER
        self.data: dict[Player, int] = {}

    @property
    def result(self) -> GameResult:
        if self.state is not GameState.END:
            raise WrongState("Can't get results for game that not in END state")
        max_value = max(self.data.values())
        winners_data = filter(lambda item: item[1] == max_value, self.data.items())
        winners = [data[0] for data in winners_data]
        losers = list(set(self.players) - set(winners))
        return GameResult(winners, losers)

    def start(self) -> None:
        self.state = GameState.WAIT_FOR_INPUT
        self._check_state()

    def force_end(self) -> None:
        self.state = GameState.END

    def add_players(self, players: Sequence[Player]) -> None:
        for player in players:
            self._players.append(player)
            if player.bot:
                self._add_dice_result(player)
        self._check_state()

    def accept_input(self, player: Player) -> bool:
        if self.state is not GameState.WAIT_FOR_INPUT:
            return False
        if player.bot:
            return False
        if player in self.data:
            return False
        self._add_dice_result(player)
        self._check_state()
        return True

    def _add_dice_result(self, player: Player) -> None:
        self.data[player] = random.randint(2, 12)

    def _check_state(self) -> None:
        if self.state is GameState.WAIT_FOR_PLAYER:
            return
        if len(self._players) == len(self.data) >= 2:
            self.state = GameState.END
            return
