import disnake
from typing import Optional

from src.bot import SEBot
from src.logger import get_logger
from src.translation import get_translator
from src.discord_views.paginate.paginators import ItemsPaginator
from src.ext.pets.classes import Journal

logger =  get_logger
t = get_translator(route='ext.pets')
   

class JournalPaginator(ItemsPaginator[Journal]):
    def __init__(
        self,
        bot: SEBot,
        thread: disnake.Thread
    ) -> None:
        self._bot = bot
        self.thread = thread
        self.message: Optional[disnake.Message] = None
        super().__init__(
            items=[Journal()],
            items_per_page=1,
            timeout=0
        )

    @property
    def item(self) -> Journal:
        return self.items[0]

    async def page_callback(
        self,
        interaction: disnake.ModalInteraction | disnake.MessageInteraction
    ) -> None:
        await interaction.response.edit_message(
            embed=self.item,
            view=self
        )

    async def _create_message(
        self,
    ) -> None:
        self.message = await self.thread.send(
            embed=self.item,
            view=self
        )

    async def start_from(self) -> None:
        await self._create_message()

    async def add_row(self, action, **kwargs) -> None:
        self.turn_to_last_page()
        if self.item.full:
            self.add_page(Journal())

        self.item.add(action, **kwargs)
        await self.update_view()

    async def update_view(self):
        await self.message.edit( # type: ignore
            embed=self.item,
            view=self
        )