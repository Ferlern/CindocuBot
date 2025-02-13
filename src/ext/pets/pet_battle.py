import disnake
from disnake.ext import commands
from datetime import datetime
import asyncio
from dateutil.relativedelta import relativedelta

from src.bot import SEBot
from src.logger import get_logger
from src.translation import get_translator
from src.ext.pets.services import get_pet_battle_settings, reset_pets_energy
from src.ext.pets.views.start import PetBattleView


logger = get_logger()
t = get_translator(route='ext.pets')


class PetBattleCog(commands.Cog):
    def __init__(self, bot: SEBot):
        self.bot = bot
        self._is_reseter_started: bool = False

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        try: 
            await self._setup_pet_battle_message()
            if not self._is_reseter_started:
                await self._start_daily_energy_reseter()

        except Exception as e:
            logger.error("tried to setup pet battle but an error occured: %s", repr(e))
     
    
    async def _setup_pet_battle_message(self):
        for guild in self.bot.guilds:
            settings = get_pet_battle_settings(guild.id)
            game_channel = self.bot.get_channel(settings.game_channel) # type: ignore

            if not isinstance(game_channel, disnake.TextChannel):
                continue

            try:
                game_message = await game_channel.fetch_message(settings.game_message) # type: ignore
            except:
                game_message = None

            view = PetBattleView(self.bot, guild, game_channel, game_message)
            await view.create_or_update_game_message()

    async def _start_daily_energy_reseter(self):
        self._is_reseter_started = True
        logger.debug("energy reseter started successfully")
        while True:
            current_time = datetime.now()
            if current_time.hour == 0 and current_time.minute == 0:                
                try:
                    reset_pets_energy()
                    logger.info("pets' energy reseted successfully")
                except Exception as e:
                    logger.error("tried to reset pet's energy but an error occured: %s", repr(e))

            next_day = current_time + relativedelta(days=1)
            next_day = datetime.combine(next_day, datetime.min.time())
            delta_seconds = (next_day - current_time).total_seconds()

            logger.debug("reseter will sleep for %d seconds", delta_seconds)
            await asyncio.sleep(delta_seconds)

def setup(bot: SEBot) -> None:
    bot.add_cog(PetBattleCog(bot))