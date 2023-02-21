from __future__ import annotations
from typing import TYPE_CHECKING

import disnake

from src.translation import get_translator
from src.logger import get_logger
from src.ext.game.utils import user_to_player
if TYPE_CHECKING:
    from ext.game.views.lobby_view import LobbyView

logger = get_logger()
t = get_translator(route="ext.games")


class StartGameButton(disnake.ui.Button):
    view: LobbyView

    def __init__(self) -> None:
        super().__init__(
            style=disnake.ButtonStyle.green,
            label=t('start_game'),
        )

    async def callback(self, interaction: disnake.MessageInteraction, /) -> None:
        view = self.view
        lobby = view.lobby
        if lobby.creator != user_to_player(interaction.author):
            await interaction.response.send_message(
                t('not_a_host', user_id=lobby.creator.player_id), ephemeral=True,
            )
            return
        if len(lobby) < 2:
            await interaction.response.send_message(t('cant_start'), ephemeral=True)
            return

        lobby.start_game()
        view.stop()
        await view.interface_type.start_from(interaction, lobby.game, lobby.bet)
