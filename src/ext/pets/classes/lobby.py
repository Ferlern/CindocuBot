from typing import Optional

from disnake import Guild, Member
from src.ext.game.services.games.classes import Player
from src.ext.game.utils import players_to_members
from .game import PetsGame
from .lobby_creators import Lobbies


class Lobby:
    def __init__(
        self,
        guild: Guild,
        creator: Player,
        game: PetsGame,
    ) -> None:
        self._players = set[Player]()
        self._guild = guild
        self._creator = creator
        self._game = game

    @property
    def full(self) -> bool:
        return len(self._players) >= (self._game.max_players or 2)
    
    @property
    def not_enough_players(self) -> bool:
        return len(self._players) < (self._game.min_players or 2)
    
    @property
    def guild(self) -> Guild:
        return self._guild

    @property
    def creator(self) -> Player:
        return self._creator

    @property
    def game(self) -> PetsGame:
        return self._game
    
    @property
    def players(self) -> tuple:
        return tuple(self._players)

    async def start_game(self) -> None:
        self._game.add_players(self.players)
        await self._game.start(self._guild.id)

    def has(self, player: Player) -> bool:
        return player in self._players
    
    def add(self, player: Player) -> None:
        if player.bot:
            return
        self._players.add(player)

    def clear(self) -> None:
        self._players.clear()

    def do_lobby_created(self) -> None:
        Lobbies.creators.add(self._creator)
    
    def undo_lobby_created(self) -> None:
        try: Lobbies.creators.remove(self._creator)
        except: return

    @property
    def is_already_creator(self) -> bool:
        if Lobbies.has_creator(self._creator):
            return True
        
        self.do_lobby_created()
        return False
    
    @property
    def members_to_ping(self) -> Optional[list[Member]]:
        if not self._players:
            return None

        return players_to_members(
            self._guild,
            [player for player in self._players]
        )      

    def __len__(self) -> int:
        return len(self._players)

    def __contains__(self, player: Player) -> bool:
        return player in self._players
