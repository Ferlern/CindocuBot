from disnake import User, Member
from typing import Union
from src.ext.game.services.games.classes import Player


def user_to_player(user: Union[User, Member]) -> Player:
    return Player(user.id, user.bot)


def id_to_player(id_: int) -> Player:
    return Player(id_, False)
