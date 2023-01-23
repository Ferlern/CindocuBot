import disnake

from disnake.ext import commands

from src.translation import get_translator
from src.utils.time_ import parse_time_to_seconds


t = get_translator()


def not_bot_member(
    _: disnake.ApplicationCommandInteraction,
    arg: disnake.User,
) -> disnake.Member:
    if arg.bot:
        raise commands.BadArgument(t('target_bot'))
    if not isinstance(arg, disnake.Member):
        raise commands.BadArgument(t('cant_find_member'))
    return arg


def interacted_member(
    inter: disnake.ApplicationCommandInteraction,
    arg: disnake.User,
) -> disnake.Member:
    not_bot = not_bot_member(inter, arg)
    if not_bot == inter.author:
        raise commands.BadArgument(t('target_self'))
    return not_bot


def moderate_target(
    inter: disnake.ApplicationCommandInteraction,
    arg: disnake.User,
) -> disnake.User:
    author = inter.author
    if not isinstance(author, disnake.Member) or not inter.guild:
        raise commands.BadArgument(t('command_no_private'))
    if arg == author:
        raise commands.BadArgument(t('target_self'))
    if not isinstance(arg, disnake.Member):
        return arg
    if arg.top_role >= author.top_role and author != inter.guild.owner:
        raise commands.BadArgument(t('target_privileged'))
    return arg


def parse_time(
    _: disnake.ApplicationCommandInteraction,
    arg: str,
) -> float:
    return parse_time_to_seconds(arg)


def translate_converter_error(error: commands.BadArgument, arg: str, expected_type: type) -> str:
    translation_mapping = {
        int: 'int_converter',
        float: 'float_converter',
        commands.BadBoolArgument: 'bool_converter',
        commands.BadColourArgument: 'color_converter',
    }
    error_type_key = translation_mapping.get(type(error))  # type: ignore
    expected_type_key = translation_mapping.get(expected_type)  # type: ignore
    return t(error_type_key or expected_type_key or 'unknown_converter', arg=arg)
