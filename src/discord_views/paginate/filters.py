from typing import Mapping

import disnake
import peewee


class ItemSelectFilter(disnake.ui.Select):
    def __init__(self, mame: str, **kwargs):
        super().__init__(**kwargs)
        self._name = mame

    def _prepare_values(self) -> list:
        raise NotImplementedError()

    async def callback(self, interaction: disnake.MessageInteraction):  # noqa
        self.view.filters[self._name] = self._prepare_values()  # type: ignore
        await self.view.resolve_interaction(interaction)  # type: ignore


class PeeweeSelectFilter(ItemSelectFilter):
    def __init__(self,
                 name: str,
                 options: Mapping[str, peewee.Expression],
                 **kwargs):
        select_options = [disnake.SelectOption(
            label=key,
        ) for key in options]
        super().__init__(name, options=select_options, **kwargs)
        self._options = options

    def _prepare_values(self) -> list[peewee.Expression]:
        return [self._options[value] for value in self.values]
