from __future__ import annotations

import asyncio
import datetime
from typing import TYPE_CHECKING, NamedTuple, Optional

import disnake
from disnake.ext import commands, tasks
from pytz import timezone
from pytz.tzinfo import BaseTzInfo

from src.ext.up_listener.services import (
    create_or_overrite_old_reminder,
    get_all_active_not_outdated_reminders,
    get_all_reminder_settings,
    get_reminder_settings,
)
from src.logger import get_logger
from src.translation import get_translator
from src.utils import custom_events

if TYPE_CHECKING:
    from src.bot import SEBot

logger = get_logger()
t = get_translator(route='ext.up_listener')
class MonitoringData(NamedTuple):
    reset_days: tuple[int, ...]
    reset_time: int
    cooldown: datetime.timedelta
    timezone: BaseTzInfo

MONITORING_INFORMATION = {
    1244278183814238259: MonitoringData(
        reset_days=(1, 15),
        reset_time=12,
        cooldown=datetime.timedelta(hours=4),
        timezone=timezone('Europe/Moscow'),
    ),
    1135447052734709761: MonitoringData(
        reset_days=(1, 15),
        reset_time=0,
        cooldown=datetime.timedelta(hours=4),
        timezone=timezone('GMT'),
    )
}

REMINDER_LEAD = datetime.timedelta(seconds=35)

class UpReminderCog(commands.Cog):
    def __init__(self, bot: SEBot) -> None:
        self.bot = bot
        self._active: set[tuple[int, int, datetime.datetime]] = set()
        self.reset_scheduler.start()

    def cog_unload(self) -> None:
        self.reset_scheduler.cancel()

    @commands.Cog.listener(f'on_{custom_events.EventName.MONITORING_GUILD_PROMOTED.value}')
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

        logger.info('Creating remidner for guild %d, monitoring %d', guild.id, monitoring_bot.id)
        current_time = datetime.datetime.now(info.timezone)
        close_to_reset = is_close_to_reset(info)

        if close_to_reset:
            send_time = next_reset(info) - REMINDER_LEAD
        else:
            send_time = current_time + info.cooldown - REMINDER_LEAD

        create_or_overrite_old_reminder(
            guild.id, monitoring_bot.id, send_time, force=close_to_reset,
        )

        self._launch_reminder(
            guild.id, monitoring_bot.id,
            channel,  # type: ignore
            settings.text,  # type: ignore
            send_time,
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
                logger.info('Restoring reminder for guild %d, monitoring %d',
                            guild.id, reminder.monitoring_bot_id)
                self._launch_reminder(
                    guild.id, reminder.monitoring_bot_id,
                    channel, settings.text, reminder.send_time,  # type: ignore
                )

    def check_reminder(self, channel: Optional[disnake.abc.GuildChannel], text: Optional[str]) -> bool:
        return bool(channel and isinstance(channel, disnake.TextChannel) and text)

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

    def _launch_reminder(
        self,
        guild_id: int,
        monitoring_bot_id: int,
        channel: disnake.TextChannel,
        text: str,
        send_time: datetime.datetime,
    ) -> None:
        key = (guild_id, monitoring_bot_id, send_time)
        
        if key in self._active:
            logger.debug('Reminder %s already scheduled, skip', key)
            return
        
        self._active.add(key)
        self.bot.loop.create_task(self._run_reminder(key, channel, text, send_time))

    async def _run_reminder(
        self,
        key: tuple[int, int, datetime.datetime],
        channel: disnake.TextChannel,
        text: str,
        send_time: datetime.datetime,
    ) -> None:
        try:
            await self.send_reminder(channel, text, send_time)
        finally:
            self._active.discard(key)

    @tasks.loop(seconds=60)
    async def reset_scheduler(self) -> None:
        for monitoring_bot_id, info in MONITORING_INFORMATION.items():
            if not is_close_to_reset(info):
                continue
            
            send_time = next_reset(info) - REMINDER_LEAD

            if send_time <= datetime.datetime.now(info.timezone):
                continue
            
            for settings in get_all_reminder_settings(monitoring_bot_id):
                guild = self.bot.get_guild(settings.guild_id.id)  # type: ignore
                
                if not guild:
                    continue
                
                channel = guild.get_channel(settings.channel_id)  # type: ignore
                
                if not self.check_reminder(channel, settings.text):  # type: ignore
                    continue
                
                if (guild.id, monitoring_bot_id, send_time) in self._active:
                    continue
                
                logger.info('Reset scheduler arms reminder for guild %d, monitoring %d at %s', guild.id, monitoring_bot_id, send_time.isoformat())
                
                create_or_overrite_old_reminder(
                    guild.id, monitoring_bot_id, send_time, force=True,
                )

                self._launch_reminder(
                    guild.id, monitoring_bot_id,
                    channel, settings.text, send_time,  # type: ignore
                )

    @reset_scheduler.before_loop
    async def before_reset_scheduler(self) -> None:
        await self.bot.wait_until_ready()


def next_reset(info: MonitoringData) -> datetime.datetime:
    now = datetime.datetime.now(info.timezone)
    candidates = []

    for month_offset in (0, 1):
        month_index = now.month - 1 + month_offset
        year = now.year + month_index // 12
        month = month_index % 12 + 1

        for day in info.reset_days:
            moment = info.timezone.localize(datetime.datetime(
                year, month, day, info.reset_time
            ))
            
            if moment > now:
                candidates.append(moment)

    return min(candidates)


def is_close_to_reset(info: MonitoringData) -> bool:
    now = datetime.datetime.now(info.timezone)
    return next_reset(info) - now < info.cooldown

def setup(bot) -> None:
    cog = UpReminderCog(bot)
    cog.bot.loop.create_task(cog.load_reminders())
    bot.add_cog(cog)
