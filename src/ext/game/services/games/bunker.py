from disnake import Member, User
from typing import Sequence, Union

from src.translation import get_translator
from src.ext.game.services.bunker_data import BunkerData
from .classes import Player, GameResult, Game, GameState, WrongState
from ..bunker_info import END_GAME_ART


t = get_translator(route='ext.games')


class BunkerGame(Game):
    def __init__(self) -> None:
        super().__init__()
        self._players = []
        self.state = GameState.WAIT_FOR_PLAYER
        self.master: Player
        self.end_game_art_url = END_GAME_ART
        self.game_data: BunkerData

    @property
    def result(self) -> GameResult:
        game_data = self.game_data
        if self.state is not GameState.END:
            raise WrongState("Can't get results for game that not in END state")
        winners = self._players
        losers = list(set(game_data.data) - set(winners))
        winners.remove(self.master)
        return GameResult(winners, losers)

    def start(self) -> None:
        self.state = GameState.WAIT_FOR_INPUT
        players = self._players
        self._players_count = len(players) - 1
        data = BunkerData()
        for player in players:
            data.create_game_data(player, self.master)

        self.game_data = data
        self._check_state()

    def force_end(self) -> None:
        self.state = GameState.END

    def add_players(self, players: Sequence[Player]) -> None:
        for player in players:
            self._players.append(player)

    def accept_add_to_vote(self, player: Player) -> bool:
        game_data = self.game_data
        if self.state is not GameState.WAIT_FOR_INPUT:
            return False
        if not self._check_is_in_players(player):
            return False
        if player in list(game_data.players_to_exclude):
            return False
        game_data.players_to_exclude[player] = 0
        return True

    def accept_anonim_vote(self, player: Player) -> bool:
        if self.state is not GameState.WAIT_FOR_INPUT:
            return False
        if self._check_for_master(player):
            return False
        return True

    def accept_end_vote(self, player: Player) -> bool:
        game_data = self.game_data
        if self.state is not GameState.WAIT_FOR_INPUT:
            return False
        if not self._check_for_master(player):
            return False
        game_data.vote_started = False
        game_data.voted.update(self._players)
        return True

    def accept_exclude(self, player: Player) -> bool:
        game_data = self.game_data
        if self.state is not GameState.WAIT_FOR_INPUT:
            return False
        if game_data.vote_started:
            return False
        self._players.remove(player)
        self._check_state()
        return True

    def accept_make_vote(self, player: Player) -> bool:
        game_data = self.game_data
        if self.state is not GameState.WAIT_FOR_INPUT:
            return False
        try:
            excluding_player = game_data.users_votes[player]
        except:
            return False
        if not excluding_player:
            return False
        if player in game_data.voted:
            return False
        game_data.players_to_exclude[excluding_player] += 1
        game_data.voted.add(player)
        return True

    def accept_master_panel(self, player: Player) -> bool:
        if self.state is not GameState.WAIT_FOR_INPUT:
            return False
        if not self._check_for_master(player):
            return False
        return True

    def accept_show_card(self, player: Player) -> bool:
        if self.state is not GameState.WAIT_FOR_INPUT:
            return False
        if self._check_for_master(player):
            return False
        return True

    def accept_start_vote(self) -> bool:
        game_data = self.game_data
        if self.state is not GameState.WAIT_FOR_INPUT:
            return False
        if not list(game_data.players_to_exclude):
            return False
        if game_data.vote_started:
            return False
        game_data.voted.clear()
        game_data.vote_started = True
        return True

    def accept_submit_attribute(self, player: Player, attribute: tuple) -> bool:
        game_data = self.game_data
        if self.state is not GameState.WAIT_FOR_INPUT:
            return False
        if not self._check_is_in_players(player):
            return False
        if attribute == (None, None):
            return False
        game_data.hidden_data[player].insert(-1, attribute)
        return True

    def _check_for_master(self, player: Player) -> bool:
        if player == self.master:
            return True
        return False

    def _check_is_in_players(self, player: Player) -> bool:
        if player in self.players:
            return True
        return False

    def _check_state(self) -> None:
        if self.state is GameState.WAIT_FOR_INPUT:
            return
        if len(self._players) - 1 <= ((self._players_count) // 2):
             self.state = GameState.END

