from __future__ import annotations
from typing import TYPE_CHECKING

import disnake

from src.translation import get_translator
from src.logger import get_logger
from src.utils.filters import remove_bots
from src.ext.game.utils import user_to_player, players_to_members
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

        if lobby.not_enough_players:
            await interaction.response.send_message(t('cant_start'), ephemeral=True)
            return

        members_to_ping = remove_bots(players_to_members(
            view.guild,
            [player for player in lobby.players if player != lobby.creator]
        ))
        message: disnake.InteractionMessage = view.message  # type: ignore
        pings = ', '.join([member.mention for member in members_to_ping])
        content = f"{pings}\n{t('game_started', jump_url=message.jump_url)}"

        lobby.start_game()
        view.stop()
        await view.interface_type.start_from(interaction, lobby.game, lobby.bet)
        if members_to_ping:
            await message.channel.send(content)
