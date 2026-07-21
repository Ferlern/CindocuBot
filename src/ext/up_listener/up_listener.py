import types

import disnake
from disnake.ext import commands

from src.bot import SEBot
from src.discord_views.embeds import DefaultEmbed
from src.ext.economy.services import change_balance
from src.logger import get_logger
from src.translation import get_translator
from src.utils import custom_events

logger = get_logger()
t = get_translator(route='ext.up_listener')

UP_MONITORING_ID = 1244278183814238259
LIKE_MONITORING_ID = 1135447052734709761

def _is_up(embed): return embed.color is not None and embed.color.value == 4437377
def _is_like(embed): return bool(embed.description) and embed.description.startswith(('Вы успешно лайкнули', 'You successfully liked'))

UP_MESSAGES_CHECKS = {
  UP_MONITORING_ID: lambda e: UP_MONITORING_ID if _is_up(e) else None,
  LIKE_MONITORING_ID: lambda e: LIKE_MONITORING_ID if _is_like(e) else None,
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
        
        resolve = UP_MESSAGES_CHECKS.get(message.author.id)

        if not resolve:
            return
        
        if not message.embeds or not message.guild or not message.interaction:
            logger.info('Message from %d, but no embeds / guild / interaction', message.author.id)
            return

        monitoring_id = resolve(message.embeds[0])

        if monitoring_id is None:
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
            custom_events.EventName.MONITORING_GUILD_PROMOTED.value,
            message.guild,
            types.SimpleNamespace(id=monitoring_id),
        )

        await message.channel.send(reference=message, embed=DefaultEmbed(
            title=t('thanks'),
            description=t('reward'),
        ))


def setup(bot) -> None:
    bot.add_cog(UpListenerCog(bot))
