import logging

import discord
from core import Member_data_controller
from discord.ext import commands
from discord.ext.commands.errors import BadArgument
from main import SEBot
from utils.custom_errors import AlreadyLiked
from utils.utils import DefaultEmbed

from ..utils.converters import Reputation

loger = logging.getLogger('Arctic')


class reputation(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
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
    async def reputation(self, ctx, to_member: discord.Member,
                         type: Reputation):
        await ctx.message.delete()
        if to_member == ctx.author:
            raise BadArgument("You can't change your reputation")
        member = Member_data_controller(ctx.author.id)
        try:
            if type == 1:
                member.like(to_member)
                embed = discord.Embed(
                    title="Reputation increased",
                    description=
                    f"{ctx.author.mention} increased {to_member.mention}'s reputation ",
                    color=discord.Colour.green())
            elif type == -1:
                member.dislike(to_member)
                embed = discord.Embed(
                    title="Reputation decreased",
                    description=
                    f"{ctx.author.mention} decreased {to_member.mention}'s reputation ",
                    color=discord.Colour.red())
            elif type == 0:
                member.reset_like(to_member)
                embed = DefaultEmbed(
                    title="Reset", description='Reputation successfully reset')
            embed.set_thumbnail(url=ctx.author.avatar_url)
        except AlreadyLiked:
            embed = DefaultEmbed(description="You can't do it twice")

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(reputation(bot))
