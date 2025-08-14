import disnake
from disnake.ext import commands

from src.discord_views.embeds import DefaultEmbed
from src.ext.economy.services import change_balance
from src.translation import get_translator
from src.bot import SEBot
from src.logger import get_logger
from src.utils import custom_events


logger = get_logger()
t = get_translator(route='ext.up_listener')
UP_MESSAGES_CHECKS = {
    464272403766444044: lambda embed: embed.color.value == 4437377,
    575776004233232386: lambda embed: embed.description.startswith((
        'Вы успешно лайкнули', 'You successfully liked')),  # noqa
}


class UpListenerCog(commands.Cog):
    def __init__(self, bot: SEBot) -> None:
        self.bot = bot
        self._m = []

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message) -> None:
        await self._check_for_up(message)

    @commands.Cog.listener()
    async def on_message_edit(self, _, after: disnake.Message) -> None:
        await self._check_for_up(after)

    async def _check_for_up(self, message: disnake.Message) -> None:
        if message.id in self._m:
            return
        check = UP_MESSAGES_CHECKS.get(message.author.id)
        if not check:
            return

        # if message.author.id == 464272403766444044:
        #     await asyncio.sleep(4)
        #     message = await message.channel.fetch_message(message.id)

        if not message.embeds or not message.guild or not message.interaction:
            logger.info('Message from %d, but no embeds / guild / interaction', message.author.id)
            return

        if not check(message.embeds[0]):
            logger.info('Message from %d, but embed check is not passed', message.author.id)
            return

        self._m.append(message.id)
        self._m = self._m[-10:]

        change_balance(
            guild_id=message.guild.id,
            user_id=message.interaction.author.id,
            amount=25,
        )
        self.bot.dispatch(
            custom_events.EventName.MONITORING_GUILD_PROMOTED,
            message.guild,
            message.author,
        )

        await message.channel.send(reference=message, embed=DefaultEmbed(
            title=t('thanks'),
            description=t('reward'),
        ))


def setup(bot) -> None:
    bot.add_cog(UpListenerCog(bot))
