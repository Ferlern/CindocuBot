from typing import Iterable, Union
from disnake import User, Member


def remove_bots(users: Iterable[Union[Member, User]]) -> list[Union[Member, User]]:
    return [user for user in users if not user.bot]
