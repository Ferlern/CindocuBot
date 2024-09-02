import disnake

from src.database.models import EconomySettings
from src.ext.economy.shops.base import Shop
from src.ext.economy.roles_shop import DefaultRolesShop, CreatedRolesShop
from src.ext.personal_voice.shop import VoiceShop
from src.ext.pets.pet_shop import PetShop


_shops: list[type[Shop]] = [
    DefaultRolesShop,
    CreatedRolesShop,
    VoiceShop,
    PetShop
]


def get_not_empty_shops(author: disnake.Member, settings: EconomySettings) -> list[Shop]:
    shops = [shop(author, settings) for shop in _shops]
    shops = list(filter(
        lambda shop: not shop.is_empty(),
        shops,
    ))
    return shops
