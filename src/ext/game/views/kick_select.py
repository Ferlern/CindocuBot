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


class KickPlayerSelect(disnake.ui.Select):
    view: LobbyView

    def __init__(self) -> None:
        super().__init__(placeholder=t('kick_player'))

    def update(self) -> None:
        options = []
        for player in self.view.lobby.players:
            member = self.view.guild.get_member(player.player_id)
            options.append(disnake.SelectOption(
                label=str(member) if member else t('unknown'), value=str(player.player_id)
            ))
        self.options = options

    async def callback(self, interaction: disnake.MessageInteraction, /) -> None:
        lobby = self.view.lobby
        host = lobby.creator
        str_ids_to_kick = interaction.values
        if not str_ids_to_kick:
            await self.view.update_using(interaction)
            return
        ids_to_kick = map(int, str_ids_to_kick)

        kicked = []
        for member in map(self.view.guild.get_member, ids_to_kick):
            if member is None:
                continue
            player = user_to_player(member)
            if player in lobby and player != host:
                kicked.append(player)

        if len(kicked) > 0:
            lobby.remove_many(kicked)
        await self.view.update_using(interaction)
