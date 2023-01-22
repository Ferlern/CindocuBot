import disnake
from disnake.ext import commands

from src.database.services import get_member
from src.ext.relationship.services import get_user_relationships_or_none
from src.converters import not_bot_member
from src.custom_errors import UsedNotOnGuild
from src.discord_views.embeds import DefaultEmbed
from src.utils.experience import format_exp
from src.utils.time_ import display_time
from src.translation import get_translator
from src.logger import get_logger
from src.ext.economy.services import get_economy_settings
from src.ext.members.services import get_member_reputation, change_bio
from src.bot import SEBot


logger = get_logger()
t = get_translator(route="ext.profile")


class ProfileCog(commands.Cog):
    def __init__(self, bot: SEBot) -> None:
        self.bot = bot

    @commands.slash_command()
    async def profile(  # pylint: disable=too-many-locals
        self,
        inter: disnake.GuildCommandInteraction,
        member=commands.Param(converter=not_bot_member, default=None)
    ) -> None:
        """
        Посмотреть профиль пользователя

        Parameters
        ----------
        member: Пользователь, профиль которого будет показан вместо вашего
        """
        await inter.response.defer()
        guild = inter.guild
        if not member:
            member = inter.author
        if not isinstance(member, disnake.Member):
            raise UsedNotOnGuild()
        self.bot.sync_user(member)

        guild_id = guild.id
        member_id = member.id

        member_data = get_member(guild_id, member_id)
        economy_settings = get_economy_settings(guild_id)
        relationships = get_user_relationships_or_none(guild_id, member_id)
        reputations = get_member_reputation(guild_id, member_id)

        bio = member_data.biography or t('no_bio')

        embed = DefaultEmbed(
            title=t("profile", username=member.name),
            description=bio,
        )
        embed.add_field(
            name=t("reputation"),
            value=f"```diff\n{reputations:+}```",
            inline=False,
        )
        embed.add_field(
            name=t("balance", coin=f'{economy_settings.coin}/{economy_settings.crystal}'),
            value=f"**{member_data.balance}** / **{member_data.donate_balance}**",
        )
        embed.add_field(
            name=t("level"),
            value=format_exp(member_data.experience),  # type: ignore
        )
        voice_time = display_time(
            member_data.voice_activity,  # type: ignore
        )
        embed.add_field(
            name=t("voice_time"),
            value=f'**{voice_time}**',
        )

        if relationships:
            soulmate = next(par for par in relationships.participants if par.user_id.id != member_id)  # noqa
            embed.add_field(
                name=t("soulmate"),
                value=t(
                    "soulmate_value",
                    soul_mate_id=soulmate.user_id,
                    timestamp=disnake.utils.format_dt(
                        relationships.creation_time,  # type: ignore
                        'f',
                    ),
                ),
                inline=False,
            )

        value = t('joined_at', timestamp=disnake.utils.format_dt(
            member.joined_at,  # type: ignore
            'F'
        ))
        if warns_amount := member_data.warns:
            value += t("warns", count=warns_amount)
        embed.add_field(name=t("other"), value=value, inline=False)
        embed.set_thumbnail(url=await self.bot.save_avatar(member))
        await inter.followup.send(embed=embed)

    @commands.slash_command()
    async def biography(
        self,
        inter: disnake.GuildCommandInteraction,
        biography: str,
    ) -> None:
        """
        Изменить отображающуюся в профиле биографию

        Parameters
        ----------
        biography: Ваша новая биография. Не длиннее 200 символов
        """
        guild = inter.guild

        if len(biography) > 200:
            raise commands.BadArgument(t('too_long_bio'))
        change_bio(
            guild_id=guild.id,
            user_id=inter.author.id,
            bio=biography,
        )
        await inter.response.send_message(
            embed=DefaultEmbed(description=t('bio_changed')),
            ephemeral=True,
        )


def setup(bot) -> None:
    bot.add_cog(ProfileCog(bot))
