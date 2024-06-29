from typing import Optional
from abc import abstractmethod

import disnake

from src.bot import SEBot
from src.logger import get_logger
from src.translation import get_translator
from src.ext.game.services.games import BunkerGame
from src.ext.game.utils import user_to_player

logger = get_logger()
t = get_translator(route='ext.games')

class BunkerGameInterface(disnake.ui.View):
    def __init__(
        self,
        bot: SEBot,
        guild: disnake.Guild,
        message: disnake.Message,
        game: BunkerGame,
        *,
        timeout: Optional[int],
    ) -> None:
        super().__init__(timeout=timeout)
        self.game = game
        self.guild = guild
        self.message = message
        self.bot = bot

    @abstractmethod
    def create_embed(self) -> disnake.Embed:
        raise NotImplementedError

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        if user_to_player(interaction.author) not in self.game.players:
            await interaction.response.send_message(t('not_a_player'), ephemeral=True)
            return False
        return True

