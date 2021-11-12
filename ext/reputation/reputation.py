import logging

import discord
from core import MemberDataController
from discord.ext import commands
from discord.ext.commands.errors import BadArgument
from main import SEBot
from utils.custom_errors import AlreadyLiked
from utils.utils import DefaultEmbed

from ..utils.converters import Reputation, InteractedMember

loger = logging.getLogger('Arctic')


class reputation(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot
        self.emoji = self.bot.config["additional_emoji"]["reputation"]

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.message.delete()
            embed = DefaultEmbed(title="Reputation not changed",
                                 description=f"**Error**: {error}")
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.message.delete()
            if error.param.name == 'to_member':
                embed = DefaultEmbed(
                    title="Reputation not changed",
                    description=f"**Error**: user not specified")
            elif error.param.name == 'type':
                reason = ('Please enter the correct type'\
                                +'\n`+` — increase reputation'\
                                +'\n`-` — reduce reputation'\
                                +"\n`?` — reset")
                embed = DefaultEmbed(title="Reputation not changed",
                                     description=f"**Error**: {reason}")
            await ctx.send(embed=embed)

    @commands.command(aliases=['rep'])
    async def reputation(self, ctx, to_member: InteractedMember,
                         type: Reputation):
        await ctx.message.delete()
        member = MemberDataController(ctx.author.id)
        try:
            if type == 1:
                member.like(to_member)
                embed = discord.Embed(
                    title=f"{self.emoji['increased']} Reputation increased",
                    description=
                    f"{ctx.author.mention} increased {to_member.mention}'s reputation ",
                    color=discord.Colour.green())
            elif type == -1:
                member.dislike(to_member)
                embed = discord.Embed(
                    title=f"{self.emoji['decreased']} Reputation decreased",
                    description=
                    f"{ctx.author.mention} decreased {to_member.mention}'s reputation ",
                    color=discord.Colour.red())
            elif type == 0:
                member.reset_like(to_member)
                embed = DefaultEmbed(
                    title=f"{self.emoji['reset']} Reset", description='Reputation successfully reset')
            embed.set_thumbnail(url=ctx.author.avatar_url)
        except AlreadyLiked:
            embed = DefaultEmbed(description="You can't do it twice")

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(reputation(bot))
