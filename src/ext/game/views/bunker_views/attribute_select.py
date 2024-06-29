from __future__ import annotations
from typing import TYPE_CHECKING
import disnake

from src.logger import get_logger
from src.translation import get_translator

if TYPE_CHECKING:
    from src.ext.game.views.game_interfaces.bunker import MasterPanelInterface

logger = get_logger()
t = get_translator(route='ext.games')


class AttributeSelect(disnake.ui.Select):
    view: MasterPanelInterface

    def __init__(self) -> None:
        super().__init__(placeholder=t('attribute_select'))

    def update(self) -> None:
        options = [
            disnake.SelectOption(
                label=name
            ) for name in self.view.attributes_map
        ]
        self.options = options
        self.placeholder = t('attribute_select')
        self.disabled = True if list(self.view.attributes_map)[0] == t('no_attributes_left') else False

    async def callback(
        self,
        interaction: disnake.MessageInteraction,
        /
    ) -> None:
        view = self.view
        name = self.values[0]
        game_data = view.game.game_data
        data = game_data.make_data_fields(view.current_player)

        self.view.current_attribute = next((atr for atr in data if atr[0] == name), (None, None)) 
        self.placeholder = name
        await interaction.response.edit_message(view=self.view)