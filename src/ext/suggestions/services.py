from typing import Optional
from src.database.models import (SuggestionSettings, Suggestions,
                                 Users, Guilds, psql_db)
from src.database.services import create_related
from src.logger import get_logger


logger = get_logger()


@create_related(Guilds)
@psql_db.atomic()
def get_suggestion_settings(guild_id: int, /) -> SuggestionSettings:
    settings, _ = SuggestionSettings.get_or_create(
        guild_id=guild_id
    )
    return settings


@create_related(Users)
@psql_db.atomic()
def create_suggestion(
    user_id: int,
    /,
    message_id: int,
    guild_id: int,
    channel_id: int,
    text: str,
    url: Optional[str],
) -> None:
    Suggestions.create(
        message_id=message_id,
        guild_id=guild_id,
        channel_id=channel_id,
        text=text,
        url=url,
        author=user_id,
    )
