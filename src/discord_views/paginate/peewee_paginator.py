from typing import Optional, Union, TypeVar, Generic, Sequence
from functools import reduce
from operator import and_

import disnake
import peewee

from src.discord_views.paginate.paginators import Paginator, PaginationItem


T = TypeVar('T', bound=peewee.Model)
Order = Optional[Union[peewee.Field,
                       peewee.Ordering]]


class PeeweePaginator(Generic[T], Paginator):
    def __init__(self,
                 model: type[T],
                 *,
                 timeout: float = 180,
                 items_per_page: int = 10,
                 order_by: Order = None,
                 filters: Optional[dict[str, peewee.Expression]] = None
                 ) -> None:
        self._model = model
        self.filters = filters if filters else {}
        self.order_by = order_by
        self.items_per_page = items_per_page
        self.items: Sequence[T] = []
        super().__init__(timeout=timeout,
                         max_page=self._count_max_page())

    async def resolve_interaction(
        self,
        interaction: Union[disnake.ModalInteraction,
                           disnake.MessageInteraction]
    ) -> None:
        return await super().resolve_interaction(interaction)

    def is_empty(self):
        return not self.items

    def update_page(self):
        self.max_page = self._count_max_page()

    def update(self):
        query = self._build_query()
        self.items = query.paginate(self.page,  # type: ignore
                                    self.items_per_page)
        super().update()

    def _build_query(self) -> peewee.ModelSelect:
        query = self._model.select()
        if self.filters:
            query = query.where(reduce(and_, self.filters.values()))
        if self.order_by:
            query = query.order_by(self.order_by)  # type: ignore
        return query  # type: ignore

    def _count_max_page(self) -> int:
        query = self._build_query()
        return (query.count() //  # type: ignore
                self.items_per_page + 1)


class PeeweeItemSelect(disnake.ui.Select, PaginationItem, Generic[T]):
    view: PeeweePaginator

    def __init__(self,
                 placeholder: Optional[str] = None,
                 ) -> None:
        super().__init__(placeholder=placeholder)

    async def callback(self, interaction: disnake.MessageInteraction):  # noqa
        values = interaction.values
        if not values:
            return

        await self._resolve_select(interaction,
                                   self.view.items[int(values[0])])

    def update(self):
        self.options = [
            disnake.SelectOption(
                label=self._build_option_label(index + 1, item),
                description=self._build_option_description(index + 1, item),
                value=str(index),
            ) for index, item in enumerate(self.view.items)
        ]

    async def _resolve_select(self,
                              inter: disnake.MessageInteraction,
                              item: T) -> None:
        raise NotImplementedError()

    def _build_option_label(self, index: int, item: T) -> str:  # noqa
        return str(index)

    def _build_option_description(self, index: int, item: T) -> Optional[str]:  # noqa
        return None
