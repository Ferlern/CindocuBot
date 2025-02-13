from src.database.models import psql_db, Guilds, ExperienceSettings, VoiceRewardsSettings
from src.database.services import create_related, get_member
from src.database.models import Members


@create_related(Guilds)
@psql_db.atomic()
def get_experience_settings(guild_id: int, /) -> ExperienceSettings:
    settings, _ = ExperienceSettings.get_or_create(
        guild_id=guild_id
    )
    return settings


@create_related(Guilds)
@psql_db.atomic()
def get_voice_rewards_settings(guild_id: int, /) -> VoiceRewardsSettings:
    settings, _ = VoiceRewardsSettings.get_or_create(
        guild_id=guild_id
    )
    return settings


@psql_db.atomic()
def add_voice_time(
    guild_id: int,
    user_id: int,
    seconds: int,
) -> Members:
    member = get_member(guild_id, user_id)
    member.voice_activity += seconds  # type: ignore
    member.until_present += seconds
    member.save()
    return member


@psql_db.atomic()
def restart_present_counter(
    guild_id: int,
    user_id: int,
    seconds: int
) -> Members:
    member = get_member(guild_id, user_id)
    member.until_present -= seconds
    member.save()
    return member