import psycopg2
from src.database.models import *
from src.settings import DATABASE


tables = (UserRoles, Likes, Members,
          Relationships, RelationshipParticipant,
          ShopRoles, Suggestions, Codes, SuggestionSettings,
          RelationshipsSettings, ModerationSettings, EconomySettings,
          ExperienceSettings, PersonalVoice, Users, Guilds,
          History, PremoderationSettings, PremoderationItem,
          WelcomeSettings, ReminderSettings, Reminders, CreatedShopRoles, RolesInventory)


def create_database() -> None:
    connection = psycopg2.connect(
        host=DATABASE['host'],
        port=DATABASE['port'],
        user=DATABASE['user'],
        password=DATABASE['password']
    )
    cursor = connection.cursor()
    cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s;", (DATABASE['dbname'],))
    exists = cursor.fetchone()
    if not exists:
        cursor.execute('CREATE DATABASE %s;', (DATABASE['dbname'],))


def create_tables() -> None:
    """drop & create tables in DB"""
    psql_db.drop_tables(tables)
    psql_db.create_tables(tables)
    psql_db.close()

    print('DB created succesfuly')
