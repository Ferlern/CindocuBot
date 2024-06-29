from src.database.models import psql_db, Guilds, GameChannelSettings
from src.database.services import create_related


@create_related(Guilds)
@psql_db.atomic()
def get_game_channel_settings(guild_id: int, /) -> GameChannelSettings:
    settings, _ = GameChannelSettings.get_or_create(
        guild_id=guild_id,
    )
    return settings
