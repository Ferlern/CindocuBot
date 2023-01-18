from typing import Literal, Union, Sequence, Callable, Any

from disnake import Member, User


def user_mention(user: Union[Member, User]) -> str:
    return user.mention


def user_short_string(user: Union[Member, User]) -> str:
    return f'{user.name}#{user.discriminator}'


def user_long_string(user: Union[Member, User]) -> str:
    return (f'{user.mention}|'
            f'`{user.name}#{user.discriminator}`|'
            f'`{user.id}`')


def from_user_to_user(user: Union[Member, User],
                      another: Union[Member, User],
                      formatter=user_mention
                      ) -> str:
    return (f'{formatter(user)} **->** '
            f'{formatter(another)}')


def to_mention_and_id(
    id_: int,
    type_: Literal['@', '#', '@&'] = '@',
) -> str:
    return f'<{type_}{id_}> | `{id_}`'


def to_mention(
    id_: int,
    type_: Literal['@', '#', '@&'] = '@',
) -> str:
    return f'<{type_}{id_}>'


def ordered_list(
    items: Sequence,
    formatter: Callable[[Any], str] = str,
) -> str:
    items_str = [formatter(item) for item in items]
    items_str = [f'{idx}. {item}' for idx, item in enumerate(items_str, 1)]
    return '\n'.join(items_str)
