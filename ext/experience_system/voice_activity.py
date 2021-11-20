import logging
import time

import discord
from core import MemberDataController
from discord.ext import commands
from main import SEBot

logger = logging.getLogger('Arctic')


class voice_activity(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot
        self.count_for = {}
        self.allowed_channels = []

    def external_sync(self, user):
        if voiceState := user.voice:
            self.check_channel(voiceState.channel, user)
        self.sync_user(user)

    def sync_user(self, user):
        self.remove_from_count(user)
        self.add_to_count(user)

    def remove_from_count(self, user):
        if user.id in self.count_for.keys():
            logger.debug(f'<voice_activity> - stop voice activity for {user}')
            member = MemberDataController(id=user.id)
            member.user_info.voice_activity += time.time(
            ) - self.count_for.pop(user.id)
            member.save()

    def add_to_count(self, user):
        voice_state: discord.VoiceState = user.voice
        if not voice_state:
            return
        if (not (voice_state.deaf or voice_state.self_deaf)
            ) and user.id not in self.count_for.keys(
            ) and voice_state.channel in self.allowed_channels:
            logger.debug(
                f'<voice_activity> - start count voice activity for {user}')
            self.count_for[user.id] = time.time()

    def check_channel(self, channel: discord.VoiceChannel, user):
        members = channel.members
        members = list(
            filter(
                lambda member: not member.bot and not (member.voice.deaf or
                                                       member.voice.self_deaf),
                members)
        )

        if len(members) > 1:
            if channel not in self.allowed_channels:
                logger.debug(
                    f'<voice_activity> - add {channel} to allowed_channels')
                self.allowed_channels.append(channel)
                for member in members:
                    self.add_to_count(member)
        else:
            if channel in self.allowed_channels:
                logger.debug(
                    f'<voice_activity> - remove {channel} from allowed_channels'
                )
                self.allowed_channels.remove(channel)
                self.remove_from_count(user)
                for member in members:
                    self.remove_from_count(member)

    @commands.Cog.listener()
    async def on_voice_state_update(self, user: discord.Member,
                                    before: discord.VoiceState,
                                    after: discord.VoiceState):
        if user.bot:
            return
        if before.channel != after.channel:
            if before.channel: self.check_channel(before.channel, user)
            if after.channel: self.check_channel(after.channel, user)
        else:
            self.sync_user(user)


def setup(bot):
    bot.add_cog(voice_activity(bot))
