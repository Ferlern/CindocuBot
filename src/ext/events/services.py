from src.logger import get_logger
from src.database.models import (Guilds, EventsSettings, psql_db)
from src.database.services import create_related


logger = get_logger()


@create_related(Guilds)
@psql_db.atomic()
def get_events_settings(guild_id: int, /) -> EventsSettings:
    settings, _ = EventsSettings.get_or_create(
        guild_id=guild_id,
    )
    return settings