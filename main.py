import logging
import sys
import time
import traceback

import discord
from discord.ext import commands
from discord_components import DiscordComponents

from bot_components.configurator import configurator
from utils.custom_context import Context
from utils.custom_errors import NotСonfigured

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
        allowed_mentions = discord.AllowedMentions(roles=True,
                                                   everyone=True,
                                                   users=True)
        intents = discord.Intents.all() # It's OK. This bot is for one server
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
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.author.send(
                'This command cannot be used in private messages.')
        elif isinstance(error, commands.DisabledCommand):
            await ctx.author.send(
                'This command is disabled and cannot be used.')
        elif isinstance(error, commands.CommandInvokeError):
            original = error.original

            if not isinstance(original, discord.HTTPException):
                stackSummary = traceback.extract_tb(original.__traceback__, limit=20)
                traceback_list = traceback.format_list(stackSummary)
                
                logger.error(f'In command {ctx.command.qualified_name}:\n' + f"{''.join(traceback_list)}\n{original.__class__.__name__}: {original}")
        elif isinstance(error, commands.ArgumentParsingError):
            await ctx.send(error)

    async def process_commands(self, message):
        ctx = await self.get_context(message, cls=Context)

        if ctx.command is None:
            return

        await self.invoke(ctx)

    async def get_or_fetch_member(self, user_id) -> discord.User:
        user = self.get_user(user_id)
        if user:
            return user
        else:
            try:
                user = await self.fetch_user(user_id)
            except discord.HTTPException:
                return None
            else:
                return user

    def get_guild_member(self, member_id):
        guild = self.get_guild(self.config['guild'])
        if not guild:
            raise NotСonfigured('guild not specified. Check your config.')
        member = guild.get_member(member_id)
        return member

    def reload_config(self):
        self.configurator.reload()
        self.config = self.configurator.config
        self.system = self.configurator.system


bot = SEBot()
bot.run(bot.system['token'])
