from typing import Optional, Union

import disnake

from src.translation import get_translator
from src.custom_errors import UsedNotOnGuild
from src.discord_views.paginate.peewee_paginator import (PeeweePaginator,
                                                         PeeweeItemSelect)
from src.discord_views.embeds import DefaultEmbed
from src.database.models import ShopRoles
from src.ext.economy.services import (change_balance, get_economy_settings)
from src.ext.economy.shops.base import Shop


t = get_translator(route="ext.economy")


class RolesShop(PeeweePaginator, Shop):
    def __init__(self, author: disnake.Member) -> None:
        super().__init__(
            ShopRoles,
            order_by=-ShopRoles.price,
            filters={'guild': ShopRoles.guild_id == author.guild.id}
        )
        self.add_paginator_item(BuyRoleSelect())
        self.author = author

    async def page_callback(self,
                            interaction: Union[disnake.ModalInteraction,
                                               disnake.MessageInteraction]
                            ) -> None:
        await interaction.response.edit_message(
            embed=self.create_embed(),
            view=self,
        )

    @property
    def name(self) -> str:
        return t('role_shop_name')

    def is_empty(self) -> bool:
        return not self.items

    def create_embed(self) -> disnake.Embed:
        guild = self.author.guild

        coin = get_economy_settings(guild.id).coin
        items_repr = [str(idx) + '. ' + _shop_role_repr(
            item,
            coin,  # type: ignore
        ) for idx, item in enumerate(self.items, 1)]

        embed = DefaultEmbed(
            title=t('roles_shop'),
            description="\n\n".join(items_repr),
        )
        return embed

    async def _response(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.send_message(
            embed=self.create_embed(),
            view=self,
        )


class BuyRoleSelect(PeeweeItemSelect[ShopRoles]):
    def __init__(self) -> None:
        super().__init__(placeholder=t("role_select"))

    def _build_option_description(self,
                                  _: int,
                                  item: ShopRoles) -> Optional[str]:
        return t("role_buy", price=item.price)

    async def _resolve_select(self,
                              inter: disnake.MessageInteraction,
                              item: ShopRoles) -> None:
        author = inter.author
        if not inter.guild or not isinstance(author, disnake.Member):
            raise UsedNotOnGuild()

        role = inter.guild.get_role(item.role_id)  # type: ignore

        if not role:
            await inter.response.send_message(t('role_missing'),
                                              ephemeral=True)
            return

        if role in author.roles:
            await inter.response.send_message(t('role_already_purchased'),
                                              ephemeral=True)
            return

        change_balance(
            guild_id=inter.guild.id,
            user_id=author.id,
            amount=-item.price  # type: ignore
        )
        await author.add_roles(role, reason=t('role_purchased_audit'))
        await inter.response.send_message(
            t('role_purchased', role_id=role.id),
            ephemeral=True,
        )


def _shop_role_repr(item: ShopRoles, coin: str):
    return t(
        'role_repr',
        role_id=item.role_id,
        price=item.price,
        coin=coin,
    )
