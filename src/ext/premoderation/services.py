from src.database.models import (Users, psql_db, Guilds,
                                 PremoderationSettings, PremoderationItem)
from src.database.services import create_related
from src.logger import get_logger


logger = get_logger()


@create_related(Guilds)
@psql_db.atomic()
def get_premoderation_settings(guild_id: int, /) -> PremoderationSettings:
    settings, _ = PremoderationSettings.get_or_create(
        guild_id=guild_id
    )
    return settings


@create_related(Guilds, Users)
@psql_db.atomic()
def create_premoderation_item(
    guild_id: int,
    user_id: int,
    /,
    content: str,
    channel_id: int,
    urls: list[str],
) -> None:
    PremoderationItem.create(
        guild_id=guild_id,
        author=user_id,
        content=content,
        channel_id=channel_id,
        urls=urls,
    )


@psql_db.atomic()
def delete_items_by_author(
    guild_id: int,
    user_id: int,
) -> None:
    PremoderationItem.delete().where(
        (PremoderationItem.guild_id == guild_id) &
        (PremoderationItem.author == user_id)
    ).execute()  # type: ignore
