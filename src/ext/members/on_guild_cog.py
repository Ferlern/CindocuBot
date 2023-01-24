import disnake
from disnake.ext import commands

from src.database.services import get_member
from src.logger import get_logger
from src.bot import SEBot


logger = get_logger()


class OnGuildCog(commands.Cog):
    def __init__(self, bot: SEBot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member) -> None:
        guild_id = member.guild.id
        member_id = member.id
        logger.info('member %d join to guild %d', guild_id, member_id)
        member_data = get_member(guild_id, member_id)
        if member_data.on_guild is not True:
            member_data.on_guild = True
            member_data.save()

    @commands.Cog.listener()
    async def on_member_remove(self, member: disnake.Member) -> None:
        guild_id = member.guild.id
        member_id = member.id
        logger.info('member %d leave from guild %d', guild_id, member_id)
        member_data = get_member(guild_id, member_id)
        if member_data.on_guild is not False:
            member_data.on_guild = False
            member_data.save()


def setup(bot) -> None:
    bot.add_cog(OnGuildCog(bot))
