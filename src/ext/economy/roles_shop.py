from typing import Optional, Union

import disnake
import peewee

from src.utils.color import validate_hex
from src.utils.custom_ids import (CREATE_ROLE, CREATE_ROLE_COLOR, CREATE_ROLE_MODAL,
                                  CREATE_ROLE_NAME, CREATE_ROLE_SHOWN)
from src.translation import get_translator
from src.custom_errors import NotEnoughMoney, UsedNotOnGuild
from src.discord_views.paginate.peewee_paginator import (PeeweePaginator,
                                                         PeeweeItemSelect)
from src.discord_views.embeds import DefaultEmbed
from src.database.models import EconomySettings, ShopRoles, CreatedShopRoles
from src.ext.economy.services import (change_balance, add_created_role, has_role_in_inventory,
                                      add_role_to_inventory, has_created_role, CurrencyType)
from src.ext.economy.shops.base import Shop


t = get_translator(route="ext.economy")
Order = Optional[
    list[Union[peewee.Field, peewee.Ordering]]
]


class RolesShop(PeeweePaginator, Shop):
    def __init__(
        self,
        model,
        author: disnake.Member,
        settings: EconomySettings,
        *,
        order_by: Order = None,
        filters: Optional[dict[str, peewee.Expression]] = None,
    ) -> None:
        self._settings = settings
        super().__init__(
            model,
            order_by=order_by,
            filters=filters,
        )
        self.add_paginator_item(self._create_select())
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
        coin = self._settings.coin
        items_repr = [str(idx) + '. ' + _shop_role_repr(
            item,
            coin,
        ) for idx, item in enumerate(self.items, 1)]

        embed = DefaultEmbed(
            title=t('roles_shop'),
            description="\n\n".join(items_repr),
        )
        return embed

    async def _response(self, inter: disnake.ApplicationCommandInteraction) -> None:
        await inter.response.send_message(
            embed=self.create_embed(),
            view=self,
        )

    def _create_select(self) -> 'BuyRoleSelect':
        return BuyRoleSelect()


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
            await inter.response.send_message(t('role_missing'), ephemeral=True)
            return

        guild_id = inter.guild.id
        user_id = author.id
        price = item.price

        if has_role_in_inventory(guild_id, user_id, role.id):
            await inter.response.send_message(t('role_already_purchased'), ephemeral=True)
            return
        change_balance(
            guild_id=inter.guild.id,
            user_id=author.id,
            amount=-item.price,
        )
        add_role_to_inventory(
            guild_id, user_id, role.id, price
        )
        await inter.response.send_message(
            t('role_purchased', role_id=role.id),
            ephemeral=True,
        )


class DefaultRolesShop(RolesShop):
    def __init__(self, author: disnake.Member, settings: EconomySettings) -> None:
        super().__init__(
            ShopRoles,
            author,
            settings,
            order_by=[-ShopRoles.price, ShopRoles.role_id],  # type: ignore
            filters={'guild': ShopRoles.guild_id == author.guild.id},
        )


class CreatedRolesShop(RolesShop):
    def __init__(self, author: disnake.Member, settings: EconomySettings) -> None:
        super().__init__(
            CreatedShopRoles,
            author,
            settings,
            order_by=[-CreatedShopRoles.price, CreatedShopRoles.role_id],  # type: ignore
            filters={
                'guild': CreatedShopRoles.guild == author.guild.id,
                'approved': CreatedShopRoles.approved == True,  # type: ignore # noqa
                'shown': CreatedShopRoles.shown == True,  # type: ignore # noqa
            },
        )

    @property
    def name(self) -> str:
        return t('created_roles_shop_name')

    def is_empty(self) -> bool:
        return False

    def create_embed(self) -> disnake.Embed:
        settings = self._settings
        embed = super().create_embed()
        embed.title = t('created_roles_shop')
        embed.add_field(
            name=t('create_role_title'),
            value=t(
                'create_role_desc',
                amount=settings.role_creation_price,
                coin=settings.crystal,
                tax_amount=settings.role_day_tax,
                tax_coin=settings.crystal,
            )
        )
        return embed

    def _create_select(self) -> 'BuyRoleSelect':
        return BuyCreatedRoleSelect(self._settings)


class BuyCreatedRoleSelect(BuyRoleSelect):  # pylint: disable=too-many-ancestors
    def __init__(self, settings: EconomySettings) -> None:
        super().__init__()
        self._settings = settings

    def update(self) -> None:
        super().update()
        self.add_option(label=t('create_role'), value=CREATE_ROLE)

    async def callback(self, interaction: disnake.MessageInteraction, /) -> None:
        values = interaction.values
        if not values:
            return

        if values[0] == CREATE_ROLE:
            await interaction.response.send_modal(CreateRoleModal(self._settings))
            return
        return await super().callback(interaction)

    async def _resolve_select(
        self,
        inter: disnake.MessageInteraction,
        item: CreatedShopRoles,
    ) -> None:
        await super()._resolve_select(inter, item)  # type: ignore
        change_balance(inter.guild.id, item.creator.id, item.price // 5)  # type: ignore


class CreateRoleModal(disnake.ui.Modal):
    def __init__(self, settings: EconomySettings) -> None:
        self._settings = settings
        components = [
            disnake.ui.TextInput(
                label=t("create_role_name"),
                custom_id=CREATE_ROLE_NAME,
                style=disnake.TextInputStyle.short,
                min_length=1,
                max_length=50,
            ),
            disnake.ui.TextInput(
                label=t("create_role_color"),
                custom_id=CREATE_ROLE_COLOR,
                style=disnake.TextInputStyle.short,
                min_length=7,
                max_length=7,
            ),
            disnake.ui.TextInput(
                label=t("create_role_shown"),
                custom_id=CREATE_ROLE_SHOWN,
                style=disnake.TextInputStyle.short,
                value='+',
                min_length=1,
                max_length=1,
            ),
        ]
        super().__init__(
            title=t('create_role_alert'),
            custom_id=CREATE_ROLE_MODAL,
            components=components,
        )

    async def callback(self, inter: disnake.ModalInteraction, /) -> None:
        shown_mapping = {
            '-': False,
            '+': True,
        }
        shown = inter.text_values[CREATE_ROLE_SHOWN]
        if not validate_hex(inter.text_values[CREATE_ROLE_COLOR]):
            await inter.response.send_message(t('invalid_hex'), ephemeral=True)
            return
        if has_created_role(inter.guild_id, inter.author.id):  # type: ignore
            await inter.response.send_message(t('second_created_role'), ephemeral=True)
            return
        if shown not in shown_mapping:
            await inter.response.send_message(t('invalid_shown'), ephemeral=True)
            return

        try:
            change_balance(
                inter.guild_id,  # type: ignore
                inter.author.id,
                -self._settings.role_creation_price,
                currency=CurrencyType.CRYSTAL,
            )
        except NotEnoughMoney:
            await inter.response.send_message(
                t('not_enough_crystals', crystal=self._settings.crystal),
                ephemeral=True,
            )
            return
        add_created_role(
            inter.guild_id,  # type: ignore
            inter.author.id,
            shown_mapping[shown],
            properties=inter.text_values,
        )
        await inter.response.send_message(t('create_role_succes'), ephemeral=True)


def _shop_role_repr(item: ShopRoles, coin: str) -> str:
    return t(
        'role_repr',
        role_id=item.role_id,
        price=item.price,
        coin=coin,
    )
