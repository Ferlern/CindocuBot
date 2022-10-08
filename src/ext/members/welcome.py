from typing import Optional
import disnake
from disnake.ext import commands

from src.logger import get_logger
from src.translation import get_translator
from src.bot import SEBot
from src.ext.members.services import get_welcome_settings
from src.discord_views.embeds import DefaultEmbed


logger = get_logger()
t = get_translator()


class WelcomeCog(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(
        self,
        member: disnake.Member,
    ) -> None:
        await self.check_and_send_welcome(member)

    @commands.Cog.listener()
    async def on_raw_reaction_add(
        self,
        payload: disnake.RawReactionActionEvent,
    ) -> None:
        # hardcoded for Cindocu guild
        guild_id = 968223733858828298
        channel_id = 968239920521052241
        message_id = 972854517215399966
        emoji = '❤️'

        if payload.message_id != message_id:
            return

        if payload.emoji.name != emoji:
            return

        guild = self.bot.get_guild(guild_id)
        member = guild.get_member(payload.user_id)  # type: ignore
        channel = guild.get_channel(channel_id)  # type: ignore

        await self._send_welcome(
            channel=channel,  # type: ignore
            member=member,  # type: ignore
            text=("Добро пожаловать на сервер, %{member}!\n\n"
                  "Советуем тебе ознакомиться с каналами <#968240466615234600> и <#968275291124424714>. Если останутся вопросы, то напиши одному из наших Администраторов или участников :з\n\n"
                  "А пока, не будем тебя больше отвлекать и пожелаем удачи на Циндоку ^^"),
            title_text=":dizzy: **На наш сервер попала новая яркая звезда**"
        )

    async def check_and_send_welcome(self, member: disnake.Member) -> None:
        settings = get_welcome_settings(member.guild.id)
        channel = member.guild.get_channel(settings.channel_id)  # type: ignore
        if self._check_welcome(
            channel,
            settings.text,  # type: ignore
            settings.title_text  # type: ignore
        ):
            await self._send_welcome(
                channel,  # type: ignore
                member,
                settings.text,  # type: ignore
                settings.title_text  # type: ignore
            )

    async def _send_welcome(
        self,
        channel: disnake.TextChannel,
        member: disnake.Member,
        text: Optional[str],
        title_text: Optional[str],
    ) -> None:
        embed = DefaultEmbed(
            title=_prepare_string(title_text, member),
            description=_prepare_string(text, member),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(
            text=f'{member.guild.member_count} {t("member")} | {t("created")} {member.created_at:%m.%d.%Y, %H:%M:%S}',  # noqa
        )
        await channel.send(embed=embed, delete_after=60)

    def _check_welcome(
        self,
        channel: Optional[disnake.abc.GuildChannel],
        text: Optional[str],
        title_text: Optional[str],
    ) -> bool:
        if not channel or not isinstance(channel, disnake.TextChannel):
            return False

        if not (text or title_text):
            return False

        return True


def _prepare_string(strings: Optional[str], member: disnake.Member) -> str:
    if not strings:
        return ''
    return strings.replace(r'%{member}', member.mention)


def setup(bot):
    bot.add_cog(WelcomeCog(bot))
