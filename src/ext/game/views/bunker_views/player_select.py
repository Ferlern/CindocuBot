from __future__ import annotations
from typing import TYPE_CHECKING
import disnake

from src.logger import get_logger
from src.translation import get_translator

if TYPE_CHECKING:
    from src.ext.game.views.game_interfaces.bunker import MasterPanelInterface

logger = get_logger()
t = get_translator(route='ext.games')


class PlayerSelect(disnake.ui.Select):
    view: MasterPanelInterface

    def __init__(self) -> None:
        super().__init__(placeholder="Выбор игрока")

    def update(self) -> None:
        options = [
            disnake.SelectOption(
                label=name
            ) for name in self.view.players_map
        ]
        self.options = options
    
    async def callback(
        self,
        interaction: disnake.MessageInteraction,
        /
    ) -> None:
        name = self.values[0]
        
        self.view.current_player = self.view.players_map[name][0]
        self.view.current_card = name
        self.placeholder = name
        await self.view.update_using(interaction)