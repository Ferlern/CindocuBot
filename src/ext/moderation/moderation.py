import disnake
from disnake.ext import commands

from src.custom_errors import UsedNotOnGuild
from src.logger import get_logger
from src.translation import get_translator
from src.discord_views.embeds import DefaultEmbed
from src.ext.history.services import make_history
from src.bot import SEBot
from src.utils.slash_shortcuts import only_admin
from src.converters import moderate_target, parse_time
from src.utils.time_ import time_autocomplate
from src.ext.moderation.actoin_providers.mute_provider import MuteProvider, UnmuteProvider
from src.ext.moderation.actoin_providers.ban_provider import BanProvider, UnbanProvider
from src.ext.moderation.actoin_providers.warn_provider import WarnProvider, UnwarnProvider


t = get_translator(route="ext.moderation")
logger = get_logger


class ModerationCog(commands.Cog):
    def __init__(self, bot: SEBot) -> None:
        self.bot = bot

    @commands.slash_command(**only_admin)
    async def mute(
        self,
        inter: disnake.ApplicationCommandInteraction,
        target: disnake.User = commands.Param(converter=moderate_target),
        time: float = commands.Param(
            autocomplete=time_autocomplate,
            converter=parse_time,
        ),
        reason: str = commands.Param(lambda _: t('default_reason')),
    ) -> None:
        """
        Выдать мут участнику

        Parameters
        ----------
        target: Участник, которому будет выдан мут. Обязан быть на сервере
        time: Время, на которое будет выдан мут.
        reason: Причина выдачи мута.\
        Будет отображена в журнале аудита и истории
        """
        author = inter.author
        if not isinstance(author, disnake.Member):
            raise UsedNotOnGuild()

        action_provider = MuteProvider(
            author=author,
            target=target,
            reason=reason,
            time=int(time),
        )
        await action_provider.resolve_interaction(inter)
        await action_provider.full_action()

    @commands.slash_command(**only_admin)
    async def unmute(
        self,
        inter: disnake.ApplicationCommandInteraction,
        target: disnake.User = commands.Param(converter=moderate_target),
        reason: str = commands.Param(lambda _: t('default_reason')),
    ) -> None:
        """
        Снять мут с участника

        Parameters
        ----------
        target: Участник, с котогоро будет снят мут. Обязан быть на сервере
        reason: Причина снятия мута.\
        Будет отображена в журнале аудита и истории
        """
        author = inter.author
        if not isinstance(author, disnake.Member):
            raise UsedNotOnGuild()

        action_provider = UnmuteProvider(
            author=author,
            target=target,
            reason=reason,
        )
        await action_provider.resolve_interaction(inter)
        await action_provider.full_action()

    @commands.slash_command(**only_admin)
    async def warn(
        self,
        inter: disnake.ApplicationCommandInteraction,
        target: disnake.User = commands.Param(converter=moderate_target),
        reason: str = commands.Param(lambda _: t('default_reason')),
    ) -> None:
        """
        Выдать варн участнику

        Parameters
        ----------
        target: Участник, которому будет выдан варн. Обязан быть на сервере
        reason: Причина выдачи варна. Будет отображена в истории
        """
        author = inter.author
        if not isinstance(author, disnake.Member):
            raise UsedNotOnGuild()

        action_provider = WarnProvider(
            author=author,
            target=target,
            reason=reason,
        )
        await action_provider.resolve_interaction(inter)
        await action_provider.full_action()

    @commands.slash_command(**only_admin)
    async def unwarn(
        self,
        inter: disnake.ApplicationCommandInteraction,
        target: disnake.User = commands.Param(converter=moderate_target),
        reason: str = commands.Param(lambda _: t('default_reason')),
    ) -> None:
        """
        Снять варн с участника

        Parameters
        ----------
        target: Участник, с котогоро будет снят варн. Обязан быть на сервере
        reason: Причина снятия варна.\
        Будет отображена в истории
        """
        author = inter.author
        if not isinstance(author, disnake.Member):
            raise UsedNotOnGuild()

        action_provider = UnwarnProvider(
            author=author,
            target=target,
            reason=reason,
        )
        await action_provider.resolve_interaction(inter)
        await action_provider.full_action()

    @commands.slash_command(**only_admin)
    async def ban(
        self,
        inter: disnake.ApplicationCommandInteraction,
        target: disnake.Member = commands.Param(converter=moderate_target),
        reason: str = commands.Param(lambda _: t('default_reason')),
        delete_days: int = commands.Param(default=0, ge=0, le=7),
    ) -> None:
        """
        Выдать бан участнику

        Parameters
        ----------
        target: Участник, которому будет выдан бан.\
        Может быть айди пользователя не с сервера
        reason: Причина выдачи бана.\
        Будет отображена в журнале аудита и истории
        delete_days: Удалить сообщения учатника за последние x дней.
        """
        author = inter.author
        if not isinstance(author, disnake.Member):
            raise UsedNotOnGuild()

        action_provider = BanProvider(
            author=author,
            target=target,
            reason=reason,
            delete_days=delete_days,  # type: ignore
        )
        await action_provider.resolve_interaction(inter)
        await action_provider.full_action()

    @commands.slash_command(**only_admin)
    async def unban(
        self,
        inter: disnake.ApplicationCommandInteraction,
        target: disnake.User = commands.Param(converter=moderate_target),
        reason: str = commands.Param(lambda _: t('default_reason')),
    ) -> None:
        """
        Снять бан с участника

        Parameters
        ----------
        target: Участник, с которого будет снят бан.\
        Может быть айди пользователя не с сервера
        reason: Причина снятия бана.\
        Будет отображена в журнале аудита и истории
        """
        author = inter.author
        if not isinstance(author, disnake.Member):
            raise UsedNotOnGuild()

        action_provider = UnbanProvider(
            author=author,
            target=target,
            reason=reason,
        )
        await action_provider.resolve_interaction(inter)
        await action_provider.full_action()

    @commands.slash_command(**only_admin)
    async def clear(
        self,
        inter: disnake.ApplicationCommandInteraction,
        amount: commands.Range[1, ...] = commands.Param(),
    ) -> None:
        """
        Массово удалить сообщения из текущего канала

        Parameters
        ----------
        amount: Количество сообщений, которые будут проверены и удалены
        """
        guild = inter.guild
        if not guild:
            raise UsedNotOnGuild()

        deleted = await inter.channel.purge(limit=amount, bulk=True)

        messages = t(
            'messages',
            count=len(deleted),
        )
        description = t(
            'clear_desc',
            author_id=inter.author.id,
            channel_id=inter.channel.id,
            messages=messages,
        )
        make_history(
            guild.id,
            inter.author.id,
            name='clear',
            description=description,
        )
        embed = DefaultEmbed(
            title=t('clear'),
            description=description,
        )
        await inter.response.send_message(embed=embed, delete_after=30)


def setup(bot) -> None:
    bot.add_cog(ModerationCog(bot))
