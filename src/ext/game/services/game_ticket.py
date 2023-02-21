from datetime import datetime, timedelta

from src.database.models import psql_db
from src.ext.members.services import get_member
from src.ext.economy.services import change_balance


GAME_TICKET_PRICE = 75


@psql_db.atomic()
def ensure_ticket(guild_id: int, user_id: int) -> None:
    member = get_member(guild_id, user_id)
    if member.game_ticket_until and member.game_ticket_until > datetime.now():
        return

    member = change_balance(guild_id, user_id, -GAME_TICKET_PRICE)
    member.game_ticket_until = datetime.now() + timedelta(days=1)
    member.save()
