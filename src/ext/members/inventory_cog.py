from typing import Union

import disnake
from disnake.ext import commands

from src.database.models import RolesInventory
from src.utils.roles import snowflake_roles_intersection
from src.discord_views.paginate.peewee_paginator import PeeweePaginator, PeeweeItemSelect
from src.translation import get_translator
from src.logger import get_logger
from src.formatters import ordered_list, to_mention
from src.ext.economy.services import delete_created_role
from src.ext.members.services import get_inventory_roles
from src.bot import SEBot


logger = get_logger()
t = get_translator(route="ext.inventory")


class InventoryCog(commands.Cog):
    def __init__(self, bot: SEBot) -> None:
        self.bot = bot

    @commands.slash_command()
    async def inventory(
        self,
        inter: disnake.GuildCommandInteraction,
    ) -> None:
        """
        Посмотреть свой инвентарь
        """
        view = RolesInventoryPaginator(inter.author)  # type: ignore
        await view.start_from(inter)


class RolesInventoryPaginator(PeeweePaginator):
    def __init__(
        self,
        author: disnake.Member,
    ) -> None:
        super().__init__(
            RolesInventory,
            order_by=[-RolesInventory.purchase_price, RolesInventory.role_id],  # type: ignore
            filters={
                'guild': RolesInventory.guild == author.guild.id,
                'user': RolesInventory.user == author.id,
            },
        )
        self._guild = author.guild
        self.add_paginator_item(RoleInventorySelect(author))
        self.add_paginator_item(RoleInventoryRemove(author))

    async def page_callback(self,
                            interaction: Union[disnake.ModalInteraction,
                                               disnake.MessageInteraction]
                            ) -> None:
        if self.is_empty():
            await interaction.response.edit_message(
                embed=self.create_embed(),
                view=None,
            )
            self.stop()
        else:
            await interaction.response.edit_message(
                embed=self.create_embed(),
                view=self,
            )

    def create_embed(self) -> disnake.Embed:
        embed = disnake.Embed(title=t('roles_inventory'))
        if not self.items:
            embed.description = t('roles_inventory_empty')
        else:
            embed.description = ordered_list(self.items, lambda it: to_mention(it.role_id, '@&'))
        return embed

    async def _response(self, inter: disnake.ApplicationCommandInteraction) -> None:
        if self.is_empty():
            await inter.response.send_message(
                embed=self.create_embed(),
                ephemeral=True,
            )
        else:
            await inter.response.send_message(
                embed=self.create_embed(),
                view=self,
                ephemeral=True,
            )


class RoleInventorySelect(PeeweeItemSelect):
    def __init__(self, author: disnake.Member) -> None:
        self._author = author
        super().__init__(t('select_role'))

    async def _resolve_select(
        self,
        inter: disnake.MessageInteraction,
        item: RolesInventory,
    ) -> None:
        author = self._author
        new_role = author.guild.get_role(item.role_id)
        if not new_role:
            await inter.response.send_message(t('role_not_found'), ephemeral=True)
            return

        roles = get_inventory_roles(author.guild.id, author.id)
        old_roles = snowflake_roles_intersection(author.roles, roles)
        await inter.response.send_message(t('role_selected'), ephemeral=True)
        print(f'{old_roles = }')
        if old_roles:
            await author.remove_roles(*old_roles)
        await author.add_roles(disnake.Object(item.role_id))


class RoleInventoryRemove(PeeweeItemSelect):
    view: RolesInventoryPaginator

    def __init__(self, author: disnake.Member) -> None:
        self._author = author
        super().__init__(t('delete_role'))

    async def _resolve_select(
        self,
        inter: disnake.MessageInteraction,
        item: RolesInventory,
    ) -> None:
        author = self._author
        item.delete_instance()
        self.view.update()
        await self.view.page_callback(inter)
        deleted = delete_created_role(author.guild.id, author.id, item.role_id)
        role = author.guild.get_role(item.role_id)
        if role and deleted:
            await role.delete()
        elif role and role in author.roles:
            await author.remove_roles(role)


def setup(bot) -> None:
    bot.add_cog(InventoryCog(bot))
