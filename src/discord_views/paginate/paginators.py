from abc import abstractmethod
from math import ceil
from typing import Optional, Union, TypeVar, Generic

import disnake
from disnake.ui import Button

from src.discord_views.base_view import BaseView


T = TypeVar('T')


class PaginationItem(disnake.ui.Item):
    @abstractmethod
    def update(self):
        ...


class FirstPageButton(Button, PaginationItem):
    def __init__(self):
        self.view: Paginator
        super().__init__(emoji="⏪",
                         style=disnake.ButtonStyle.blurple)

    async def callback(self,  # pylint: disable=arguments-differ
                       interaction: disnake.MessageInteraction
                       ) -> None:
        self.view.page = 1
        await self.view.resolve_interaction(interaction)

    def update(self) -> None:
        self.disabled = self.view.page == 1


class PrevPageButton(Button, PaginationItem):
    def __init__(self):
        self.view: Paginator
        super().__init__(emoji="◀",
                         style=disnake.ButtonStyle.secondary)

    async def callback(self,  # pylint: disable=arguments-differ
                       interaction: disnake.MessageInteraction
                       ) -> None:
        self.view.page -= 1
        await self.view.resolve_interaction(interaction)

    def update(self) -> None:
        self.disabled = self.view.page == 1


class NextPageButton(Button, PaginationItem):
    def __init__(self):
        self.view: Paginator
        super().__init__(emoji="▶",
                         style=disnake.ButtonStyle.secondary)

    async def callback(self,  # pylint: disable=arguments-differ
                       interaction: disnake.MessageInteraction
                       ) -> None:
        self.view.page += 1
        await self.view.resolve_interaction(interaction)

    def update(self) -> None:
        self.disabled = self.view.page == self.view.max_page


class LastPageButton(Button, PaginationItem):
    def __init__(self):
        self.view: Paginator
        super().__init__(emoji="⏩",
                         style=disnake.ButtonStyle.blurple)

    async def callback(self,  # pylint: disable=arguments-differ
                       interaction: disnake.MessageInteraction
                       ) -> None:
        if self.view.max_page:
            self.view.page = self.view.max_page
        await self.view.resolve_interaction(interaction)

    def update(self) -> None:
        max_page = self.view.max_page
        self.disabled = not max_page or self.view.page == max_page


class SetPageButton(Button, PaginationItem):
    def __init__(self):
        self.view: Paginator
        super().__init__(style=disnake.ButtonStyle.secondary)

    async def callback(self,  # pylint: disable=arguments-differ
                       interaction: disnake.MessageInteraction
                       ) -> None:
        await interaction.response.send_modal(
            ChangePageModal(self.view),
        )

    def update(self) -> None:
        page_str = str(self.view.page)
        if self.view.max_page is not None:
            page_str += f"/{self.view.max_page}"
        self.label = page_str


class Paginator(BaseView):
    def __init__(
        self,
        *,
        timeout: float = 180,
        max_page: Optional[int] = None,
    ) -> None:
        # TODO this is necessary due to multiple inheritance
        # shops will stop work if we just call super(). Should be fixed in future
        super(BaseView, self).__init__(timeout=timeout)
        # paginator does not call __init__ of base view, so set shown here
        self.shown = True
        self._paginator_items: list[PaginationItem] = []
        self._max_page = max_page
        self._page = 1
        self.update()
        self.add_paginator_item(FirstPageButton())
        self.add_paginator_item(PrevPageButton())
        self.add_paginator_item(SetPageButton())
        self.add_paginator_item(NextPageButton())
        self.add_paginator_item(LastPageButton())

    @property
    def page(self) -> int:
        return self._page

    @page.setter
    def page(self, value: int):
        self._page = self._check_page_range(value)
        self.update()

    @property
    def max_page(self) -> Optional[int]:
        return self._max_page

    @max_page.setter
    def max_page(self, value: Optional[int]):
        self._max_page = value
        self._page = self._check_page_range(self._page)
        self.update()

    async def page_callback(self,
                            interaction: Union[disnake.ModalInteraction,
                                               disnake.MessageInteraction]
                            ) -> None:
        await interaction.response.edit_message(view=self)

    async def resolve_interaction(
        self,
        interaction: Union[disnake.ModalInteraction,
                           disnake.MessageInteraction],
    ) -> None:
        await self.page_callback(interaction)

    def add_paginator_item(self, item: PaginationItem) -> None:
        self._paginator_items.append(item)
        super().add_item(item)
        item.update()

    def update(self):
        self._update_paginator_items()

    def _update_paginator_items(self):
        for item in self._paginator_items:
            item.update()

    def _check_page_range(self, page: int):
        if self.max_page is not None:
            page = min(page, self.max_page)
        page = max(1, page)
        return page


class ItemsPaginator(Generic[T], Paginator):
    def __init__(
        self,
        items: list[T],
        items_per_page: int,
        *,
        timeout: float = 180,
    ) -> None:
        max_page = ceil(len(items) / items_per_page) or 1
        self._all_items = items
        self.items: list[T] = []
        super().__init__(timeout=timeout, max_page=max_page)

    def is_empty(self) -> bool:
        return not self._all_items

    def update(self) -> None:
        page = self.page
        self.items = self._all_items[(page-1)*10:page*10]
        return super().update()

    async def page_callback(
        self,
        interaction: Union[disnake.ModalInteraction, disnake.MessageInteraction],
    ) -> None:
        return await super().page_callback(interaction)


class ChangePageModal(disnake.ui.Modal):
    def __init__(self,
                 paginator: Paginator) -> None:
        components = [
            disnake.ui.TextInput(
                label="Введите страницу",
                custom_id="cpm:new_page",
                style=disnake.TextInputStyle.short,
                value=str(paginator.page),
                max_length=20,
            ),
        ]
        super().__init__(title="Изменение страницы",
                         custom_id="cpm:set_page",
                         components=components)
        self.__paginator = paginator

    async def callback(self, inter: disnake.ModalInteraction) -> None:  # noqa: C901
        try:
            self.__paginator.page = int(inter.text_values["cpm:new_page"])
        except ValueError:
            pass
        await self.__paginator.resolve_interaction(inter)
