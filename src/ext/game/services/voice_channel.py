from disnake import CategoryChannel, VoiceChannel, Message, Guild
from typing import Optional

from src.translation import get_translator
from src.logger import get_logger
from src.ext.game.services.games.classes import GameSettings
from src.ext.game.views.game_interfaces.channel_base import ChannelGameInterface

logger = get_logger()
t = get_translator(route="ext.games")

class VoiceGameChannel:
    def __init__(
        self,
        guild: Guild,
        voice_category: CategoryChannel,
        channel: VoiceChannel,
        game_settings: GameSettings,
        game_interface: type[ChannelGameInterface],
        message: Optional[Message] = None
    ) -> None:
        self._guild = guild
        self._voice_category = voice_category
        self._channel = channel
        self._game_settings = game_settings
        self._game_interface = game_interface
        self._message = message
        self._is_connectable = True

    @property
    def voice_category(self) -> CategoryChannel:
        return self._voice_category

    @property
    def channel(self) -> VoiceChannel:
        return self._channel
    
    @property
    def game_settings(self) -> GameSettings:
        return self._game_settings
    
    @property
    def game_interface(self) -> type[ChannelGameInterface]:
        return self._game_interface
    
    @property
    def message(self) -> Optional[Message]:
        return self._message
    
    @property
    def is_connectable(self) -> bool:
        return self._is_connectable
    
    @property
    def user_limit(self) -> int:
        return self._channel.user_limit
    
    @property
    def jump_url(self) -> str:
        return self._channel.jump_url
    
    def add_message(self, message: Message) -> None:
        self._message = message

    def close_or_open_connection(self) -> None:
        self._is_connectable = not self._is_connectable

    async def send_message(self, view) -> Message:
        self._message = await self._channel.send(
            embed=view.create_embed(), view=view
        )
        return self._message
    
    def __len__(self) -> int:
        return len(self._channel.members)
    
    