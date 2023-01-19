from typing import Optional
import disnake

from src.custom_errors import RegularException
from src.discord_views.embeds import ActionFailedEmbed


class BaseView(disnake.ui.View):
    message: disnake.Message
    author: disnake.Member

    def __init__(self, *, timeout: Optional[float] = 180) -> None:
        super().__init__(timeout=timeout)
        self.shown = True

    async def start_from(self, inter: disnake.ApplicationCommandInteraction) -> None:
        await self._response(inter)
        self.message = await inter.original_message()
        self.author = inter.author  # type: ignore

    async def interaction_check(
        self,
        interaction: disnake.MessageInteraction
    ) -> bool:
        if not hasattr(self, 'author'):
            return True
        author_id = self.author.id
        is_author = author_id == interaction.author.id
        if not is_author:
            await interaction.response.send_message(
                f"Извините, <@{author_id}> вызвал это сообщение."
                f" Только он может с ним взаимодействовать",
                ephemeral=True
            )
            return False
        return True

    async def on_error(
        self,
        error: Exception,
        item: disnake.ui.Item,
        interaction: disnake.MessageInteraction,
    ) -> None:
        if isinstance(error, RegularException):
            await interaction.response.send_message(
                embed=ActionFailedEmbed(
                    reason=str(error),
                ),
                ephemeral=True,
            )
        else:
            await super().on_error(error, item, interaction)

    async def on_timeout(self) -> None:
        if not self.shown:
            return

        has_message = hasattr(self, 'message')
        if not has_message:
            return

        for item in self.children:
            item.disabled = True  # type: ignore

        await self.message.edit(view=self)

    async def _response(self, inter: disnake.ApplicationCommandInteraction) -> None:
        await inter.response.send_message(
            view=self,
        )
