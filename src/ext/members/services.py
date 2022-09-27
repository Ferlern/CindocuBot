from peewee import fn

from src.logger import get_logger
from src.database.models import (Guilds, Users, psql_db,
                                 Likes, Members, UserRoles)
from src.database.services import get_member, create_related


logger = get_logger()


@psql_db.atomic()
def get_member_reputation(guild_id: int, user_id: int) -> int:
    return (Likes.  # noqa
            select((fn.Sum(Likes.type)).alias('amount')).
            where(
                (Likes.guild_id == guild_id) &
                (Likes.to_user_id == user_id)
            )  # type: ignore
            )[0].amount or 0


@create_related(Guilds, Users)
@psql_db.atomic()
def get_member_roles(guild_id: int, user_id: int, /) -> list[UserRoles]:
    return (UserRoles.
            select(UserRoles).
            where(
                (UserRoles.guild_id == guild_id) &
                (UserRoles.user_id == user_id)
            )  # type: ignore
            )


@create_related(Guilds, Users)
@psql_db.atomic()
def create_member_roles(
    guild_id: int,
    user_id: int,
    /,
    role_ids: list[int],
) -> None:
    logger.info('save roles %s for user %d on guild %d',
                role_ids, user_id, guild_id)
    data = [(guild_id, user_id, role_id)
            for role_id in role_ids]
    UserRoles.insert_many(  # noqa
        data,
        fields=[
            UserRoles.guild_id,
            UserRoles.user_id,
            UserRoles.role_id,
        ]
    ).execute()  # type: ignore


@create_related(Guilds, Users)
@psql_db.atomic()
def delete_member_roles(
    guild_id: int,
    user_id: int,
    /,
    role_ids: list[int],
) -> None:
    logger.info('delete roles %s for user %d on guild %d',
                role_ids, user_id, guild_id)
    (UserRoles.
        delete().
        where(
            (UserRoles.guild_id == guild_id) &
            (UserRoles.user_id == user_id) &
            (UserRoles.role_id << role_ids)
        ).
        execute())  # type: ignore


@psql_db.atomic()
def change_bio(guild_id: int, user_id: int, bio: str) -> Members:
    logger.info("user %d change boi to %s on guild %d",
                user_id, bio, guild_id)
    member = get_member(guild_id, user_id)
    member.biography = bio  # type: ignore
    member.save()
    return member
