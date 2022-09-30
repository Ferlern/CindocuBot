import disnake
from disnake.ext import commands

from src.discord_views.paginate.peewee_paginator import (PeeweePaginator,
                                                         PeeweeItemSelect)
from src.discord_views.base_view import BaseView
from src.database.models import History
from src.translation import get_translator
from src.utils.table import DiscordTable
from src.discord_views.embeds import DefaultEmbed
from src.utils.slash_shortcuts import only_admin
from src.bot import SEBot


t = get_translator(route='ext.history')


class HistoryCog(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot

    @commands.slash_command(**only_admin)
    async def history(
        self,
        inter: disnake.GuildCommandInteraction,
    ):
        """
        Показать историю событий на этом сервере
        """
        view = HistoryPaginator(inter.guild)
        await view.start_from(inter)


class HistoryPaginator(PeeweePaginator[History]):
    def __init__(self, guild: disnake.Guild) -> None:
        super().__init__(
            History,
            items_per_page=15,
            order_by=-History.id,
            filters={'guild': History.guild_id == guild.id},
        )
        self.add_paginator_item(HistorySelect())
        self._guild = guild

    async def continue_from(
        self,
        inter: disnake.MessageInteraction,
    ) -> None:
        await inter.response.edit_message(
            embed=self.create_embed(),
            view=self,
        )

    def create_embed(self) -> disnake.Embed:
        table = DiscordTable(
            max_columns_length=(6, 12, 10, 8),
            columns=(
                t('table_inxed'),
                t('table_action_user'),
                t('table_action'),
                t('table_action_time'),
            )
        )
        for item in self.items:
            member = self._guild.get_member(item.user_id.id)  # type: ignore
            member_name = member.name if member else t('not_found_name')
            table.add_row((
                str(item.id),
                member_name,
                item.action_name,  # type: ignore
                str(item.creation_time.strftime('%d/%m/%y')),  # type: ignore
            ))

        return DefaultEmbed(
            title=t('history'),
            description=str(table),
        )

    async def _response(
        self,
        inter: disnake.ApplicationCommandInteraction
    ) -> None:
        await inter.response.send_message(
            embed=self.create_embed(),
            view=self,
        )


class HistorySelect(PeeweeItemSelect):
    view: HistoryPaginator

    async def _resolve_select(
        self,
        inter: disnake.MessageInteraction,
        item: History,
    ) -> None:
        await HistoryRowInfo.continue_from(
            inter=inter,
            item=item,
            backref=self.view,
        )

    def _build_option_label(
        self,
        _: int,
        item: History,
    ) -> str:
        return f'#{item.id}'


class HistoryRowInfo(BaseView):
    def __init__(
        self,
        item: History,
        backref: HistoryPaginator,
    ) -> None:
        super().__init__()
        self._backref = backref
        self._item = item

    @classmethod
    async def continue_from(
        cls,
        inter: disnake.MessageInteraction,
        item: History,
        backref: HistoryPaginator,
    ):
        instance = cls(item, backref)
        instance.message = inter.message
        instance.author = inter.author  # type: ignore
        await inter.response.edit_message(
            embed=instance.create_embed(),
            view=instance,
        )

    @disnake.ui.button(label=t('back'))
    async def back(
        self,
        _: disnake.ui.Button,
        inter: disnake.MessageInteraction,
    ) -> None:
        await self._backref.continue_from(
            inter=inter,
        )

    def create_embed(self) -> disnake.Embed:
        item = self._item
        embed = DefaultEmbed(
            title=t('action', number=item.id),
            description=item.description
        )
        embed.add_field(
            name=t('user'),
            value=f"<@{item.user_id}>",
        )
        embed.add_field(
            name=t('time'),
            value=disnake.utils.format_dt(
                item.creation_time, 'f'  # type: ignore
            ),
        )
        return embed


def setup(bot):
    bot.add_cog(HistoryCog(bot))
