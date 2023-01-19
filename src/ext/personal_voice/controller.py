import asyncio
from dataclasses import dataclass
from typing import Union

from peewee import DoesNotExist
import disnake
from disnake.ext import commands

from src.database.models import EconomySettings, PersonalVoice
from src.custom_errors import CriticalException
from src.logger import get_logger
from src.translation import get_translator
from src.ext.personal_voice.services import (get_voice_channel_by_id, get_voice_channel,
                                             update_voice_state)
from src.ext.economy.services import get_economy_settings
from src.bot import SEBot


t = get_translator(route="ext.personal_voice")
logger = get_logger()
RPIVATE_VOICE_DELETE_TIMER = 60


@dataclass
class VoiceState:
    name: str
    slots: int
    bitrate: int
    overwrites: dict[Union[disnake.Role, disnake.Member], disnake.PermissionOverwrite]

    @staticmethod
    def from_voice_data(bot: SEBot, voice_data: PersonalVoice, default_name: str) -> 'VoiceState':
        guild = bot.get_guild(voice_data.guild_id.id)
        if not guild:
            raise CriticalException(
                f"Can't create right state for channel {voice_data} without Bot on the guild "
            )

        overwrites = {}
        if current_overwrites := voice_data.current_overwrites:
            for id_, pair in current_overwrites.items():
                role = guild.get_role(int(id_))
                member = guild.get_member(int(id_))
                if role is None and member is None:
                    continue
                overwrites[role or member] = disnake.PermissionOverwrite.from_pair(
                    *[disnake.Permissions(value) for value in pair]
                )

        return VoiceState(
            voice_data.current_name or default_name,
            voice_data.current_slots,
            voice_data.current_bitrate * 1000,
            overwrites,
        )

    @staticmethod
    def from_voice_channel(voice_channel: disnake.VoiceChannel) -> 'VoiceState':
        return VoiceState(
            voice_channel.name,
            voice_channel.user_limit,
            voice_channel.bitrate,
            voice_channel.overwrites
        )

    def save_in_db(self, guild_id: int, user_id: int) -> None:
        overwrites = {key.id: [per.value for per in value.pair()] for key, value in self.overwrites.items()}  # noqa
        update_voice_state(user_id, guild_id, self.name, self.slots, self.bitrate, overwrites)


class PersonalVoiceControllerCog(commands.Cog):
    def __init__(self, bot: SEBot) -> None:
        self.bot = bot
        self._checked_categories: set[int] = set()
        self._chennel_delete_tasks: dict[int, asyncio.Task] = {}

    @commands.Cog.listener()
    async def on_guild_channel_update(
        self,
        before: disnake.VoiceChannel,
        after: disnake.VoiceChannel,
    ) -> None:
        if not isinstance(before, disnake.VoiceChannel):
            return

        try:
            voice = get_voice_channel_by_id(before.id)
        except DoesNotExist:
            return

        logger.debug("VoiceCustomizeCog listen to %s", after)
        before_state = VoiceState.from_voice_channel(before)
        after_state = VoiceState.from_voice_channel(after)
        if before_state == after_state:
            logger.debug("states equal, stop listen to %s", after)
            return

        checked_state = self._get_checked_personal_voice_state(after, voice)

        if checked_state != after_state:
            logger.debug("checked state different from after state (%s)", after)
            await after.edit(
                name=checked_state.name,
                user_limit=checked_state.slots,
                bitrate=checked_state.bitrate,
                overwrites=checked_state.overwrites,
                reason=t('forbidden_opportunities'),
            )
        else:
            logger.debug("checked state equals to after state (%s)", after)
            checked_state.save_in_db(after.guild.id, voice.user_id.id)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: disnake.Member,
        before: disnake.VoiceState,
        after: disnake.VoiceState
    ) -> None:
        guild = member.guild
        settings = get_economy_settings(member.guild.id)
        voice_category = guild.get_channel(settings.voice_category_id)  # type: ignore

        if not isinstance(voice_category, disnake.CategoryChannel):
            return

        await self.consider_main_voice_channel(voice_category, settings)

        if isinstance(after.channel, disnake.VoiceChannel):
            await self._handle_main_voice_join(member, voice_category, after.channel, settings)

        if voice_category.id not in self._checked_categories:
            self._checked_categories.add(voice_category.id)
            self._check_category(voice_category, settings)
        else:
            channel = before.channel
            if isinstance(channel, disnake.VoiceChannel):
                self._check_voice_for_delete(channel, settings)

            channel = after.channel
            if isinstance(channel, disnake.VoiceChannel):
                self._check_voice_for_delete(channel, settings)

    async def consider_main_voice_channel(
        self,
        category: disnake.CategoryChannel,
        settings: EconomySettings,
    ) -> None:
        if (
            settings.main_voice_id is None or
            settings.main_voice_id not in [channel.id for channel in category.channels]
        ):
            channel = await category.create_voice_channel(t('main_voice_default_name'))
            settings.main_voice_id = channel.id
            settings.save()

    async def _handle_main_voice_join(
        self,
        member: disnake.Member,
        voice_category: disnake.CategoryChannel,
        voice_channel: disnake.VoiceChannel,
        settings: EconomySettings,
    ) -> None:
        guild = member.guild
        if voice_channel.id != settings.main_voice_id:
            return

        try:
            voice_data = get_voice_channel(member.id, guild.id)
        except DoesNotExist:
            logger.info("member %s joined main channel but don't have personal channel", member)
            return

        current_voice = guild.get_channel(voice_data.voice_id)  # type: ignore
        if isinstance(current_voice, disnake.VoiceChannel):
            logger.info("member %s already have personal voice instance on guild %s. Removing",
                        member, guild)
            await current_voice.delete()

        logger.info("member %s joined main channel, creating his personal voice", member)
        voice_state = VoiceState.from_voice_data(self.bot, voice_data, member.display_name)
        channel = await voice_category.create_voice_channel(
            name=voice_state.name,
            user_limit=voice_state.slots,
            bitrate=voice_state.bitrate,
            overwrites=voice_state.overwrites,
        )
        voice_data.voice_id = channel.id
        voice_data.save()
        try:
            await member.move_to(channel)
        except disnake.HTTPException as error:
            logger.info("can't move %d to his voice channel: %s", member.id, error)

    def _check_voice_for_delete(
        self,
        voice_channel: disnake.VoiceChannel,
        settings: EconomySettings,
    ) -> None:
        if (
            voice_channel.category and voice_channel.category.id == settings.voice_category_id and
            voice_channel.id != settings.main_voice_id
        ):
            self._check_private_voice_for_delete(voice_channel)

    def _check_category(
        self,
        category_channel: disnake.CategoryChannel,
        settings: EconomySettings,
    ) -> None:
        for channel in category_channel.channels:
            if isinstance(channel, disnake.VoiceChannel):
                self._check_voice_for_delete(channel, settings)

    def _check_private_voice_for_delete(self, voice_channel: disnake.VoiceChannel) -> None:
        if not self._is_useless(voice_channel):
            if task := self._chennel_delete_tasks.get(voice_channel.id):
                logger.info("canceling channel_delete_task for %d voice_channel", voice_channel.id)
                del self._chennel_delete_tasks[voice_channel.id]
                res = task.cancel()
                if not res:
                    raise CriticalException('Task cancaled or done without removing from tasks map')
        else:
            async def channel_delete_task() -> None:
                logger.info("starts channel_delete_task for %d voice_channel on %d guild",
                            voice_channel.id, voice_channel.guild.id)
                await asyncio.sleep(RPIVATE_VOICE_DELETE_TIMER)

                del self._chennel_delete_tasks[voice_channel.id]

                guild = self.bot.get_guild(voice_channel.guild.id)
                if not guild:
                    return
                channel = guild.get_channel(voice_channel.id)
                if channel:
                    logger.info("delete %d voice_channel", voice_channel.id)
                    await channel.delete()

            task = asyncio.create_task(channel_delete_task())
            self._chennel_delete_tasks[voice_channel.id] = task

    def _is_useless(self, voice_channel: disnake.VoiceChannel) -> bool:
        if not voice_channel.members:
            return True
        return False

    def _get_checked_personal_voice_state(
        self,
        after: disnake.VoiceChannel,
        voice_data: PersonalVoice,
    ) -> VoiceState:
        state = VoiceState.from_voice_channel(after)

        if state.slots > voice_data.slots or state.slots == 0:
            state.slots = voice_data.slots

        if state.bitrate > voice_data.max_bitrate * 1000:
            state.bitrate = voice_data.max_bitrate * 1000

        overwrites = state.overwrites
        for _, overwrite in overwrites.items():
            if any([
                overwrite.move_members, overwrite.mute_members,
                overwrite.deafen_members
            ]):
                overwrite.move_members = None
                overwrite.mute_members = None
                overwrite.deafen_members = None

        if category := after.category:
            overwrites.update(category.overwrites)

        owner = after.guild.get_member(voice_data.user_id.id)
        if owner:
            overwrite = overwrites.get(owner)
            if overwrite:
                overwrite.view_channel = True
                overwrite.manage_channels = True
                overwrite.manage_permissions = True
            else:
                overwrites[owner] = disnake.PermissionOverwrite(
                    view_channel=True,
                    manage_channels=True,
                    manage_permissions=True,
                )

        return state


def setup(bot: SEBot) -> None:
    bot.add_cog(PersonalVoiceControllerCog(bot))
