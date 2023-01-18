from enum import Enum

from src.database.models import (Members, Users, psql_db, Guilds,
                                 EconomySettings, ShopRoles, CreatedShopRoles, RolesInventory)
from src.database.services import get_member, create_related
from src.logger import get_logger
from src.custom_errors import CriticalException, NotEnoughMoney, DailyAlreadyReceived
from src.utils.time_ import get_current_day


logger = get_logger()


class CurrencyType(str, Enum):
    COIN = 'coin'
    CRYSTAL = 'crystal'

    def get_guild_repr(self, settings: EconomySettings) -> str:
        return {
            CurrencyType.COIN: settings.coin,
            CurrencyType.CRYSTAL: settings.crystal,
        }[self]


@psql_db.atomic()
def change_balance(
    guild_id: int,
    user_id: int,
    amount: int,
    *,
    currency: CurrencyType = CurrencyType.COIN,
) -> Members:
    member = get_member(guild_id, user_id)
    if currency == CurrencyType.COIN:
        member.balance += amount
        balance = member.balance
    elif currency == CurrencyType.CRYSTAL:
        member.donate_balance += amount
        balance = member.donate_balance
    else:
        raise CriticalException(f'no currency {currency}')

    if balance < 0:
        raise NotEnoughMoney(abs(balance))

    member.save()
    logger.info('Balance of memeber %d changed %d, currency is %s', user_id, amount, currency)
    return member


@psql_db.atomic()
def set_balance(guild_id: int, user_id: int, amount: int) -> None:
    member = get_member(guild_id, user_id)
    member.balance = amount  # type: ignore
    if member.balance < 0:
        raise NotEnoughMoney(abs(member.balance))  # type: ignore
    member.save()
    logger.info('Balance of memeber %d setted to %d', user_id, amount)


@create_related(Guilds)
@psql_db.atomic()
def get_economy_settings(guild_id: int, /) -> EconomySettings:
    settings, _ = EconomySettings.get_or_create(
        guild_id=guild_id
    )
    return settings


@psql_db.atomic()
def take_bonus(guild_id: int,
               user_id: int,
               amount: int
               ) -> Members:
    member = get_member(guild_id, user_id)
    if member.bonus_taked_on_day >= get_current_day():
        raise DailyAlreadyReceived()

    member = change_balance(guild_id, user_id, amount)
    member.bonus_taked_on_day = get_current_day()  # type: ignore
    member.save()
    return member


@create_related(Guilds)
@psql_db.atomic()
def add_shop_role(guild_id: int,
                  /,
                  role_id: int,
                  price: int,
                  ) -> ShopRoles:
    item = ShopRoles.create(
        guild_id=guild_id,
        role_id=role_id,
        price=price,
    )
    return item


@create_related(Guilds)
@psql_db.atomic()
def delete_shop_role(guild_id: int,
                     /,
                     role_id: int,
                     ) -> None:
    item: ShopRoles = ShopRoles.get(
        guild_id=guild_id,
        role_id=role_id,
    )
    item.delete_instance()


@create_related(Guilds, Users)
@psql_db.atomic()
def add_created_role(
    guild_id: int,
    user_id: int,
    /,
    shown: bool,
    properties: dict,
) -> ShopRoles:
    item = CreatedShopRoles.create(
        guild_id=guild_id,
        creator=user_id,
        shown=shown,
        properties=properties,
    )
    return item


@create_related(Guilds, Users)
@psql_db.atomic()
def add_role_to_inventory(
    guild_id: int,
    user_id: int,
    /,
    role_id: int,
    purchase_price: int,
) -> ShopRoles:
    return RolesInventory.create(
        guild=guild_id,
        user=user_id,
        role_id=role_id,
        purchase_price=purchase_price,
    )


@create_related(Guilds, Users)
@psql_db.atomic()
def has_role_in_inventory(
    guild_id: int,
    user_id: int,
    /,
    role_id: int,
) -> bool:
    return bool(RolesInventory.get_or_none(
        guild=guild_id,
        user=user_id,
        role_id=role_id,
    ))


@create_related(Guilds, Users)
@psql_db.atomic()
def has_created_role(
    guild_id: int,
    user_id: int,
    /,
) -> bool:
    return bool(CreatedShopRoles.get_or_none(
        guild=guild_id,
        creator=user_id,
    ))


@psql_db.atomic()
def delete_created_role(
    guild_id: int,
    user_id: int,
    role_id: int,
) -> int:
    query = CreatedShopRoles.delete().where(
        CreatedShopRoles.guild == guild_id,
        CreatedShopRoles.creator == user_id,
        CreatedShopRoles.role_id == role_id,
    )
    return query.execute()


@psql_db.atomic()
def take_tax_for_roles() -> list[CreatedShopRoles]:
    lack_of_balance = (
        Members.
        select(Members.user_id)
        .join(EconomySettings, on=(Members.guild_id == EconomySettings.guild_id))
        .where(Members.donate_balance < EconomySettings.role_day_tax)
    )
    to_delete_squery = CreatedShopRoles.select(
        CreatedShopRoles.role_id).where(CreatedShopRoles.creator == lack_of_balance)
    to_delete = list(CreatedShopRoles.select().where(CreatedShopRoles.creator == lack_of_balance))

    RolesInventory.delete().where(RolesInventory.role_id == to_delete_squery).execute()
    CreatedShopRoles.delete().where(CreatedShopRoles.creator == lack_of_balance).execute()
    psql_db.execute_sql("""
        UPDATE members
        SET donate_balance = donate_balance - economysettings.role_day_tax
        FROM economysettings, createdshoproles
        WHERE (
            members.guild_id=economysettings.guild_id AND
            createdshoproles.creator_id=members.user_id
        );
    """)
    return to_delete
