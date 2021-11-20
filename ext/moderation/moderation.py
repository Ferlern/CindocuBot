import time
import typing
from importlib import reload

import core
import discord
from core import Logs
from discord.ext import commands
from discord.ext.commands.errors import BadArgument
from discord_components import Button
from main import SEBot
from utils.custom_errors import NotConfigured
from utils.utils import DefaultEmbed, display_time

from ..utils.checks import is_mod
from ..utils.converters import TimeAndReasonConverter, PunishedMember
from ..utils.utils import to_string, to_string_with_ids
from .components import mute_controller
from .components.mail import mail


class moderationCog(commands.Cog):
    def __init__(self, bot: SEBot):
        reload(mute_controller)
        self.bot = bot
        self.mute_controller = mute_controller.Mute_controller(bot)
        self.mute_controller.start()

    def cog_unload(self):
        self.mute_controller.cancel()

    async def cog_check(self, ctx):
        if not ctx.guild:
            return False
        return await is_mod().predicate(ctx)

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.message.delete()
            embed = discord.Embed(title="Failed to complete action",
                                  description=f"**Error**: {error}",
                                  color=0x93a5cd)
            await ctx.send(embed=embed)     

    async def ban_members(self, ctx, members, delete_days, reason):
        banned = []
        for member in members:
            try:
                await member.ban(delete_message_days=delete_days,
                                 reason=reason)
                banned.append(member)
            except Exception as e:
                pass
        return banned

    @commands.command()
    async def mute(self,
                   ctx,
                   members: commands.Greedy[PunishedMember],
                   *,
                   reason_and_time: TimeAndReasonConverter = ""):
        if len(members) == 0:
            raise commands.BadArgument("user not specified")
        if len(reason_and_time) == 0:
            raise commands.BadArgument("time and reason not specified")
        await ctx.message.delete()

        time = int(reason_and_time[0])
        reason = reason_and_time[1]
        muted = await self.mute_controller.mute_members(
            ctx, members, time, reason)

        for member in muted:
            await mail(ctx, member, "muted", reason, time=time)

        muted_string = to_string(muted)

        if not reason:
            reason = "not specified."

        Logs.create_mod_log(ctx.message.author, "mute", reason, time, muted)

        embed = discord.Embed(
            title="User Muted!",
            description="{0} was muted by {1} for {2}.\n\n**Reason**: {3}".
            format(muted_string, ctx.message.author.mention,
                   display_time(time, granularity=4, full=True), reason),
            color=0x93a5cd)
        await ctx.send(embed=embed, delete_after=30)

    @commands.command()
    async def unmute(self,
                     ctx,
                     members: commands.Greedy[PunishedMember],
                     *,
                     reason: typing.Optional[str] = "not specified."):
        if len(members) == 0:
            raise commands.BadArgument("user not specified")
        await ctx.message.delete()

        for member in members:
            member_info = core.MemberDataController(member.id)
            member_info.end_mute()
            member_info.save()

            await self.mute_controller.clean_mute(member)

        unmuted = to_string(members)
        Logs.create_mod_log(ctx.message.author,
                            "unmute",
                            reason=reason,
                            targets=members)
        embed = discord.Embed(
            title="Unmute",
            description="{0} unmuted by {1}\n\n**Reason**: {2}".format(
                unmuted, ctx.message.author.mention, reason),
            color=0x93a5cd)
        await ctx.send(embed=embed, delete_after=30)

    @commands.command()
    async def warn(self,
                   ctx,
                   members: commands.Greedy[PunishedMember],
                   *,
                   reason: typing.Optional[str] = "not specified."):
        if len(members) == 0:
            raise commands.BadArgument("user not specified")
        await ctx.message.delete()

        for member in members:
            member_info = core.MemberDataController(member.id)
            member_info.warn()
            member_info.save()

            warn_amount: int = member_info.user_info.warn
            warn_system = self.bot.config["warns_system"]

            try:
                actions = warn_system[warn_amount - 1]
            except IndexError:
                try:
                    actions = warn_system[-1]
                except IndexError:
                    raise NotConfigured(
                        "Set at least one warning in config")
            except TypeError:
                raise NotConfigured("Warn system created incorrectly")

            if actions.get('ban'):
                additional_description = actions[
                    "text"] + "\nAlong with this warning, you are banned from the server"
                await mail(ctx,
                           member,
                           "warned",
                           reason,
                           additional_description=additional_description)
                await self.ban_members(ctx, (member, ), 0, reason)
            else:
                additional_description = actions[
                    "text"] + f"\nAlong with this warning, you are muted for {display_time(actions['mute_time'], granularity=4, full=True)}."
                await mail(ctx,
                           member,
                           "warned",
                           reason,
                           additional_description=additional_description)
                await self.mute_controller.mute_members(
                    ctx, (member, ), actions["mute_time"], reason)

            warned = to_string(members)
            Logs.create_mod_log(ctx.message.author,
                                "warn",
                                reason=reason,
                                targets=members)
            embed = discord.Embed(
                title="User Warned!",
                description="{0} was warned by {1}\n\n**Reason**: {2}".format(
                    warned, ctx.message.author.mention, reason),
                color=0x93a5cd)
            await ctx.send(embed=embed, delete_after=30)

    @commands.command()
    async def unwarn(self,
                     ctx,
                     members: commands.Greedy[PunishedMember],
                     *,
                     reason: typing.Optional[str] = "not specified."):
        if len(members) == 0:
            raise commands.BadArgument("user not specified")
        await ctx.message.delete()

        for member in members:
            member_info = core.MemberDataController(member.id)
            member_info.unwarn()
            member_info.save()

        unwarned = to_string(members)
        Logs.create_mod_log(ctx.message.author,
                            "unwarn",
                            reason=reason,
                            targets=members)
        embed = discord.Embed(
            title="Unwarn",
            description="{0} unwarned by {1}\n\n**Reason**: {2}".format(
                unwarned, ctx.message.author.mention, reason),
            color=0x93a5cd)
        await ctx.send(embed=embed, delete_after=30)

    @commands.command()
    async def ban(self,
                  ctx,
                  members: commands.Greedy[PunishedMember],
                  delete_days: typing.Optional[int] = 0,
                  *,
                  reason: typing.Optional[str]):
        if len(members) == 0:
            raise commands.BadArgument("user not specified")
        await ctx.message.delete()

        banned = await self.ban_members(ctx, members, delete_days, reason)
        for member in banned:
            await mail(ctx, member, "banned", reason)
        banned_string = to_string(banned)
        if not reason:
            reason = "not specified."

        Logs.create_mod_log(ctx.message.author,
                            "ban",
                            reason=reason,
                            targets=banned)
        embed = discord.Embed(
            title="User Banned!",
            description="{0} was banned by {1}.\n\n**Reason**: {2}".format(
                banned_string, ctx.message.author.mention, reason),
            color=0x93a5cd)
        await ctx.send(embed=embed, delete_after=30)

    @commands.command()
    async def banid(self, ctx, ids: commands.Greedy[int],
                    reason: typing.Optional[str]):
        if len(ids) == 0:
            raise commands.BadArgument("user not specified")

        to_ban = []
        for id in ids:
            user = await self.bot.get_or_fetch_user(id)
            if user:
                to_ban.append(user)

        if not to_ban:
            raise BadArgument(
                "can't find users. Maybe you are giving wrong IDs?")
            
        await ctx.message.delete()
        to_ban_string = to_string_with_ids(to_ban)
        embed = DefaultEmbed(title="Ban by ID",
                             description=f"Ready to ban:\n{to_ban_string}")
        
        message = await ctx.confirm(embed=embed)

        banned = []
        for user in to_ban:
            try:
                await ctx.guild.ban(user, reason=reason)
                banned.append(user)
            except Exception as e:
                pass
        
        if not banned:
            embed = DefaultEmbed(description="can't ban users. Maybe you can't ban them")
            await ctx.send(embed=embed)
            return

        if not reason:
            reason = "not specified."

        Logs.create_mod_log(ctx.message.author,
                            "banid",
                            reason=reason,
                            targets=banned)
        banned = to_string_with_ids(banned)

        embed = discord.Embed(
            title="Ban by ID",
            description="{0} \nbanned by {1}\n\n**Reason**: {2}".format(
                banned, ctx.message.author.mention, reason),
            color=0x93a5cd)
        await message.edit(embed=embed)

    @commands.command()
    async def unban(self, ctx, ids: commands.Greedy[int],
                    reason: typing.Optional[str]):
        if len(ids) == 0:
            raise commands.BadArgument("user not specified")

        unbaned = []
        for id in ids:
            user = await self.bot.get_or_fetch_user(id)
            if not user:
                continue
            try:
                await ctx.guild.unban(user, reason=reason)
                unbaned.append(user)
            except Exception as e:
                pass

        if not unbaned:
            raise BadArgument(
                "can't find users. Maybe you are giving wrong IDs?")
            
        await ctx.message.delete()

        if not reason:
            reason = "not specified."
        Logs.create_mod_log(ctx.message.author,
                            "unban",
                            reason=reason,
                            targets=unbaned)
        unbaned = to_string_with_ids(unbaned)

        embed = discord.Embed(
            title="Unban",
            description="{0} \nunbaned by {1}\n\n**Reason**: {2}".format(
                unbaned, ctx.message.author.mention, reason),
            color=0x93a5cd)
        await ctx.send(embed=embed)

    @commands.command(ignore_extra=False)
    async def clear(self, ctx, members: commands.Greedy[discord.User],
                    amount: int):
        await ctx.message.delete()

        def check(message):
            if not members:
                return True
            else:
                return message.author in members

        deleted = await ctx.channel.purge(limit=amount, check=check, bulk=True)
        deleted_amount = len(deleted)

        Logs.create_mod_log(ctx.message.author, "clear", targets=members)

        embed = discord.Embed(
            title="Clear",
            description=
            f"{ctx.author.mention}, successfully deleted {deleted_amount} messages",
            color=0x93a5cd)
        await ctx.send(embed=embed, delete_after=30)

    @clear.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.TooManyArguments):
            embed = discord.Embed(
                title="Failed to complete action",
                description=
                f"**Error**: Make sure the IDs you specified are correct",
                color=0x93a5cd)
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(moderationCog(bot))
