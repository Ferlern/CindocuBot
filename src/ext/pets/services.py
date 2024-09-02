from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from datetime import datetime

from src.database.models import (
    Pets, psql_db, UserPets,
    PetBattleSettings, AuctionPet,
    AuctionMail
)
from src.logger import get_logger
from src.ext.economy.services import change_balance, CurrencyType
from src.custom_errors import NotEnoughFeedStuff, ItemAlreadySold
from src.database.services import get_member

if TYPE_CHECKING:
    from src.ext.pets.classes import Specialization


logger = get_logger()


ENERGY_PER_GAME = 20


@psql_db.atomic()
def create_pet(
    guild_id: int,
    user_id: int,
    name: str,
    exp_scale: float,
    spec: Specialization
) -> Pets:
    return Pets.create(
        guild = guild_id,
        user = user_id,
        name = name,
        spec = spec.prefix,
        exp_scale = exp_scale,
        health = spec.health,
        max_health = spec.health,
        strength = spec.strength,
        dexterity = spec.dexterity,
        intellect = spec.intellect,
        got_date = datetime.now().timestamp()
    )


@psql_db.atomic()
def create_custom_pet(
    guild_id: int,
    user_id: int,
    name: str,
    exp_scale: float,
    spec: Specialization,
    health: int,
    strength: int,
    dexterity: int,
    intellect: int
) -> Pets:
    return Pets.create(
        guild = guild_id,
        user = user_id,
        name = name,
        spec = spec.prefix,
        exp_scale = exp_scale,
        health = health,
        max_health = health,
        strength = strength,
        dexterity = dexterity,
        intellect = intellect,
        got_date = datetime.now().timestamp()
    )


@psql_db.atomic()
def get_pet_by_id(
    id: int
) -> Pets:
    return Pets.get(id=id)


@psql_db.atomic()
def update_pet(
    id: int,
    level: int,
    experience: int,
    max_health: int,
    health: int,
    strength: int,
    dexterity: int,
    intellect: int,
    winner: bool
) -> None:
    pet = get_pet_by_id(id)
    pet.level = level
    pet.experience = experience
    pet.max_health = max_health
    pet.health = health
    pet.strength = strength
    pet.dexterity = dexterity
    pet.intellect = intellect
    if winner: pet.wins += 1
    else: pet.loses += 1
    pet.save()


@psql_db.atomic()
def get_user_pet(
    guild_id: int,
    user_id: int
) -> UserPets:
    user_pet_data, _ = UserPets.get_or_create(
        guild_id = guild_id,
        user_id = user_id
    )
    return user_pet_data


@psql_db.atomic()
def change_main_pet(
    guild_id: int,
    user_id: int,
    pet: Pets
) -> UserPets:
    user_pet_data = get_user_pet(
        guild_id, user_id
    )
    user_pet_data.current_pet = pet
    user_pet_data.save()
    return user_pet_data


@psql_db.atomic()
def delete_pet(id: int) -> None:
    Pets.delete_by_id(pk=id)


@psql_db.atomic()
def get_main_pet(
    guild_id: int,
    user_id: int,
    /
) -> Optional[Pets]:
    user_pet_data = get_user_pet(
        guild_id, user_id
    )
    return user_pet_data.current_pet


@psql_db.atomic()
def remove_main_pet(
    guild_id: int,
    user_id: int,
    /
) -> None:
    user_pet_data = get_user_pet(
        guild_id, user_id
    )
    if user_pet_data.current_pet:
        user_pet_data.current_pet = None
        user_pet_data.save()


@psql_db.atomic()
def rename_pet(
    id: int,
    new_name: str
) -> Pets:
    pet = get_pet_by_id(id)
    pet.name = new_name
    pet.save()
    return pet


@psql_db.atomic()
def get_pet_battle_settings(
    guild_id: int
) -> PetBattleSettings:
    settings, _ = PetBattleSettings.get_or_create(
        guild = guild_id
    )
    return settings


@psql_db.atomic()
def create_game_channel_message(
    guild_id: int,
    message_id: int
) -> PetBattleSettings:
    settings = get_pet_battle_settings(guild_id)
    settings.game_message = message_id
    settings.save()
    return settings


@psql_db.atomic()
def accept_consume_energy(
    pet_id: int
) -> bool:
    pet = get_pet_by_id(pet_id)
    if pet.energy >= ENERGY_PER_GAME:
        pet.energy -= ENERGY_PER_GAME
        pet.save()
        return True
    return False


@psql_db.atomic()
def return_energy(
    pet_id: int
) -> None:
    pet = get_pet_by_id(pet_id)
    pet.energy = min(pet.energy + ENERGY_PER_GAME, pet.max_energy)
    pet.save()


@psql_db.atomic()
def get_feed_stuff(
    guild_id: int,
    user_id: int
) -> int:
    user_pet_data = get_user_pet(
        guild_id, user_id
    )
    return user_pet_data.feed_stuff


@psql_db.atomic()
def remove_feed_stuff(
    guild_id: int,
    user_id: int
) -> UserPets:
    user_pet_data = get_user_pet(
        guild_id, user_id
    )
    if user_pet_data.feed_stuff <= 0:
        raise NotEnoughFeedStuff
    
    user_pet_data.feed_stuff -= 1
    user_pet_data.save()
    return user_pet_data


@psql_db.atomic()
def add_feed_stuff(
    guild_id: int,
    user_id: int
) -> UserPets:
    user_pet_data = get_user_pet(
        guild_id, user_id
    )
    user_pet_data.feed_stuff += 1
    user_pet_data.save()
    return user_pet_data


@psql_db.atomic()
def feed_pet(
    pet_id: int,
    guild_id: int,
    user_id: int
) -> Pets:
    remove_feed_stuff(
        guild_id, user_id
    )
    pet = get_pet_by_id(pet_id)
    pet.health = min(pet.health + 20, pet.max_health)
    pet.save()
    return pet


@psql_db.atomic()
def restore_energy(
    pet_id: int,
    guild_id: int,
    user_id: int,
    amount: int,
) -> Pets:
    change_balance(
        guild_id, user_id, -amount,
        currency=CurrencyType.CRYSTAL
    )
    pet = get_pet_by_id(pet_id)
    pet.energy = pet.max_energy
    pet.save()
    return pet


@psql_db.atomic()
def buy_feed_stuff(
    guild_id: int,
    user_id: int,
    price: int
) -> None:
    change_balance(
        guild_id, user_id, -price
    )
    add_feed_stuff(guild_id, user_id)
    

@psql_db.atomic()
def pet_pet(
    pet_id: int,
    guild_id: int,
    user_id: int,
    amount: int
) -> Pets:
    pet = get_pet_by_id(pet_id)
    pet.petted = True
    pet.save()

    change_balance(guild_id, user_id, amount)
    return pet


@psql_db.atomic()
def reset_pets_energy():
    (Pets.update({Pets.energy: Pets.max_energy})
     .where(Pets.energy < Pets.max_energy)
     .execute())
    

@psql_db.atomic()
def create_pet_auction_item(
    guild_id: int,
    user_id: int,
    pet_id: int,
    price: int
) -> AuctionPet:
    pet_auc = AuctionPet.create(
        guild=guild_id,
        owner=user_id,
        pet=pet_id,
        price=price,
        sale_date=datetime.now().timestamp()
    )
    return pet_auc


@psql_db.atomic()
def get_pet_auction_item(
    guild_id: int,
    user_id: int,
    pet_id: int
) -> Optional[AuctionPet]:
    return AuctionPet.get_or_none(
        guild=guild_id,
        owner=user_id,
        pet=pet_id
    )

@psql_db.atomic()
def send_to_auction(
    guild_id: int,
    user_id: int,
    pet_id: int,
    price: int
) -> None:
    auc_item = create_pet_auction_item(
        guild_id, user_id, pet_id, price
    )
    pet = auc_item.pet
    pet.on_auction = True
    pet.save()
    remove_main_pet(guild_id, user_id)


@psql_db.atomic()
def buy_auc_item(
    guild_id: int,
    user_id: int,
    owner_id: int,
    pet: Pets,
    price: int
) -> int:
    auc_item = get_pet_auction_item(guild_id, owner_id, pet.id)
    if not auc_item:
        raise ItemAlreadySold

    change_balance(guild_id, user_id, -price)
    change_balance(guild_id, owner_id, proceed := int(price-(price * 0.05)))
    buyer = get_member(guild_id, user_id)

    pet.user = buyer.user_id
    pet.got_date = datetime.now().timestamp()
    pet.save()

    delete_pet_auc_item(guild_id, owner_id, pet.id)
    return proceed
    

@psql_db.atomic()
def delete_pet_auc_item(
    guild_id: int,
    owner_id: int,
    pet_id: int
) -> None:
    item = get_pet_auction_item(guild_id, owner_id, pet_id)
    if not item:
        raise ItemAlreadySold
    
    pet = get_pet_by_id(pet_id)
    pet.on_auction = False
    pet.save()
    
    item.delete_by_id(
        (guild_id, owner_id, pet_id)
    )


@psql_db.atomic()
def create_auc_mail(
    guild_id: int,
    user_id: int,
    buyer_id: int,
    proceed: int
) -> AuctionMail:
    return AuctionMail.create(
        guild=guild_id,
        user=user_id,
        buyer_id=buyer_id,
        proceed=proceed,
        buy_date=datetime.now().timestamp()
    )


@psql_db.atomic()
def make_read(
    mail_id: int
) -> AuctionMail:
    mail = AuctionMail.get_by_id(mail_id)
    mail.is_read = True
    mail.save()
    return mail


@psql_db.atomic()
def change_price(
    guild_id: int,
    owner_id: int,
    pet_id: int,
    new_price: int
) -> AuctionPet:
    item = get_pet_auction_item(guild_id, owner_id, pet_id)
    if not item: 
        raise ItemAlreadySold
    
    item.price = new_price
    item.save()
    return item