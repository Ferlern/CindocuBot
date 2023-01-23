from typing import Union, Sequence, Protocol
import disnake


class HasRoleId(Protocol):  # pylint: disable=too-few-public-methods
    @property
    def role_id(self) -> int:
        ...


RolesLikeSeq = Union[
    Sequence[HasRoleId],
    Sequence[disnake.abc.Snowflake],
    Sequence[int],
]


def snowflake_roles_intersection(
    *roles_like_seqs: RolesLikeSeq,
) -> list[disnake.Object]:
    result = None
    for roles_seq in roles_like_seqs:
        if len(roles_seq) == 0:
            return []
        if isinstance(roles_seq[0], int):
            ids_set = set(roles_seq)
        elif hasattr(roles_seq[0], 'role_id'):
            ids_set = {role.role_id for role in roles_seq}  # type: ignore
        elif isinstance(roles_seq[0], disnake.abc.Snowflake):
            ids_set = {role.id for role in roles_seq}  # type: ignore
        else:
            raise TypeError('roles_like object must have id, role_id or be id himself')
        if result is not None:
            result &= ids_set
        else:
            result = ids_set
    return list(disnake.Object(role_id) for role_id in result)  # type: ignore


def filter_assignable(
    roles_like_seq: RolesLikeSeq,
    guild: disnake.Guild,
) -> list[disnake.Role]:
    roles = roles_like_to_roles(roles_like_seq, guild)
    return [role for role in roles if role.is_assignable()]


def roles_like_to_ids(role_like_seq: RolesLikeSeq) -> list[int]:
    if len(role_like_seq) == 0:
        return []
    if isinstance(role_like_seq[0], int):
        return list(role_like_seq)  # type: ignore
    if hasattr(role_like_seq[0], 'role_id'):
        return [role.role_id for role in role_like_seq]  # type: ignore
    if isinstance(role_like_seq[0], disnake.abc.Snowflake):
        return [role.id for role in role_like_seq]  # type: ignore
    raise TypeError('roles_like object must have id, role_id or be id himself')


def roles_like_to_roles(role_like_seq: RolesLikeSeq, guild: disnake.Guild) -> list[disnake.Role]:
    ids = roles_like_to_ids(role_like_seq)
    roles = [guild.get_role(role_id) for role_id in ids]
    return [role for role in roles if role is not None]
