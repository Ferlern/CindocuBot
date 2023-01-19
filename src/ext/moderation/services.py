from src.database.models import Members, psql_db, Guilds, ModerationSettings
from src.database.services import get_member, create_related
from src.logger import get_logger


logger = get_logger()


@create_related(Guilds)
@psql_db.atomic()
def get_moderation_settings(guild_id: int, /) -> ModerationSettings:
    settings, _ = ModerationSettings.get_or_create(
        guild_id=guild_id
    )
    return settings


@psql_db.atomic()
def add_warn(
    guild_id: int,
    user_id: int,
) -> Members:
    member = get_member(guild_id, user_id)
    member.warns += 1
    member.save()
    return member


@psql_db.atomic()
def remove_warn(
    guild_id: int,
    user_id: int,
) -> Members:
    member = get_member(guild_id, user_id)
    member.warns -= 1
    member.save()
    return member
