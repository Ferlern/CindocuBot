from peewee import DoesNotExist
import disnake
from disnake.ext import commands

from src.logger import get_logger
from src.translation import get_translator
from src.ext.personal_voice.services import (get_voice_channel_by_id)
from src.bot import SEBot


t = get_translator(route="ext.personal_voice")
logger = get_logger()


class VoiceCustomizeCog(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        if not isinstance(before, disnake.VoiceChannel):
            return

        try:
            voice = get_voice_channel_by_id(before.id)
        except DoesNotExist:
            return

        logger.debug("VoiceCustomizeCog listen to %s", after)

        if after.user_limit > voice.slots or after.user_limit == 0:
            await after.edit(
                user_limit=voice.slots,
                reason=t('voice_too_many_slots'),
            )
        if after.bitrate > voice.max_bitrate * 1000:
            await after.edit(
                bitrate=voice.max_bitrate * 1000,
                reason=t('voice_too_hight_bitrate'),
            )

        overwrites = after.overwrites
        need_edit = False
        for _, overwrite in overwrites.items():
            if any([
                    overwrite.move_members, overwrite.mute_members,
                    overwrite.deafen_members
            ]):
                overwrite.move_members = None
                overwrite.mute_members = None
                overwrite.deafen_members = None
                need_edit = True
        if need_edit:
            await after.edit(
                overwrites=overwrites,
                reason=t('forbidden_opportunities'),
            )


def setup(bot):
    bot.add_cog(VoiceCustomizeCog(bot))
