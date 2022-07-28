import logging
import re
import discord

from discord.ext import commands
from discord.ext.commands.errors import BadArgument


logger = logging.getLogger('Arctic')
time_regex = re.compile("(?:(\d{1,5})(h|s|m|d))+?")
time_dict = {"h": 3600, "s": 1, "m": 60, "d": 86400}
reason_regex = re.compile(r"\b[^\d\s].+")


def convert_time(argument, translator):
    _ = translator
    args = argument.lower()
    matches = re.findall(time_regex, args)
    if not matches:
        raise commands.BadArgument(_("Time specified incorrectly."))
    time = 0
    for v, k in matches:
        try:
            time += time_dict[k] * float(v)
        except KeyError:
            raise commands.BadArgument(
                _("{} is an invalid time-key! h/m/s/d are valid!").format(k))
        except ValueError:
            raise commands.BadArgument(_("{} is not a number!").format(v))
    return time


class TimeAndReasonConverter(commands.Converter):
    async def convert(self, ctx, args):
        translator = ctx.get_translator()
        _ = translator
        reason = re.findall(reason_regex, args)
        reason = [_("not specified.")] if len(reason) == 0 else reason
        args = re.sub(reason_regex, "", args)

        time = convert_time(args, translator)
        return time, reason[0]


class Prefix(commands.Converter):
    async def convert(self, ctx, argument) -> str:
        user_id = ctx.bot.user.id
        if argument.startswith((f'<@{user_id}>', f'<@!{user_id}>')):
            _ = ctx.get_translator()
            raise commands.BadArgument(
                _('Prefixes should not contain bot mentions.'))
        return argument


class Reputation(commands.Converter):
    async def convert(self, ctx, argument) -> int:
        _ = ctx.get_translator()
        if argument in ['+', 'true', '1']:
            return 1
        elif argument in ['-', 'false', '0']:
            return -1
        elif argument in ['?', 'none', 'null']:
            return 0
        else:
            raise BadArgument(_('Please enter the correct type')\
                                + _('\n`+` - increase reputation')\
                                + _('\n`-` - reduce reputation')\
                                + _("\n`?` - reset"))


class NotBotMember(commands.MemberConverter):
    async def convert(self, ctx, argument) -> discord.Member:
        member = await super().convert(ctx, argument)
            
        if member.bot:
            _ = ctx.get_translator()
            raise commands.BadArgument(_('Specified user is a bot'))
        return member


class InteractedMember(commands.MemberConverter):
    async def convert(self, ctx, argument) -> discord.Member:
        member = await super().convert(ctx, argument)
        _ = ctx.get_translator()
            
        if member.bot:
            raise commands.BadArgument(_('Specified user is a bot'))
        if member == ctx.author:
            raise commands.BadArgument(_('Specified user is yourself'))
        return member

class PunishedMember(InteractedMember):
    
    async def convert(self, ctx, argument) -> discord.Member:
        member = await super().convert(ctx, argument)
        _ = ctx.get_translator()
        mod_roles_ids = set(ctx.bot.config["moderators_roles"])
        member_roles_ids = set([role.id for role in member.roles])
        if mod_roles_ids & member_roles_ids:
            raise BadArgument(_('Specified user is moderator'))
        
        permissions = member.guild_permissions
        if permissions.administrator:
            raise BadArgument(_('Specified user is administrator'))
        if member.id == ctx.bot.owner_id:
            raise BadArgument(_('Specified user is bot owner'))
        
        return member
    
    
class NaturalNumber(commands.Converter):
    
    async def convert(self, ctx, argument):
        try:
            argument = int(argument)
            assert argument >= 0
        except Exception:
            _ = ctx.get_translator()
            raise BadArgument(_("{argument} is not a natural number").format(argument=argument))
        
        return argument
