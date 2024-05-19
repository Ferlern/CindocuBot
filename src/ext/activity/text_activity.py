import asyncio
from random import randint

import disnake
from disnake.ext import commands

from src.bot import SEBot
from src.logger import get_logger
from src.translation import get_translator
from src.database.models import ChannelExperienceSettings, ExperienceSettings, Members
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
    def __init__(self, bot: SEBot) -> None:
        self.bot = bot
        self.on_cooldown: set[tuple[int, int]] = set()

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message) -> None:
        author = message.author
        channel = message.channel
        if author.bot or not isinstance(author, disnake.Member):
            return

        settings = get_experience_settings(author.guild.id)
        channels_settings = settings.experience_channels
        if not channels_settings:
            return

        channel_setting = channels_settings.get(str(channel.id))
        if not channel_setting:
            return

        checks = (
            not self._is_on_cooldown(author),
            _is_message_long_enough(message, channel_setting),
        )

        if all(checks):
            await _give_prize_for_activity(author, settings, channel_setting, message)
            await self._set_cooldown(author, channel_setting)

    async def _set_cooldown(
        self,
        author: disnake.Member,
        channel_settings: ChannelExperienceSettings,
    ) -> None:
        cooldown = channel_settings.get("cooldown")
        if not cooldown:
            return

        guild_id = author.guild.id
        author_id = author.id
        self.on_cooldown.add((guild_id, author_id))
        await asyncio.sleep(cooldown)
        self.on_cooldown.remove((guild_id, author_id))

    def _is_on_cooldown(self, author: disnake.Member) -> bool:
        guild_id = author.guild.id
        author_id = author.id
        return (guild_id, author_id) in self.on_cooldown


def _is_message_long_enough(
    message: disnake.Message,
    channel_settings: ChannelExperienceSettings,
) -> bool:
    min_lenght = channel_settings.get("minimal_message_length")
    if min_lenght is None:
        return True
    return (len(message.content) >=
            min_lenght)


async def _give_prize_for_activity(
    member: disnake.Member,
    settings: ExperienceSettings,
    channel_settings: ChannelExperienceSettings,
    message: disnake.Message,
) -> None:
    min_exp = channel_settings.get("min_experience_per_message", 1)
    max_exp = channel_settings.get("max_experience_per_message", 1)
    min_exp, max_exp = min(min_exp, max_exp), max(min_exp, max_exp)

    member_data = get_member(
        member.guild.id,
        member.id,
    )
    logger.info("count text activity for %s on guild %s",
                member, member.guild)
    prev_lvl = exp_to_lvl(member_data.experience)
    gained_experience = randint(
        channel_settings["min_experience_per_message"],
        channel_settings["max_experience_per_message"],
    )
    member_data.experience += gained_experience
    member_data.monthly_chat_activity += gained_experience

    lvl = exp_to_lvl(member_data.experience)
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


def setup(bot) -> None:
    bot.add_cog(TextActivityCog(bot))
