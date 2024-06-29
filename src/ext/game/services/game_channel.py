from disnake import CategoryChannel, TextChannel, Message, Guild
from typing import Optional

from src.translation import get_translator
from src.logger import get_logger
from src.ext.game.services.games.classes import GameSettings
from src.ext.game.services.voice_channel import VoiceGameChannel

logger = get_logger()
t = get_translator(route="ext.games")

class GameChannel:
    voice_channels: list[VoiceGameChannel] = []

    def __init__(
        self,
        guild: Guild,
        game_settings: GameSettings,
        game_category: CategoryChannel,
        game_name: str,
        channel: TextChannel,
        message: Optional[Message]
    ) -> None:
        self._guild = guild
        self._game_name = game_name
        self._game_settings = game_settings
        self._game_category = game_category
        self._channel = channel
        self._message = message


    @property
    def game_settings(self) -> GameSettings:
        return self._game_settings

    @property
    def game_category(self) -> CategoryChannel:
        return self._game_category

    @property
    def game_name(self) -> str:
        return self._game_name

    @property
    def channel(self) -> TextChannel:
        return self._channel

    @property
    def message(self) -> Optional[Message]:
        return self._message
    

        


