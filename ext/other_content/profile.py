import logging
import typing

import discord
from core import MemberDataController
from discord.ext import commands
from discord.ext.commands.errors import BadArgument
from main import SEBot
from utils.utils import DefaultEmbed, display_time

loger = logging.getLogger('Arctic')


class ProfileCog(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot
        self.emoji = self.bot.config['additional_emoji']['profile']
        self.hearth_emoji = self.bot.config['additional_emoji']['other']['heart']

    async def cog_command_error(self, ctx, error):
        _ = ctx.get_translator()
        if isinstance(error, commands.BadArgument):
            await ctx.message.delete()
            embed = DefaultEmbed(title=_("Can't set biography"),
                                 description=f"**Error**: {error}")
            await ctx.send(embed=embed)

    def sync(self, member):
        cog = self.bot.get_cog('VoiceActivityCog')
        cog.external_sync(member)

    @commands.command()
    async def profile(self,
                      ctx,
                      member: typing.Optional[discord.Member] = None):
        translator = ctx.get_translator()
        _ = translator
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
        if not bio: bio = _('Biography not specified')

        embed = DefaultEmbed(
            title=_("Profile {member}").format(member=member.name),
            description=f"{bio}")
        
        embed.add_field(
            name=_("{emoji} Reputation").format(emoji=self.emoji['reputation']),
            value=f"```diff\n{likes}```",
            inline=False
        )
        
        embed.add_field(
            name=_("{emoji} Balance").format(emoji=self.emoji['balance']),
            value=f"**{balance}**"
        )
        
        embed.add_field(
            name=_("{emoji} Level").format(emoji=self.emoji['level']),
            value=f'**{level}** ({gained_after_lvl_up}/{left_before_lvl_up})')
        
        embed.add_field(name=_("{emoji} Voice time").format(emoji=self.emoji['voice']),
                        value=f'**{display_time(translator, int(voice_activity))}**')
        
        if soul_mate:
            embed.add_field(
                name=_("{emoji} Soul mate").format(emoji=self.emoji['soul_mate']),
                value=_('<@{soul_mate}> since <t:{married_time}:F> {emoji}').format(
                    soul_mate=soul_mate,
                    married_time=married_time,
                    emoji=self.hearth_emoji,
                ),
                inline=False)
            
        value = _('joined at <t:{time}:F>').format(time=int(member.joined_at.timestamp()))
        if warn:
            value += _('\nwarned **{warn}** times').format(warn=warn)
        embed.add_field(name=_("{emoji} Other").format(emoji=self.emoji['other']), value=value, inline=False)

        embed.set_thumbnail(url=member.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(aliases=['bio'])
    async def biography(self, ctx, *, biography: str):
        _ = ctx.get_translator()
        member = MemberDataController(id=ctx.author.id)
        new_lines = biography.count('\n')

        if new_lines > 5:
            raise BadArgument(_('Too many line breaks'))
        elif len(biography) > 200:
            raise BadArgument(_('Biography must be less than 200 characters'))
        else:
            await ctx.message.delete()
            member.user_info.biography = biography
            member.save()
            await ctx.send(embed=DefaultEmbed(
                description=_('Biography has been successfully updated')
            ))
            
    @biography.error
    async def handle(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.message.delete()
            _ = ctx.get_translator()

            embed = DefaultEmbed(title=_("Can't set biography"),
                                    description=_("**Error**: specify bio"))
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(ProfileCog(bot))
