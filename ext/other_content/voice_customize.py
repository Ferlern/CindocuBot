import logging

from core import PersonalVoice
from disnake import channel
from disnake.ext import commands
from main import SEBot

logger = logging.getLogger('Arctic')


class VoiceCustomizeCog(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        if not isinstance(before, channel.VoiceChannel):
            return
        _ = self.bot.get_translator_by_guild(before.guild)
        voices = PersonalVoice.select().dicts().execute()
        voices_id_list = [voice['voice_id'] for voice in voices]
        if before.id not in voices_id_list:
            return
        logger.debug(f"VoiceCustomizeCog listen to: {after.id}")
        voice_index = voices_id_list.index(before.id)
        voice = voices[voice_index]

        if after.user_limit > voice['slots'] or after.user_limit == 0:
            await after.edit(user_limit=voice['slots'],
                             reason=_('too many slots'))
        if after.bitrate > voice['max_bitrate'] * 1000:
            await after.edit(bitrate=voice['max_bitrate'] * 1000,
                             reason=_('bitrate higher than purchased'))
        overwrites = after.overwrites
        need_edit = False
        for type, overwrite in overwrites.items():
            if any([
                    overwrite.move_members, overwrite.mute_members,
                    overwrite.deafen_members
            ]):
                overwrite.move_members = None
                overwrite.mute_members = None
                overwrite.deafen_members = None
                need_edit = True
        if need_edit:
            await after.edit(overwrites=overwrites,
                             reason=_("forbidden opportunities"))


def setup(bot):
    bot.add_cog(VoiceCustomizeCog(bot))
