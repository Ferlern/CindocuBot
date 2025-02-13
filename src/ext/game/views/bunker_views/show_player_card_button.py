from __future__ import annotations
from typing import TYPE_CHECKING
import disnake

from src.ext.game.utils import user_to_player
from src.translation import get_translator
from src.logger import get_logger

if TYPE_CHECKING:
    from src.ext.game.views.game_interfaces import BunkerDiscordInterface

logger = get_logger()
t = get_translator(route='ext.games')

class ShowPlayerCardButton(disnake.ui.Button):
    view: BunkerDiscordInterface

    def __init__(self) -> None:
        super().__init__(
            label=t('show_player_card_button'),
            style=disnake.ButtonStyle.blurple
        )

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        view = self.view
        accepted = view.game.accept_show_card(user_to_player(interaction.user))
        if not accepted:
            await interaction.response.send_message(t('no_card'), ephemeral=True)
            return
        
        game_data = view.game.game_data
        await interaction.response.send_message(
            embed=game_data.players_embeds[user_to_player(interaction.user)],
            ephemeral=True
        )