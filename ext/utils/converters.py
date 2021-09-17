import re

from discord.ext import commands
from discord.ext.commands.errors import BadArgument

time_regex = re.compile("(?:(\d{1,5})(h|s|m|d))+?")
time_dict = {"h": 3600, "s": 1, "m": 60, "d": 86400}
reason_regex = re.compile(r"\b[^\d\s].+")


def convert_time(argument):
    args = argument.lower()
    matches = re.findall(time_regex, args)
    if not matches:
        raise commands.BadArgument("Time specified incorrectly.")
    time = 0
    for v, k in matches:
        try:
            time += time_dict[k] * float(v)
        except KeyError:
            raise commands.BadArgument(
                "{} is an invalid time-key! h/m/s/d are valid!".format(k))
        except ValueError:
            raise commands.BadArgument("{} is not a number!".format(v))
    return time


class Time_and_ReasonConverter(commands.Converter):
    async def convert(self, ctx, args):
        reason = re.findall(reason_regex, args)
        reason = ["not specified."] if len(reason) == 0 else reason
        args = re.sub(reason_regex, "", args)

        time = convert_time(args)
        return time, reason[0]


class Prefix(commands.Converter):
    async def convert(self, ctx, argument) -> str:
        user_id = ctx.bot.user.id
        if argument.startswith((f'<@{user_id}>', f'<@!{user_id}>')):
            raise commands.BadArgument(
                'Prefixes should not contain bot mentions.')
        return argument


class Reputation(commands.Converter):
    async def convert(self, ctx, argument) -> int:
        if argument in ['+', 'true', '1']:
            return 1
        elif argument in ['-', 'false', '0']:
            return -1
        elif argument in ['?', 'none', 'null']:
            return 0
        else:
            raise BadArgument('Please enter the correct type'\
                                +'\n`+` — increase reputation'\
                                +'\n`-` — reduce reputation'\
                                +"\n`?` — reset")
