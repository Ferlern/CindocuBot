from src import settings
from src.bot import bot
from src.logger import setup_logger

if __name__ == '__main__':
    setup_logger()
    bot.run(settings.TOKEN)
