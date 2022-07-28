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


class ReputationCog(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot
        self.emoji = self.bot.config["additional_emoji"]["reputation"]

    async def cog_command_error(self, ctx, error):
        _ = ctx.get_translator()
        if isinstance(error, commands.BadArgument):
            await ctx.message.delete()
            embed = DefaultEmbed(title=_("Reputation not changed"),
                                 description=_("**Error**: {error}").format(error=error))
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.message.delete()
            if error.param.name == 'to_member':
                embed = DefaultEmbed(
                    title=_("Reputation not changed"),
                    description=_("**Error**: user not specified"))
            elif error.param.name == 'type':
                reason = (_('Please enter the correct type')\
                                + _('\n`+` - increase reputation')\
                                + _('\n`-` - reduce reputation')\
                                + _("\n`?` - reset"))
                embed = DefaultEmbed(title=_("Reputation not changed"),
                                     description=_("**Error**: {reason}").format(reason=reason))
            await ctx.send(embed=embed)

    @commands.command(aliases=['rep'])
    async def reputation(self, ctx, to_member: InteractedMember,
                         type: Reputation):
        await ctx.message.delete()
        _ = ctx.get_translator()

        member = MemberDataController(ctx.author.id)
        try:
            if type == 1:
                member.like(to_member)
                embed = discord.Embed(
                    title=_("{emoji} Reputation increased").format(emoji=self.emoji['increased']),
                    description=_("{author} increased {to_member}'s reputation").format(
                        to_member=to_member.mention,
                        author=ctx.author.mention,
                    ),
                    color=discord.Colour.green())
            elif type == -1:
                member.dislike(to_member)
                embed = discord.Embed(
                    title=_("{emoji} Reputation decreased").format(emoji=self.emoji['decreased']),
                    description=_("{author} decreased {to_member}'s reputation").format(
                        to_member=to_member.mention,
                        author=ctx.author.mention,
                    ),
                    color=discord.Colour.red())
            elif type == 0:
                member.reset_like(to_member)
                embed = DefaultEmbed(
                    title=_("{emoji} Reset").format(emoji=self.emoji['reset']),
                    description=_('Reputation successfully reset')
                )
            embed.set_thumbnail(url=ctx.author.avatar_url)
        except AlreadyLiked:
            embed = DefaultEmbed(description=_("You can't do it twice"))

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(ReputationCog(bot))
