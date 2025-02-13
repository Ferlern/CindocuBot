from abc import ABC, abstractmethod
from disnake import MessageCommandInteraction, Embed

class Presents(ABC):
    def __init__(self, interaction: MessageCommandInteraction) -> None:
        self.interaction = interaction

    @abstractmethod
    async def get_present() -> None:
        raise NotImplementedError()

    @abstractmethod
    def create_embed() -> Embed:
        raise NotImplementedError()