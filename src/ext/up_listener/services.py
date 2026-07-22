from datetime import datetime
from typing import Optional

from src.database.models import Guilds, Reminders, ReminderSettings, psql_db
from src.database.services import create_related


@create_related(Guilds)
@psql_db.atomic()
def get_reminder_settings(guild_id: int, /, monitoring_bot_id: int) -> ReminderSettings:
    settings, _ = ReminderSettings.get_or_create(
        guild_id=guild_id,
        monitoring_bot_id=monitoring_bot_id,
    )
    return settings


@create_related(Guilds)
@psql_db.atomic()
def get_active_reminder(guild_id: int, /, monitoring_bot_id: int) -> Optional[Reminders]:
    return Reminders.get_or_none(guild_id=guild_id, monitoring_bot_id=monitoring_bot_id)

@psql_db.atomic()
def get_all_reminder_settings(monitoring_bot_id: int) -> tuple[ReminderSettings, ...]:
    return tuple(ReminderSettings.select().where(
        ReminderSettings.monitoring_bot_id == monitoring_bot_id
    ))


def create_or_overrite_old_reminder(
    guild_id: int,
    monitoring_bot_id: int,
    send_time: datetime,
    force: bool = False,
) -> None:
    current_reminder = get_active_reminder(guild_id, monitoring_bot_id=monitoring_bot_id)
    if force or not current_reminder or current_reminder.send_time < send_time:
        if current_reminder:
            current_reminder.delete_instance()
        Reminders.create(
            guild_id=guild_id,
            monitoring_bot_id=monitoring_bot_id,
            send_time=send_time
        )


def get_all_active_not_outdated_reminders() -> tuple[Reminders, ...]:
    return Reminders.select(Reminders).where(Reminders.send_time > datetime.now().astimezone())
