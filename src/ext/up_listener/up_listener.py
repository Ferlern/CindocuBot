import asyncio

import disnake
from disnake.ext import commands

from src.discord_views.embeds import DefaultEmbed
from src.ext.economy.services import change_balance
from src.translation import get_translator
from src.bot import SEBot


t = get_translator(route='ext.up_listener')
UP_MESSAGES_CHECKS = {
    464272403766444044: lambda embed: embed.color.value == 4437377,
    575776004233232386: lambda embed: embed.description.startswith('Вы успешно лайкнули'),  # noqa
}


class UpListenerCog(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        check = UP_MESSAGES_CHECKS.get(message.author.id)
        if not check:
            return

        if message.author.id == 464272403766444044:
            await asyncio.sleep(2)
            message = await message.channel.fetch_message(message.id)

        if not message.embeds or not message.guild or not message.interaction:
            return

        if not check(message.embeds[0]):
            return

        change_balance(
            guild_id=message.guild.id,
            user_id=message.interaction.author.id,
            amount=25,
        )

        await message.channel.send(reference=message, embed=DefaultEmbed(
            title=t('thanks'),
            description=t('reward'),
        ))


def setup(bot):
    bot.add_cog(UpListenerCog(bot))
