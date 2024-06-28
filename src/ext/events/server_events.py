from enum import Enum
from typing import Optional, Sequence

from src.discord_views.shortcuts import ModalInput
from src.translation import get_translator

t = get_translator(route='ext.events')

class EventType():
    def __init__(
        self,
        event: str,
        is_concrete: bool
    ) -> None:
        self.event = event
        self.event_name = t(event)
        self.event_option = t(event + '_option')
        self.gif = t(event + '_gif')
        self.image = t(event + '_image')
        self.is_concrete = is_concrete

    def get_long_desc(self, **kwargs) -> str:
        return t(self.event + "_long_desc", **kwargs)
    
    def get_short_desc(self, **kwargs) -> str:
        return t(self.event + "_short_desc", **kwargs)


class Mafia(EventType):
    def __init__(self) -> None:
        super().__init__(
            event = 'mafia',
            is_concrete = True
        )

class Codenames(EventType):
    def __init__(self) -> None:
        super().__init__(
            event = 'codenames',
            is_concrete = True
        )


class Gartic(EventType):
    def __init__(self) -> None:
        super().__init__(
            event = 'gartic',
            is_concrete=True
        )
    
class ServerEvents(Enum):
    MAFIA = Mafia()
    CODENAMES = Codenames()
    GARTIC = Gartic()

    def get_event_option(self) -> str:
        return self.value.event_option
    
    def get_modal_params(
        self,
    ) -> Sequence[ModalInput[str]]:
        inputs = [
            ModalInput(label=t("event_time"),
                    placeholder=t("time_placeholder"),
                    required=True),
            ModalInput(label=t("event_channel"), 
                    placeholder=t("can_be_empty"),
                    required=False),
        ]
        if not self.value.is_concrete:
            inputs.insert(1,
                ModalInput(
                    label=t("event_addition_name"),
                    placeholder=t("addition_name_placeholder"),
                    required=True
                )
            )
            inputs.insert(2,
                ModalInput(
                    label=t("event_addition_gif"),
                    placeholder=t("addition_gif_value"),
                    value=t("addition_gif_value"),
                    required=True
                )
            )
        return tuple(inputs)
    


