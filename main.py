from functools import cache
import gettext
import logging
import sys
import time
import traceback
from importlib import reload
import disnake
from disnake.ext import commands
from discord_components import DiscordComponents

from bot_components import translate
from bot_components.configurator import configurator
from ext.utils.checks import is_admin, is_mod
from utils.custom_context import Context
from utils.custom_errors import (ConfirmationError, NotConfigured,
                                 OnlyAuthorError, WaitError)

logger = logging.getLogger('Arctic')


def _prefix_callable(bot, msg):
    user_id = bot.user.id
    base = [f'<@!{user_id}> ', f'<@{user_id}> ']
    base.extend(bot.config["prefixes"])
    return base


class SEBot(commands.AutoShardedBot):
    def __init__(self):
        self.configurator = configurator
        self.config = configurator.config
        self.system = configurator.system
        self.controller = translate.MessageController(self)
        self.expected_exception = (ConfirmationError, NotConfigured,
                                   OnlyAuthorError, WaitError)
        allowed_mentions = disnake.AllowedMentions(roles=True,
                                                   everyone=True,
                                                   users=True)
        intents = disnake.Intents.all()  # It's OK. This bot is for one server
        super().__init__(command_prefix=_prefix_callable,
                         description='temporary unknown',
                         allowed_mentions=allowed_mentions,
                         intents=intents,
                         case_insensitive=True,
                         strip_after_prefix=True)

        for extension in self.system['initial_extensions']:
            try:
                self.load_extension(extension)
                logger.info(f'extension {extension} installed successfully')
            except Exception as e:
                logger.exception('Failed to load extension')

    async def on_ready(self):
        DiscordComponents(self)
        if not hasattr(self, 'uptime'):
            self.uptime = time.time()
        else:
            return

        logger.info(f'Ready: {self.user} (ID: {self.user.id})')

    async def on_command_error(self, ctx, error):
        _ = ctx.get_translator()
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.author.send(
                _('This command cannot be used in private messages.'))
        elif isinstance(error, commands.DisabledCommand):
            await ctx.author.send(
                _('This command is disabled and cannot be used.'))
        elif isinstance(error, commands.CommandInvokeError):
            original = error.original

            if not isinstance(original, disnake.HTTPException):
                if original.__class__ in self.expected_exception:
                    logger.debug(
                        f'ignore expected exception {original.__class__.__name__}, in {ctx.command.qualified_name}'
                    )

                else:
                    stack_summary = traceback.extract_tb(
                        original.__traceback__, limit=20)
                    traceback_list = traceback.format_list(stack_summary)

                    logger.error(
                        f'In command {ctx.command.qualified_name}:\n' +
                        f"{''.join(traceback_list)}\n{original.__class__.__name__}: {original}"
                    )

        elif isinstance(error, commands.ArgumentParsingError):
            await ctx.send(error)

    async def on_error(self, event_method, *args, **kwargs):
        exception_info = sys.exc_info()
        if exception_info[0] in self.expected_exception:
            logger.debug(
                f'ignore expected exception {exception_info[0]}, in {event_method}'
            )
        else:
            stack_summary = traceback.extract_tb(exception_info[2], limit=20)
            traceback_list = traceback.format_list(stack_summary)

            logger.error(
                f'Ignoring exception in {event_method}\n' +
                f"{''.join(traceback_list)}\n{exception_info[0].__name__}: {exception_info[1]}"
            )

    async def process_commands(self, message):
        if message.author.bot:
            return

        ctx = await self.get_context(message, cls=Context)

        if ctx.command is None:
            await self.controller.check(ctx)
            return

        if ctx.channel.id not in self.config['commands_channels']:
            if not await is_mod().predicate(ctx):
                return

        await self.invoke(ctx)

    @cache
    def get_translator(self, lang: str = "en"):
        if lang == "en":

            def empty_translator(message: str):
                return message

            return empty_translator

        trans = gettext.translation("messages",
                                    localedir="locales",
                                    languages=(lang, ))
        return trans.gettext
    
    def get_translator_by_interaction(self, interaction):
        tranlstor = self.get_translator("ru")
        return tranlstor
    
    def get_translator_by_guild(self, guild: disnake.Guild):
        tranlstor = self.get_translator("ru")
        return tranlstor

    async def get_or_fetch_user(self, user_id) -> disnake.User:
        user = self.get_user(user_id)
        if user:
            return user
        else:
            try:
                user = await self.fetch_user(user_id)
            except disnake.HTTPException:
                return None
            else:
                return user

    def get_guild_member(self, member_id) -> disnake.Member:
        guild: disnake.Guild = self.get_guild(self.config['guild'])
        if not guild:
            raise NotConfigured('guild not specified. Check your config.')
        member = guild.get_member(member_id)
        return member

    def reload_config(self):
        self.configurator.reload()
        self.config = self.configurator.config
        self.system = self.configurator.system
        reload(translate)
        self.controller = translate.MessageController(self)


bot = SEBot()
bot.run(bot.system['token'])
bot.help_command.add_check(is_admin)
