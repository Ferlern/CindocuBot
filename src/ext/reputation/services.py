from typing import Literal

from src.database.models import Likes, Users, Guilds, psql_db
from src.database.services import create_related
from src.logger import get_logger


logger = get_logger()


@create_related(Guilds, Users, Users)
@psql_db.atomic()
def change_reputation(
    guild_id: int,
    from_member_id: int,
    to_member_id: int,
    /,
    action: Literal[1, 0, -1]
) -> bool:
    if type == 0:
        instance = Likes.get_or_none(
            guild_id=guild_id,
            user_id=from_member_id,
            to_user_id=to_member_id,
        )
        if instance:
            instance.delete_instance()
            return True
        return False

    instance, _ = Likes.get_or_create(
        guild_id=guild_id,
        user_id=from_member_id,
        to_user_id=to_member_id,
    )
    if instance.type == action:
        return False

    instance.type = action
    instance.save()
    logger.info(
        "%s change reputation for %d on guild %s",
        from_member_id, to_member_id, guild_id,
    )
    return True
