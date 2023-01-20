from typing import Union, Sequence, Protocol
import disnake


class HasRoleId(Protocol):  # pylint: disable=too-few-public-methods
    @property
    def role_id(self) -> int:
        ...


def snowflake_roles_intersection(
    *roles_like_seqs: Union[
        Sequence[HasRoleId],
        Sequence[disnake.abc.Snowflake],
        Sequence[int],
    ],
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
