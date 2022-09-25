from src.database.models import (Users, psql_db, Guilds,
                                 History)
from src.database.services import create_related
from src.logger import get_logger


logger = get_logger()


@create_related(Guilds, Users)
@psql_db.atomic()
def make_history(
    guild_id: int,
    user_id: int,
    /,
    name: str,
    description: str,
) -> History:
    action = History.create(
        guild_id=guild_id,
        user_id=user_id,
        action_name=name,
        description=description,
    )
    return action
