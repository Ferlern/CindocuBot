from __future__ import annotations
from typing import TYPE_CHECKING
import disnake

from src.ext.game.utils import user_to_player
from src.translation import get_translator
from src.logger import get_logger
if TYPE_CHECKING:
    from ext.game.views.lobby_view import LobbyView

logger = get_logger()
t = get_translator(route="ext.games")


class InviteSelect(disnake.ui.UserSelect):
    view: LobbyView

    def __init__(self) -> None:
        super().__init__(placeholder=t('invite_player'))

    async def callback(self, interaction: disnake.MessageInteraction, /) -> None:
        lobby = self.view.lobby
        player = user_to_player(self.values[0])

        if lobby.creator != user_to_player(interaction.author):
            await interaction.response.send_message(
                t('not_a_host', user_id=lobby.creator.player_id), ephemeral=True,
            )
            return
        if lobby.is_invited(player) or player in lobby:
            await interaction.response.send_message(t('already_invited'), ephemeral=True)
            return
        if len(lobby.invited) > 25:
            await interaction.response.send_message(t('too_many_invites'), ephemeral=True)
            return

        lobby.invite(player)
        await interaction.response.send_message(t('invited'), ephemeral=True)
        await self.view.update()
