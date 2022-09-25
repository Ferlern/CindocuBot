from typing import Generic, Optional, TypeVar

import disnake

from src.discord_views.base_view import BaseView


T = TypeVar('T', bound=BaseView)


class ViewSwitcher(disnake.ui.Select, Generic[T]):
    def __init__(self,
                 placeholder: Optional[str] = None,
                 ) -> None:
        super().__init__(placeholder=placeholder, row=4)
        self._switch_items: dict[str, T] = {}

    def add_view(
        self,
        view: T,
        *,
        label: str,
        description: Optional[str] = None,
    ) -> None:
        view.add_item(self)
        super().add_option(label=label, description=description)
        self._switch_items[label] = view

    async def start_from(
        self,
        inter: disnake.ApplicationCommandInteraction,
        view: Optional[T] = None,
    ) -> None:
        view = view or list(self._switch_items.values())[0]
        await view.start_from(inter)

        message = view.message
        author = view.author
        for my_view in self._switch_items.values():
            my_view.message = message
            my_view.author = author

    async def _resolve_selection(
        self,
        view: T,
        inter: disnake.MessageInteraction
    ) -> None:
        await inter.response.edit_message(
            view=view,
        )

    async def callback(self, interaction: disnake.MessageInteraction, /):
        values = interaction.values
        if not values:
            return  # impossible but just for type checker

        await self._resolve_selection(
            self._switch_items[values[0]],
            interaction
        )
