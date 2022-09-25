import disnake

from src.ext.economy.shops.base import Shop
from src.ext.economy.roles_shop import RolesShop
from src.ext.personal_voice.shop import VoiceShop


_shops: list[type[Shop]] = [
    RolesShop,
    VoiceShop
]


def get_not_empty_shops(author: disnake.Member) -> list[Shop]:
    shops = [shop(author) for shop in _shops]
    shops = list(filter(
        lambda shop: not shop.is_empty(),
        shops,
    ))
    return shops
