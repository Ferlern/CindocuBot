from typing import Union
import time

import disnake
from disnake.ext import commands

from src.logger import get_voice_logger
from src.ext.activity.services import add_voice_time


logger = get_voice_logger()
MIN_MEMRBER_AMOUNT = 2


class VoiceActivityCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.count_for = {}
        self.allowed_channels = set()

    def external_sync(
        self,
        user: Union[disnake.Member, disnake.User],
    ) -> None:
        if not isinstance(user, disnake.Member):
            return

        voice_state = user.voice
        if not voice_state:
            return

        channel = voice_state.channel
        if not channel:
            return

        self._check_channel(channel)
        self._sync_member(user)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: disnake.Member,
        before: disnake.VoiceState,
        after: disnake.VoiceState
    ) -> None:
        if member.bot:
            return

        if before.channel != after.channel:
            if before.channel:
                self._check_channel(before.channel)
            if after.channel:
                self._check_channel(after.channel)

        self._sync_member(member)

    def _sync_member(self, member: disnake.Member) -> None:
        self._try_remove_from_count(member)
        self._try_add_to_count(member)

    def _try_remove_from_count(self, member: disnake.Member) -> None:
        if not self._is_count_for(member):
            return

        seconds = time.time() - self.count_for.pop(
            (member.guild.id, member.id)
        )
        logger.info('stop voice activity for %s on guild %s (%ds.)',
                    member, member.guild, seconds)
        add_voice_time(
            member.guild.id,
            member.id,
            int(seconds),
        )

    def _try_add_to_count(self, member: disnake.Member) -> None:
        voice_state = member.voice
        if not voice_state:
            return
        if not self._is_can_add_to_count(member):
            return

        self.count_for[(member.guild.id, member.id)] = time.time()
        logger.info('start count voice activity for %s on guild %s',
                    member, member.guild)

    def _check_channel(
        self,
        channel: Union[disnake.VoiceChannel,
                       disnake.StageChannel]
    ) -> None:
        members = channel.members
        members = list(filter(_is_conversation_participant, members))

        if len(members) >= MIN_MEMRBER_AMOUNT:
            if not self._is_channel_allowed(channel):
                self.allowed_channels.add(channel.id)
                logger.info('add %s to allowed_channels', channel)
                for member in members:
                    self._try_add_to_count(member)
        else:
            if self._is_channel_allowed(channel):
                self.allowed_channels.remove(channel.id)
                logger.info('remove %s from allowed_channels', channel)
                for member in members:
                    self._try_remove_from_count(member)

    def _is_can_add_to_count(self, member: disnake.Member) -> bool:
        voice_state = member.voice
        if not voice_state:
            return False

        channel = voice_state.channel
        if not channel:
            return False

        return (_is_conversation_participant(member) and
                not self._is_count_for(member) and
                self._is_channel_allowed(channel))

    def _is_count_for(self, member: disnake.Member) -> bool:
        return (member.guild.id, member.id) in self.count_for

    def _is_channel_allowed(
        self,
        channel: Union[disnake.VoiceChannel,
                       disnake.StageChannel]
    ) -> bool:
        return channel.id in self.allowed_channels


def _is_conversation_participant(member: disnake.Member) -> bool:
    return not member.bot and not _is_muted(member)


def _is_muted(member: disnake.Member) -> bool:
    voice_state = member.voice
    if not voice_state:
        return False
    return voice_state.deaf or voice_state.self_deaf


def setup(bot):
    bot.add_cog(VoiceActivityCog(bot))
