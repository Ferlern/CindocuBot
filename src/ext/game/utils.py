from disnake import User, Member
from typing import Optional, Union, Iterable

import disnake
from src.ext.game.services.games.classes import Player


def user_to_player(user: Union[User, Member]) -> Player:
    return Player(user.id, user.bot)


def id_to_player(id_: int) -> Player:
    return Player(id_, False)


def player_to_member(guild: disnake.Guild, player: Player) -> Optional[Member]:
    return guild.get_member(player.player_id)


def players_to_members(guild: disnake.Guild, players: Iterable[Player]) -> list[Member]:
    members = map(guild.get_member, [player.player_id for player in players])
    return [member for member in members if member is not None]
