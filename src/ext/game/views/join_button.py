from __future__ import annotations
from typing import TYPE_CHECKING
import disnake

from src.logger import get_logger
from src.translation import get_translator
from src.ext.game.utils import user_to_player

if TYPE_CHECKING:
    from ext.game.views.lobby_view import LobbyView

logger = get_logger()
t = get_translator(route="ext.games")


class JoinGameButton(disnake.ui.Button):
    view: LobbyView

    def __init__(self) -> None:
        super().__init__(
            style=disnake.ButtonStyle.blurple,
            label=t('join_game'),
        )

    async def callback(self, interaction: disnake.MessageInteraction, /) -> None:
        lobby = self.view.lobby
        player = user_to_player(interaction.author)
        if player in lobby:
            await interaction.response.send_message(t('already_joined'), ephemeral=True)
            return
        if not lobby.open and not lobby.is_invited(player):
            await interaction.response.send_message(t('table_closed'), ephemeral=True)
            return
        if lobby.full:
            await interaction.response.send_message(t('max_players'), ephemeral=True)
            return

        lobby.add(user_to_player(interaction.author))
        await self.view.update_using(interaction)
