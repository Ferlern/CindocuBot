import sys
import time
import traceback
from typing import Optional, Union

import disnake
from disnake.ext import commands

from src import settings
from src.setup_development.entry import setup_development
from src.lock import AsyncioLockManager
from src.database.services import get_guild_prefixes
from src.logger import get_logger
from src.translation import get_translator
from src.utils.extract_traceback import extract_traceback
from src.discord_views.embeds import ActionFailedEmbed
from src.custom_errors import RegularException
from src.utils.cycle import Cycle


logger = get_logger()
t = get_translator()


class SEBot(commands.AutoShardedBot):
    def __init__(self) -> None:
        allowed_mentions = disnake.AllowedMentions(roles=True,
                                                   everyone=True,
                                                   users=True)
        intents = disnake.Intents.all()  # It's OK. This bot is for one server
        test_guilds = settings.TEST_GUILD_IDS if settings.DEVELOPMENT else None
        super().__init__(
            command_prefix=_prefix_callable,
            test_guilds=test_guilds,
            sync_commands_debug=settings.DEBUG,
            description='temporary unknown',
            allowed_mentions=allowed_mentions,
            intents=intents,
            case_insensitive=True,
            strip_after_prefix=True,
        )
        self.uptime = time.time()
        self.persistent_views_added = False
        self.image_channel_cycle = Cycle[int](settings.IMAGE_CHANNELS)
        self.lock = AsyncioLockManager()

        self._load_exts()

    async def save_avatar(
        self,
        user: Union[disnake.User, disnake.Member],
    ) -> str:
        url = await self.save_file(await user.display_avatar.to_file())
        return url or user.display_avatar.url

    async def possible_embed_image(self, url: str) -> bool:
        channel = self._next_image_channel()
        if not channel:
            return False

        embed = disnake.Embed()
        embed.set_image(url=url)
        try:
            await channel.send(embed=embed)
        except disnake.HTTPException:
            return False
        return True

    async def save_file(self, file: disnake.File) -> Optional[str]:
        channel = self._next_image_channel()
        if not channel:
            return None

        try:
            message = await channel.send(file=file)
        except (disnake.HTTPException, disnake.Forbidden):
            return None

        return message.attachments[0].url

    def sync_user(self, user: Union[disnake.User, disnake.Member]) -> None:
        cog = self.get_cog('VoiceActivityCog')
        cog.external_sync(user)  # type: ignore

    async def on_ready(self) -> None:
        if not self.persistent_views_added:
            # may be usefull in the future
            pass
        if not hasattr(self, 'uptime'):
            self.uptime = time.time()

        if settings.DEVELOPMENT and not hasattr(self, 'prepared'):
            await setup_development(
                self,
                settings.APP_NAME,
                settings.TESTERS_DISCORD_IDS,
                settings.TEST_GUILD_IDS,
                settings.CREATE_NEW_TEST_GUILD,
                settings.RECREATE_DATABASE_SCHEMA,
                settings.PREPARE_DATABASE,
                settings.PREPARE_GUILDS,
            )
            setattr(self, 'prepared', True)
        print(f'Ready: {self.user} (ID: {self.user.id})')

    async def process_commands(self, message) -> None:
        if message.author.bot:
            return

        ctx = await self.get_context(message)

        if ctx.command is None:
            return

        # TODO check is command in commands channel
        # temporary unnecessary, bot has no text commands

        await self.invoke(ctx)

    async def on_application_command(
        self,
        interaction: disnake.ApplicationCommandInteraction,
    ) -> None:
        accept_time = time.time()
        logger.info(
            'Command (%d) %s called by %d on guild %d',
            interaction.id,
            interaction.data,
            interaction.author.id,
            interaction.guild.id if interaction.guild else 0,
        )
        await super().on_application_command(interaction)
        logger.info(
            'Command %d DONE (%.3f seconds to respond)',
            interaction.id,
            time.time() - accept_time,
        )

    async def on_slash_command_error(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        exception: commands.errors.CommandError
    ) -> None:
        await self._application_command_error_handler(
            interaction, exception
        )

    async def on_user_command_error(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        exception: commands.errors.CommandError
    ) -> None:
        await self._application_command_error_handler(
            interaction, exception
        )

    async def on_command_error(self, context, exception) -> None:
        if isinstance(exception, commands.NoPrivateMessage):
            await context.author.send(t('command_no_private'))
        elif isinstance(exception, commands.DisabledCommand):
            await context.author.send(t('command_disabled'))
        elif isinstance(exception, commands.CommandInvokeError):
            original = exception.original

            if isinstance(original, disnake.HTTPException):
                return

            traceback_str = extract_traceback(original.__traceback__)
            command = context.command
            command_name = command.qualified_name if command else 'unknown'
            logger.error(
                'Ignoring exception in command %s:\n%s\n%s:%s',
                command_name, traceback_str,
                original.__class__.__name__, original
            )

        elif isinstance(exception, commands.ArgumentParsingError):
            await context.send(str(exception))

    async def on_error(self, event_method, *_, **__) -> None:
        exception_info = sys.exc_info()
        traceback_str = extract_traceback(exception_info[2])
        exception_name = exception_info[0]
        if exception_name:
            exception_name = exception_name.__name__
        logger.error(
            'Ignoring exception in %s\n%s\n%s:%s',
            event_method, traceback_str, exception_name, exception_info[1]
        )

    async def _application_command_error_handler(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        exception: commands.errors.CommandError
    ) -> None:
        # TODO check is exceptions are handled correctly
        # maybe we should supress all HTTPExceptions like in old version?
        if isinstance(exception, commands.CheckFailure):
            await interaction.response.send_message(
                t('command_no_permission'),
                ephemeral=True,
            )
        elif isinstance(exception, commands.CommandOnCooldown):
            timestamp = disnake.utils.format_dt(
                time.time() + exception.retry_after, 'R'
            )
            await interaction.response.send_message(
                t('command_cooldown', timestamp=timestamp),
                ephemeral=True,
            )
        elif isinstance(exception, commands.BadArgument):
            embed = ActionFailedEmbed(reason=str(exception))
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True,
            )
        elif all((
            isinstance(exception, commands.CommandInvokeError),
            isinstance(exception.original, RegularException),  # type: ignore
        )):
            embed = ActionFailedEmbed(
                reason=str(exception.original)  # type: ignore
            )
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True,
            )
        else:
            traceback_list = traceback.format_exception(
                type(exception), exception, exception.__traceback__
            )
            traceback_str = ''.join(traceback_list)
            command_name = interaction.application_command.name
            logger.error(
                'Ignoring exception in command %s\n%s',
                command_name, traceback_str
            )
            return await super().on_slash_command_error(interaction, exception)

    def _next_image_channel(self) -> Optional[disnake.TextChannel]:
        channel_id = next(self.image_channel_cycle)
        if not channel_id:
            return None

        channel = self.get_channel(channel_id)
        if not channel or not isinstance(channel, disnake.TextChannel):
            self.image_channel_cycle.remove(channel_id)
            return self._next_image_channel()

        return channel

    def _load_exts(self) -> None:
        for ext_path in settings.INITIAL_EXTENSIONS:
            self.load_extension(f'src.ext.{ext_path}')


def _prefix_callable(bot_: SEBot, message: disnake.Message) -> list[str]:
    bot_id = bot_.user.id
    base = [f'<@!{bot_id}>', f'<@{bot_id}>']

    guild = message.guild
    if guild:
        guild_prefixes = get_guild_prefixes(guild.id)
        if guild_prefixes:
            base.extend(guild_prefixes)
            return base

    base.extend(settings.DEFAULT_PREFIXES)
    return base


bot = SEBot()
bot.remove_command('help')
