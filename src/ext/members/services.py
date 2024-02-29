from peewee import fn

from src.logger import get_logger
from src.database.models import (Guilds, Users, psql_db,
                                 Likes, Members, UserRoles,
                                 WelcomeSettings, RolesInventory)
from src.database.services import get_member, create_related


logger = get_logger()


@create_related(Guilds)
@psql_db.atomic()
def get_welcome_settings(guild_id: int, /) -> WelcomeSettings:
    settings, _ = WelcomeSettings.get_or_create(
        guild_id=guild_id,
    )
    return settings


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
            (UserRoles.role_id << role_ids)  # type: ignore
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


@psql_db.atomic()
def get_inventory_roles(guild_id: int, user_id: int) -> list[RolesInventory]:
    return list((
        RolesInventory.
        select(RolesInventory).
        where(
            (RolesInventory.guild == guild_id) &
            (RolesInventory.user == user_id)
        )  # type: ignore
    ))


@psql_db.atomic()
def get_inventory_role(guild_id: int, user_id: int, role_id: int) -> RolesInventory:
    return RolesInventory.get(
        guild=guild_id,
        user=user_id,
        role_id=role_id,
    )


@psql_db.atomic()
def reset_members_activity(guild_id: int) -> None:
    logger.info('reset all members chat activity to 0')
    (Members
    .update(monthly_chat_activity = 0)
    .where(Members.guild_id == guild_id)
    .execute())


@psql_db.atomic()
def give_activity_rewards(guild_id: int, rewards: dict[int, str]) -> None: 
    logger.info("give monthly rewards to active members")
    awarded = Members.select().order_by(Members.monthly_chat_activity.desc()).limit(len(rewards))
    ids = [str(user.user_id) for user in awarded]
    
    for i in range(len(ids)):
        (Members
        .update({Members.balance: Members.balance + int(rewards[i + 1])})
        .where((Members.user_id == int(ids[i])) & (Members.guild_id == guild_id))
        .execute())