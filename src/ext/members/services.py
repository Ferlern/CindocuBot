from peewee import fn

from src.logger import get_logger
from src.database.models import psql_db, Likes, Members
from src.database.services import get_member


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


@psql_db.atomic()
def change_bio(guild_id: int, user_id: int, bio: str) -> Members:
    logger.info("user %d change boi to %s on guild %d",
                user_id, bio, guild_id)
    member = get_member(guild_id, user_id)
    member.biography = bio  # type: ignore
    member.save()
    return member
