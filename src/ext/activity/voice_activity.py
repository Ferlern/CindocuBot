from typing import Union
import time

import disnake
from disnake.ext import commands

from src.bot import SEBot
from src.logger import get_voice_logger
from src.translation import get_translator
from src.ext.activity.services import (
    add_voice_time,
    get_voice_rewards_settings,
    restart_present_counter
)
from src.ext.gifts.services import add_activity_present
from src.discord_views.embeds import DefaultEmbed


logger = get_voice_logger()
t = get_translator(route="ext.activity")
MIN_MEMRBER_AMOUNT = 2
REWARD_MESSAGE_DELETE_TIME = 60


class VoiceActivityCog(commands.Cog):
    def __init__(self, bot: SEBot) -> None:
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
        member_data = add_voice_time(
            member.guild.id,
            member.id,
            int(seconds),
        )
        self._check_for_present(member_data)

    def _try_add_to_count(self, member: disnake.Member) -> None:
        voice_state = member.voice
        if not voice_state:
            return
        if not self._is_can_add_to_count(member):
            return

        self.count_for[(member.guild.id, member.id)] = time.time()
        logger.info('start count voice activity for %s on guild %s',
                    member, member.guild)

    def _check_for_present(self, member_data) -> None:
        guild = member_data.guild_id.id
        user = member_data.user_id.id

        settings = get_voice_rewards_settings(guild)
        if member_data.until_present <= settings.seconds_for_present:
            return
        
        logger.info('rewarding member %s for voice activity on guild %s',
                member_data.user_id, member_data.guild_id)
        restart_present_counter(guild, user, settings.seconds_for_present) #type: ignore 
        add_activity_present(guild, user, 1)

        channel = self.bot.get_channel(settings.channel_id) # type: ignore
        if not isinstance(channel, disnake.TextChannel):
            return
        
        self.bot.loop.create_task(
            _send_reward_embed(channel, member_data.user_id)
        )

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


async def _send_reward_embed(channel: disnake.TextChannel, user_id: int) -> None:     
    embed = DefaultEmbed(
        description = t('present_got',
            user_id=user_id
        )
    )
    await channel.send(
        content=f"<@{user_id}>",
        embed=embed,
        delete_after=REWARD_MESSAGE_DELETE_TIME
    )


def setup(bot) -> None:
    bot.add_cog(VoiceActivityCog(bot))
