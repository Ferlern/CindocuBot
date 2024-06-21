from enum import Enum

from src.discord_views.shortcuts import ModalInput
from src.translation import get_translator

t = get_translator(route='ext.events')

class ServerEvents(str, Enum):
    MAFIA = 'mafia'
    CODENAMES = 'codenames'

    def get_translated_name(self) -> str:
        return t(self.value + '_name')
    
    def get_modal_params(
        self,
    ) -> tuple[ModalInput, ModalInput]:
        return (
            ModalInput(label=t("event_time"),
                       placeholder="1 января, 00:00",
                       required=True),
            ModalInput(label=t("event_channel"), 
                       placeholder=t("can_be_empty"),
                       required=False)
        )