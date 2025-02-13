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


class OpenCloseTableButton(disnake.ui.Button):
    view: LobbyView

    def update(self) -> None:
        is_open = self.view.lobby.open
        self.style = disnake.ButtonStyle.green if is_open else disnake.ButtonStyle.red
        self.label = t('close_table') if is_open else t('open_table')

    async def callback(self, interaction: disnake.MessageInteraction, /) -> None:
        lobby = self.view.lobby
        if lobby.creator != user_to_player(interaction.author):
            await interaction.response.send_message(
                t('not_a_host', user_id=lobby.creator.player_id), ephemeral=True,
            )
            return
        lobby.open = not lobby.open
        await self.view.update_using(interaction)
