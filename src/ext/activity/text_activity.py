import asyncio
from random import randint

import disnake
from disnake.ext import commands

from src.bot import SEBot
from src.logger import get_logger
from src.translation import get_translator
from src.database.models import ExperienceSettings, Members
from src.database.services import get_member
from src.ext.activity.services import get_experience_settings
from src.ext.activity.lvl_reward.coin_rewarder import coin_rewarder
from src.ext.activity.lvl_reward.role_rewarder import role_rewarder
from src.utils.experience import exp_to_lvl
from src.discord_views.embeds import DefaultEmbed


LVL_UP_MESSAGE_DISPLAY_TIME = 30

logger = get_logger()
t = get_translator(route="ext.activity")
_rewarders = [coin_rewarder, role_rewarder]


class TextActivityCog(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot
        self.on_cooldown: set[tuple[int, int]] = set()

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        author = message.author
        if author.bot or not isinstance(author, disnake.Member):
            return

        settings = get_experience_settings(author.guild.id)
        checks = (_is_message_in_allowed_channel(message, settings),
                  not self._is_on_cooldown(author),
                  _is_message_long_enough(message, settings))

        if all(checks):
            await _give_prize_for_activity(author, settings, message)
            await self._set_cooldown(author, settings)

    async def _set_cooldown(self,
                            author: disnake.Member,
                            settings: ExperienceSettings):
        cooldown = settings.cooldown
        if cooldown is None:
            return

        guild_id = author.guild.id
        author_id = author.id
        self.on_cooldown.add((guild_id, author_id))
        await asyncio.sleep(settings.cooldown)  # type: ignore
        self.on_cooldown.remove((guild_id, author_id))

    def _is_on_cooldown(self, author: disnake.Member) -> bool:
        guild_id = author.guild.id
        author_id = author.id
        return (guild_id, author_id) in self.on_cooldown


def _is_message_long_enough(message: disnake.Message,
                            settings: ExperienceSettings) -> bool:
    min_lenght = settings.minimal_message_length
    if min_lenght is None:
        return True
    return (len(message.content) >=
            min_lenght)  # type: ignore


def _is_message_in_allowed_channel(
    message: disnake.Message,
    settings: ExperienceSettings,
) -> bool:
    channels = settings.experience_channels
    return channels is None or message.channel.id in channels  # type: ignore


async def _give_prize_for_activity(
    member: disnake.Member,
    settings: ExperienceSettings,
    message: disnake.Message,
) -> None:
    member_data = get_member(
        member.guild.id,
        member.id,
    )
    logger.info("count text activity for %s on guild %s",
                member, member.guild)
    prev_lvl = exp_to_lvl(member_data.experience)  # type: ignore
    member_data.experience += randint(  # type: ignore
        settings.min_experience_per_message,  # type: ignore
        settings.max_experience_per_message,  # type: ignore
    )
    lvl = exp_to_lvl(member_data.experience)  # type: ignore
    if lvl > prev_lvl:
        await _give_new_lvl_award(member, member_data, settings, lvl, message)
    member_data.save()


async def _give_new_lvl_award(
    member: disnake.Member,
    member_data: Members,
    settings: ExperienceSettings,
    lvl: int,
    message: disnake.Message,
) -> None:
    resonses = []
    for rewarder in _rewarders:
        response = await rewarder(
            member, member_data, settings, lvl
        )
        if response is not None:
            resonses.append(response)
    response_string = "\n".join(resonses)

    embed = DefaultEmbed(
        description=t(
            'lvl_up',
            user_id=member.id,
            old_level=lvl - 1,
            new_level=lvl,
        )
    )
    embed.add_field(
        name=t('lvl_up_bonuses'),
        value=response_string,
    )
    await message.channel.send(
        embed=embed,
        delete_after=LVL_UP_MESSAGE_DISPLAY_TIME,
    )


def setup(bot):
    bot.add_cog(TextActivityCog(bot))
