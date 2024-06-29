import disnake
from disnake.ext import commands
from typing import Optional, List, Dict

from src.bot import SEBot
from src.translation import get_translator
from src.logger import get_logger
from src.database.models import GameChannelSettings
from src.ext.game.views.game_channel_view import GameChannelView
from src.ext.game.services.bunker_settings import BunkerSettings
from src.ext.game.services.game_channel import GameChannel
from src.ext.game.db_services import get_game_channel_settings
from src.ext.game.services.games.bunker import BunkerGame
from src.ext.game.views.game_interfaces.bunker.bunker import BunkerDiscordInterface

logger = get_logger()
t = get_translator(route="ext.games")

GAMES_MAPPING = {
    'bunker_game': (BunkerSettings, BunkerGame, BunkerDiscordInterface),
}

class GameChannelCog(commands.Cog):
    def __init__(self, bot: SEBot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        try:
            await self.setup_game_channel()

        except Exception as e:
            logger.error("tried to setup game channels but an error occured: %s", repr(e))
  
    async def setup_game_channel(self) -> None:
        for guild in self.bot.guilds:
            settings = get_game_channel_settings(guild.id)
            game_category = self.bot.get_channel(settings.category_id) # type: ignore
            voice_category = self.bot.get_channel(settings.voice_game_category_id) # type: ignore
        
            if not (
                isinstance(game_category, disnake.CategoryChannel)
                and isinstance(voice_category, disnake.CategoryChannel)
            ): continue

            channels_data = self.transform_data(settings)
            for key, (channel, message) in channels_data.items():
                (settings, game_type, interface_type) = GAMES_MAPPING[key]
                game_settings = settings(game_type)

                channel_ref = self.bot.get_channel(channel) # type: ignore
                if not isinstance(channel_ref, disnake.TextChannel):
                    continue

                try:
                    message_ref = await channel_ref.fetch_message(message) # type: ignore
                except:
                    message_ref = None

                game_channel = GameChannel(guild, game_settings, game_category, key, channel_ref, message_ref)
                view = GameChannelView(guild, voice_category, game_channel, interface_type)
                await view.update_or_create_channel_message()


    def transform_data(self, settings: GameChannelSettings) -> Dict[str, List[Optional[int]]]:
        game_channels = settings.channels_id
        game_messages = settings.messages_id

        if not (
            isinstance(game_channels, dict)
            and isinstance(game_messages, dict)
        ): return {}

        channel_data = {
            key: [game_channels.get(key), game_messages.get(key)]
            for key in set(game_channels) | set(game_messages)
        }
        return channel_data  


def setup(bot) -> None:
    bot.add_cog(GameChannelCog(bot))
