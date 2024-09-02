from enum import Enum
import random
from disnake import MessageCommandInteraction, Embed

from src.ext.gifts.presents import Presents
from src.discord_views.embeds import DefaultEmbed


class AnotherGifts(str, Enum):
    SOMETHING1 = "smth1"
    SOMETHING2 = "smth2"

    @staticmethod
    def chances() -> dict[int, str]:
        return {
            50: AnotherGifts.SOMETHING1.value,
            50: AnotherGifts.SOMETHING2.value
        }
    

class AnotherPresent(Presents):
    def __init__(self, interaction: MessageCommandInteraction) -> None:
        super().__init__(interaction)
    
    async def get_present(self) -> None:
        present = self._get_another_present()
        await self.interaction.response.send_message(present, ephemeral=True)
    
    @staticmethod
    def create_embed() -> Embed:
        return DefaultEmbed(
            title="TEST"
        )
    
    def _get_another_present(self) -> str:
        chances = AnotherGifts.chances()
        return random.choices(
            population=list(chances.values()),
            weights=list(chances.keys()),
            k=1)[0]