import disnake
from disnake.ext import commands
from enum import Enum

from src.logger import get_logger
from src.translation import get_translator
from src.bot import SEBot
from src.utils.slash_shortcuts import only_admin
from src.converters import not_bot_member

from src.ext.pets.classes.specialization import *
from src.ext.pets.services import create_custom_pet


logger = get_logger()
t = get_translator(route='ext.pets')


class Specs(Enum):
    WARRIOR = Warrior
    HUNTER = Hunter
    MAGE = Mage
    DEMON = Demon

    def get_option(self) -> str:
        return str(self.name)


class ExpScales(float, Enum):
    DEFAULT = 1.0
    LEGENDARY = 2.0


class PetCreationCog(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot

    @commands.slash_command(**only_admin)
    async def create_custom_pet(
        self,
        inter: disnake.GuildCommandInteraction,
        owner = commands.Param(converter=not_bot_member),
        spec: str = commands.Param(
            choices={spec.get_option(): 
                     spec.name for spec in Specs}),
        name: str = 'noname',
        exp_scale: ExpScales = ExpScales.DEFAULT,
        health: int = 0,
        strength: int = 0,
        dexterity: int = 0,
        intellect: int = 0
    ) -> None:
        """
        custom
        """
        type = Specs[spec]
        specialization: Specialization = type.value()

        health = abs(health) or specialization.health
        strength = abs(strength) or specialization.strength
        dexterity = abs(dexterity) or specialization.dexterity
        intellect = abs(intellect) or specialization.intellect

        pet = create_custom_pet(
            inter.guild.id, owner.id,
            name, exp_scale,
            specialization,
            health, strength,
            dexterity, intellect
        )
        logger.info('custom pet for %d created', owner.id)
        await inter.response.send_message(
            f"custom pet for <@{owner.id}> created: {name}, " +
            f"{health} {strength} {dexterity} {intellect}"
        )


def setup(bot: SEBot) -> None:
    bot.add_cog(PetCreationCog(bot))