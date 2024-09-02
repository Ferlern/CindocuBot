from src.database.models import Gifts, psql_db
from src.logger import get_logger


logger = get_logger()


@psql_db.atomic()
def get_gifts(
    guild_id: int,
    user_id: int
) -> Gifts:
    gifts_data, _ = Gifts.get_or_create(
        guild = guild_id,
        user = user_id
    )
    return gifts_data


@psql_db.atomic()
def add_activity_present(
    guild_id: int,
    user_id: int,
    amount: int
) -> Gifts:
    gifts_data = get_gifts(guild_id, user_id)
    gifts_data.activity_presents += amount
    gifts_data.save()
    return gifts_data


@psql_db.atomic()
def add_role_peace(
    guild_id: int,
    user_id: int
) -> Gifts:
    gifts_data = get_gifts(guild_id, user_id)
    gifts_data.role += 1
    gifts_data.save()
    return gifts_data


@psql_db.atomic()
def remove_activity_present(
    guild_id: int,
    user_id: int
) -> Gifts:
    gifts_data = get_gifts(guild_id, user_id)
    gifts_data.activity_presents -= 1
    gifts_data.save()
    return gifts_data


@psql_db.atomic()
def get_activity_presents(
    guild_id: int,
    user_id: int
) -> int:
    gifts_data = get_gifts(guild_id, user_id)
    return gifts_data.activity_presents