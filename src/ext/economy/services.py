from enum import Enum

from src.database.models import (Members, Users, psql_db, Guilds,
                                 EconomySettings, ShopRoles, CreatedShopRoles, RolesInventory)
from src.database.services import get_member, create_related
from src.logger import LoggingLevel, get_logger, log_calls
from src.custom_errors import CriticalException, NotEnoughMoney, DailyAlreadyReceived
from src.utils.time_ import get_current_day


logger = get_logger()

COINS_PER_CRYSTAL = 10


class CurrencyType(str, Enum):
    COIN = 'coin'
    CRYSTAL = 'crystal'

    @property
    def model_field(self) -> int:
        return {
            CurrencyType.COIN: Members.balance,
            CurrencyType.CRYSTAL: Members.donate_balance,
        }[self]

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
@log_calls(level=LoggingLevel.INFO)
def change_balances(
    guild_id: int,
    user_ids: list[int],
    amount: int,
    *,
    currency: CurrencyType = CurrencyType.COIN,
) -> None:
    field = currency.model_field
    target = ((Members.guild_id == guild_id) & (Members.user_id << user_ids))  # type: ignore
    if amount < 0 < (
        Members.
        select().
        where((field < amount) & target).
        count()
    ):
        raise CriticalException("Can't change balances, some members don't have enough money")
    (
        Members.
        update({field: field + amount})
        .where(target)
        .execute()
    )


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
def take_bonus(
    guild_id: int,
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
def add_shop_role(
    guild_id: int,
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
def delete_shop_role(
    guild_id: int,
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
    roles_to_delete = (
        CreatedShopRoles.
        select(CreatedShopRoles).
        join(Members, on=(
            (Members.guild_id == CreatedShopRoles.guild) &
            (Members.user_id == CreatedShopRoles.creator) &
            (CreatedShopRoles.role_id.is_null(False))  # type: ignore
        )).
        join(EconomySettings, on=(CreatedShopRoles.guild == EconomySettings.guild_id)).
        where(Members.donate_balance < EconomySettings.role_day_tax)
    )
    to_delete = list(roles_to_delete)

    squery = roles_to_delete.select(CreatedShopRoles.role_id)
    RolesInventory.delete().where(RolesInventory.role_id << squery).execute()
    CreatedShopRoles.delete().where(CreatedShopRoles.role_id << squery).execute()
    psql_db.execute_sql("""
        UPDATE members
        SET donate_balance = donate_balance - economysettings.role_day_tax
        FROM economysettings, createdshoproles
        WHERE (
            members.guild_id=economysettings.guild_id AND
            createdshoproles.creator_id=members.user_id AND
            createdshoproles.guild_id=members.guild_id AND
            createdshoproles.role_id IS NOT NULL
        );
    """)
    return list(to_delete)


@psql_db.atomic()
def swap_crystals_to_coins(
    guild_id: int,
    user_id: int,
    amount: int,
) -> None:
    member_data = get_member(guild_id, user_id)
    if member_data.donate_balance < 1:
        raise NotEnoughMoney(amount)
    amount = min(amount, member_data.donate_balance)
    change_balance(guild_id, user_id, -amount, currency=CurrencyType.CRYSTAL)
    change_balance(guild_id, user_id, amount * COINS_PER_CRYSTAL, currency=CurrencyType.COIN)
