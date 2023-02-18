from src import settings
from src.bot import bot
from src.logger import setup_logger
from src.database.create import create_tables, create_database


if __name__ == '__main__':
    create_database()
    create_tables()
    setup_logger()
    bot.run(settings.TOKEN)
