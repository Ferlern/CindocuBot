from src.database.models import (Members, psql_db, Guilds,
                                 EconomySettings, ShopRoles)
from src.database.services import get_member, create_related
from src.logger import get_logger
from src.custom_errors import NotEnoughMoney, DailyAlreadyReceived
from src.utils.time_ import get_current_day


logger = get_logger()


@psql_db.atomic()
def change_balance(guild_id: int, user_id: int, amount: int) -> Members:
    member = get_member(guild_id, user_id)
    member.balance += amount  # type: ignore
    if member.balance < 0:
        raise NotEnoughMoney(abs(member.balance))  # type: ignore
    member.save()
    logger.info('Balance of memeber %d changed %d', user_id, amount)
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
