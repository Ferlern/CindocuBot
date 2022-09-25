from src.database.models import PersonalVoice, Users, Guilds, psql_db
from src.database.services import create_related


@create_related(Guilds, Users)
@psql_db.atomic()
def has_voice_channel(user_id: int,
                      guild_id: int,
                      /,
                      ) -> bool:
    return bool(PersonalVoice.get_or_none(
        user_id=user_id,
        guild_id=guild_id,
    ))


@create_related(Guilds, Users)
@psql_db.atomic()
def create_voice_channel(user_id: int,
                         guild_id: int,
                         /,
                         voice_id: int
                         ) -> PersonalVoice:
    return PersonalVoice.create(
        user_id=user_id,
        guild_id=guild_id,
        voice_id=voice_id,
    )


@create_related(Guilds, Users)
@psql_db.atomic()
def get_voice_channel(user_id: int,
                      guild_id: int,
                      /,
                      ) -> PersonalVoice:
    return PersonalVoice.get(
        user_id=user_id,
        guild_id=guild_id,
    )


@psql_db.atomic()
def get_voice_channel_by_id(channel_id: int) -> PersonalVoice:
    return PersonalVoice.get(voice_id=channel_id)
