from abc import abstractmethod
import disnake
from .base import DiscordInterface, T


class SingleDiscordInterface(DiscordInterface[T]):
    async def on_timeout(self) -> None:
        self.game.force_end()

    @abstractmethod
    def create_embed(self) -> disnake.Embed:
        raise NotImplementedError
