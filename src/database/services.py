from typing import Optional
from functools import wraps

import peewee

from src.database.models import Guilds, Users, Members, psql_db
from src.logger import get_logger


logger = get_logger()


def get_guild_data(guild_id: int) -> Guilds:
    guild_data, created = Guilds.get_or_create(id=guild_id)
    if created:
        logger.info('Discord guild with id %d added', guild_id)
    return guild_data


def get_guild_prefixes(guild_id: int) -> Optional[list[str]]:
    guild_data = get_guild_data(guild_id)
    return guild_data.prefixes  # type: ignore


def create_related(*models: type[peewee.Model]):
    def wrapper(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except peewee.IntegrityError:
                for id_, model in zip(args, models):
                    _, created = model.get_or_create(id=id_)
                    if created:
                        logger.info('%s with pk %d created', model, id_)
                return func(*args, **kwargs)
        return wrapped
    return wrapper


@create_related(Guilds, Users)
@psql_db.atomic()
def get_member(guild_id: int, user_id: int, /) -> Members:
    member, created = Members.get_or_create(guild_id=guild_id, user_id=user_id)
    if created:
        logger.info('Member with id %d created', user_id)
    return member
