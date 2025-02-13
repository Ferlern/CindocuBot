import peewee

from src import settings
from src.logger import get_logger
from src.bot import bot
from src.database.create import create_database, create_tables
from src.logger import setup_logger


if __name__ == '__main__':
    # Creates a database if it doesn't exist. This shouldn't be a problem
    create_database()
    try:
        create_tables()
    except peewee.IntegrityError:
        logger = get_logger()
        logger.critical(
            'An error occurred while trying to securely create tables in the database. '
            'Probably some of your tables are outdated, try to determine which tables are '
            'causing problems and change them manually. Or call /setup.py script, '
            'it will recreate the database'
        )
        raise

    setup_logger()

    bot.run(settings.TOKEN)
