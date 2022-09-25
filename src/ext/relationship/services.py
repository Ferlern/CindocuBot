import time
from typing import Optional
from src.database.models import (Relationships, RelationshipParticipant,
                                 RelationshipsSettings, Users, psql_db,
                                 Guilds)
from src.database.services import create_related


def get_user_relationships_or_none(
    guild_id: int,
    user_id: int,
) -> Optional[Relationships]:
    try:
        return (
            Relationships.
            select(Relationships).
            join(RelationshipParticipant).
            where(  # type: ignore
                (Relationships.guild_id == guild_id) &
                (RelationshipParticipant.user_id == user_id)
            )
        )[0]
    except IndexError:
        return None


@create_related(Guilds, Users, Users)
@psql_db.atomic()
def create_relationships(
    guild_id: int,
    first_user: int,
    second_user: int,
    /,
) -> None:
    rel = Relationships.create(
        guild_id=guild_id,
        creation_time=int(time.time()),
    )
    RelationshipParticipant.insert_many(  # noqa
        [(first_user, rel.id), (second_user, rel.id)],
        [RelationshipParticipant.user_id,
         RelationshipParticipant.relationship_id],
    ).execute()  # type: ignore


@create_related(Guilds)
@psql_db.atomic()
def get_relationships_settings(guild_id: int, /) -> RelationshipsSettings:
    settings, _ = RelationshipsSettings.get_or_create(guild_id=guild_id)
    return settings
