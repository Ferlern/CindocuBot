import random
from enum import Enum
from disnake import MessageCommandInteraction, Embed

from src.logger import get_logger
from src.translation import get_translator
from src.ext.gifts.services import (
    add_role_peace,
    remove_activity_present,
    get_activity_presents
)
from src.ext.gifts.utils import request_leg_pets_data, request_def_pets_data
from src.ext.gifts.presents.base_present import Presents
from src.ext.pets.services import create_pet
from src.ext.pets.classes import SpecUtils
from src.ext.economy.services import change_balance
from src.ext.activity.services import get_voice_rewards_settings
from src.discord_views.embeds import DefaultEmbed


logger = get_logger()
t = get_translator(route="ext.gifts")


EMBED_THUMBNAIL = "https://i.imgur.com/VD8QgT3.jpeg"


class ActivityGifts(str, Enum):
    COINS = t("coins")
    DEFAULT_PET = t("default_pet")
    ROLE_SHARD = t("role_shard")
    LEGENDARY_PET = t("legendary_pet")

    @staticmethod
    def chances() -> dict[int, str]: 
        return {
            50: ActivityGifts.COINS,
            36: ActivityGifts.DEFAULT_PET,
            12: ActivityGifts.ROLE_SHARD,
            2: ActivityGifts.LEGENDARY_PET
        }


class ActivityPresent(Presents):
    def __init__(self, interaction: MessageCommandInteraction) -> None:
        super().__init__(interaction)
        self.guild = interaction.guild
        self.user = interaction.user

    async def get_present(self):
        interaction = self.interaction
        amount = get_activity_presents(self.guild.id, self.user.id) # type: ignore
        if amount <= 0:
            await interaction.response.send_message(t('not_enough_presents'), ephemeral = True)
            return

        present = self._get_activity_present()
        remove_activity_present(self.guild.id, self.user.id) # type: ignore
        match present:

            case ActivityGifts.DEFAULT_PET | ActivityGifts.LEGENDARY_PET as rarity:
                await self._pet_present_handler(rarity)
            
            case ActivityGifts.COINS:
                await self._coins_present_handler()

            case ActivityGifts.ROLE_SHARD:
                await self._role_present_handler()

            case _:
                await interaction.response.send_message("Unknown present\\\\\\", ephemeral=True)

    @staticmethod
    def create_embed() -> Embed:
        embed = DefaultEmbed(
            title = t("activity_present"),
            description = (
                t("chances") + "\n\n" + 
                f"**50%** — {ActivityGifts.COINS.value}\n" +
                f"**36%** — {ActivityGifts.DEFAULT_PET.value}\n" +
                f"**12%** — {ActivityGifts.ROLE_SHARD.value}\n" +
                f"**2%** — {ActivityGifts.LEGENDARY_PET.value}\n"
            )
        )
        embed.set_thumbnail(EMBED_THUMBNAIL)
        embed.set_footer(text = t("activity_embed_footer"))
        return embed
    
    def _get_activity_present(self) -> str:
        chances = ActivityGifts.chances()
        return random.choices(
            population=list(chances.values()),
            weights=list(chances.keys()),
            k=1)[0]
    
    async def _coins_present_handler(self) -> None:
        interaction = self.interaction

        change_balance(
            interaction.guild.id, # type: ignore
            interaction.user.id,
            amount := random.randint(100, 500)
        )
        await interaction.response.send_message(t("coins_got", amount=amount), ephemeral=True)

    async def _role_present_handler(self) -> None:
        interaction = self.interaction

        gifts_data = add_role_peace(
            interaction.guild.id, # type: ignore
            interaction.user.id
        )
        if gifts_data.role > 9:
            await self._coins_present_handler()
        elif gifts_data.role < 9:
            await interaction.response.send_message(t("role_shard_got"), ephemeral=True)
        else:
            await self._add_present_role()
            await interaction.response.send_message(t("all_shards_got"), ephemeral=True)
    
    async def _pet_present_handler(self, rarity: str) -> None:
        interaction = self.interaction

        match rarity:

            case ActivityGifts.DEFAULT_PET:
                pet_name, spec, scale = await self._get_def_pet_data()

            case ActivityGifts.LEGENDARY_PET:
                pet_name, spec, scale = await self._get_leg_pet_data()

            case _:
                return
        
        if not interaction.response.is_done():
            await interaction.response.defer(with_message=False)

        users_pet = create_pet(
            guild_id = interaction.guild.id, # type: ignore
            user_id = interaction.user.id,
            name = pet_name,
            exp_scale = scale,
            spec = spec
        )
        await interaction.followup.send(t("pet_got"), ephemeral=True)

    async def _add_present_role(self) -> None: 
        interaction = self.interaction

        settings = get_voice_rewards_settings(interaction.guild.id) # type: ignore
        role = interaction.guild.get_role(settings.gifts_role) # type: ignore
        if role not in interaction.user.roles: # type: ignore
            await interaction.user.add_roles(role) # type: ignore
        
    async def _get_def_pet_data(self) -> tuple:
        interaction = self.interaction

        pet_name = await request_def_pets_data(interaction) or "nameless"
        spec = SpecUtils.get_random_spec()
        scale = 1.0
        return pet_name, spec, scale
    
    async def _get_leg_pet_data(self) -> tuple:
        interaction = self.interaction
        
        pet_name, pet_spec = await request_leg_pets_data(interaction) or ("nameless", None)
        spec = SpecUtils.get_spec_by_letter(pet_spec) or SpecUtils.get_random_spec()
        scale = 2.0
        return pet_name, spec, scale