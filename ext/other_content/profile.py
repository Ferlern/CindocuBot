import logging
import typing

import discord
from core import MemberDataController
from discord.ext import commands
from discord.ext.commands.errors import BadArgument
from main import SEBot
from utils.utils import DefaultEmbed, display_time

loger = logging.getLogger('Arctic')


class profile(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot
        self.emoji = self.bot.config['additional_emoji']['profile']
        self.hearth_emoji = self.bot.config['additional_emoji']['other']['heart']

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.message.delete()
            embed = DefaultEmbed(title="Сan't set biography",
                                 description=f"**Error**: {error}")
            await ctx.send(embed=embed)

    def sync(self, member):
        cog = self.bot.get_cog('voice_activity')
        cog.external_sync(member)

    @commands.command()
    async def profile(self,
                      ctx,
                      member: typing.Optional[discord.Member] = None):
        await ctx.message.delete()
        if not member:
            member = ctx.author
        self.sync(member)
        
        member_info = MemberDataController(id=member.id)
        coin = self.bot.config["coin"]
        soul_mate = member_info.soul_mate
        married_time = member_info.married_time
        balance = member_info.balance
        level, gained_after_lvl_up, left_before_lvl_up = member_info.level
        voice_activity = member_info.user_info.voice_activity
        warn = member_info.user_info.warn
        bio = member_info.user_info.biography
        likes = member_info.likes
        
        if likes > 0:
            likes = f'+{likes}'
        if not bio: bio = 'Biography not specified'

        embed = DefaultEmbed(
            title=f"Profile {member.name}",
            description=f"{bio}")
        
        embed.add_field(
            name=f"{self.emoji['reputation']} Reputation",
            value=f"```diff\n{likes}```",
            inline=False
        )
        
        embed.add_field(
            name=f"{self.emoji['balance']} Balance",
            value=f"**{balance}**"
        )
        
        embed.add_field(
            name=f"{self.emoji['level']} Level",
            value=f'**{level}** ({gained_after_lvl_up}/{left_before_lvl_up})')
        
        embed.add_field(name=f"{self.emoji['voice']} Voice time",
                        value=f'**{display_time(int(voice_activity))}**')
        
        if soul_mate:
            embed.add_field(
                name=f"{self.emoji['soul_mate']} Soul mate",
                value=f'<@{soul_mate}> since <t:{married_time}:F> {self.hearth_emoji}',
                inline=False)
            
        value = f'joined at <t:{int(member.joined_at.timestamp())}:F>'
        if warn:
            value += f'\nwarned **{warn}** times'
        embed.add_field(name=f"{self.emoji['other']} Other", value=value, inline=False)

        embed.set_thumbnail(url=member.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(aliases=['bio'])
    async def biography(self, ctx, *, biography: str):
        member = MemberDataController(id=ctx.author.id)
        new_lines = biography.count('\n')

        if new_lines > 5:
            raise BadArgument('Too many line breaks')
        elif len(biography) > 200:
            raise BadArgument('Biography must be less than 200 characters')
        else:
            await ctx.message.delete()
            member.user_info.biography = biography
            member.save()
            await ctx.send(embed=DefaultEmbed(
                description='Biography has been successfully updated'))
            
    @biography.error
    async def handle(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.message.delete()
            embed = DefaultEmbed(title="Сan't set biography",
                                    description=f"**Error**: specify bio")
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(profile(bot))
