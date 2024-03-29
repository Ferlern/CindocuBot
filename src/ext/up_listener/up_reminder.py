from __future__ import annotations
import asyncio
from typing import NamedTuple, Optional, TYPE_CHECKING
import datetime

import disnake
from disnake.ext import commands
from pytz import timezone
from pytz.tzinfo import BaseTzInfo

from src.translation import get_translator
from src.logger import get_logger
from src.utils import custom_events
from src.ext.up_listener.services import (get_reminder_settings,
                                          create_or_overrite_old_reminder,
                                          get_all_active_not_outdated_reminders)
if TYPE_CHECKING:
    from src.bot import SEBot


logger = get_logger()
t = get_translator(route='ext.up_listener')


class MonitoringData(NamedTuple):
    reset_days: tuple[int, ...]
    reset_time: int
    cooldown: int
    timezone: BaseTzInfo


MONITORING_INFORMATION = {
    464272403766444044: MonitoringData(
        reset_days=(1, 15),
        reset_time=12,
        cooldown=4,
        timezone=timezone('Europe/Moscow'),
    ),
    575776004233232386: MonitoringData(
        reset_days=(1, 15),
        reset_time=3,
        cooldown=4,
        timezone=timezone('Europe/Moscow'),
    )
}


class UpReminderCog(commands.Cog):
    def __init__(self, bot: SEBot) -> None:
        self.bot = bot

    @commands.Cog.listener(f'on_{custom_events.EventName.MONITORING_GUILD_PROMOTED}')
    async def up_listener(self, guild: disnake.Guild, monitoring_bot: disnake.User) -> None:
        info = MONITORING_INFORMATION.get(monitoring_bot.id)
        if not info:
            return

        settings = get_reminder_settings(guild.id, monitoring_bot.id)
        channel = guild.get_channel(settings.channel_id)  # type: ignore
        if not self.check_reminder(
            channel,
            text=settings.text  # type: ignore
        ):
            return

        logger.info('Creating remidner for guild %d, monitoring %d',
                    guild.id, monitoring_bot.id)
        current_time = datetime.datetime.now(info.timezone)
        if not is_close_to_reset(info):
            send_time = current_time + datetime.timedelta(hours=info.cooldown, seconds=-30)
        else:
            send_time = info.timezone.localize(datetime.datetime(
                current_time.year,
                current_time.month,
                current_time.day,
                info.reset_time,
            ))

        create_or_overrite_old_reminder(guild.id, monitoring_bot.id, send_time)
        await self.send_reminder(
            channel,  # type: ignore
            settings.text,  # type: ignore
            send_time
        )

    async def load_reminders(self) -> None:
        await self.bot.wait_until_ready()
        reminders = get_all_active_not_outdated_reminders()
        logger.info('%d pending reminders found', len(reminders))

        for reminder in reminders:  # noqa
            guild = self.bot.get_guild(reminder.guild_id.id)
            if not guild:
                continue
            settings = get_reminder_settings(guild.id, reminder.monitoring_bot_id)
            channel = guild.get_channel(settings.channel_id)  # type: ignore
            if self.check_reminder(channel, settings.text):  # type: ignore
                logger.info('Creating remidner for guild %d, monitoring %d',
                            guild.id, reminder.monitoring_bot_id)
                task = self.send_reminder(channel, settings.text, reminder.send_time)  # type: ignore
                self.bot.loop.create_task(task)

    def check_reminder(
        self,
        channel: Optional[disnake.abc.GuildChannel],
        text: Optional[str],
    ) -> bool:
        if not channel or not isinstance(channel, disnake.TextChannel):
            return False
        if not text:
            return False
        return True

    async def send_reminder(
        self,
        channel: disnake.TextChannel,
        text: str,
        send_time: datetime.datetime
    ) -> None:
        current_time = datetime.datetime.now().astimezone()
        wait_time = (send_time - current_time).total_seconds()
        logger.debug('send_reminder will sleep for %d second', wait_time)

        await asyncio.sleep(wait_time)
        logger.info('Sending remidner in channel %d', channel.id)
        await channel.send(
            text,
            allowed_mentions=disnake.AllowedMentions(
                everyone=False,
                users=True,
                roles=True,
            ),
        )


def is_close_to_reset(info: MonitoringData) -> bool:
    current_time = datetime.datetime.now(info.timezone)
    for day in info.reset_days:
        reset_time = current_time.replace(day=day, hour=info.reset_time, minute=0, second=0)
        delta = reset_time - current_time
        if datetime.timedelta() < delta < datetime.timedelta(hours=info.cooldown):
            return True
    return False


def setup(bot) -> None:
    cog = UpReminderCog(bot)
    cog.bot.loop.create_task(cog.load_reminders())
    bot.add_cog(cog)
