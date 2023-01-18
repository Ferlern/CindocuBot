from abc import abstractmethod
from typing import Optional

import disnake

from src.database.models import EconomySettings
from src.discord_views.base_view import BaseView


class Shop(BaseView):
    def __init__(
        self,
        author: disnake.Member,
        settings: EconomySettings,
        *,
        timeout: Optional[float] = 180
    ) -> None:
        super().__init__(timeout=timeout)
        self._settings = settings
        self.author = author

    @abstractmethod
    def create_embed(self) -> disnake.Embed:
        pass

    @abstractmethod
    def is_empty(self) -> bool:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    async def start_from(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.send_message(
            embed=self.create_embed(),
            view=self,
        )
        self.message = await inter.original_message()
