import psycopg2
from src.database.models import *
from src.settings import DATABASE


tables = (UserRoles, Likes, Members,
          Relationships, RelationshipParticipant,
          ShopRoles, Suggestions, Codes, SuggestionSettings,
          RelationshipsSettings, ModerationSettings, EconomySettings,
          ExperienceSettings, PersonalVoice, Users, Guilds,
          History, PremoderationSettings, PremoderationItem,
          WelcomeSettings, ReminderSettings, Reminders, CreatedShopRoles, RolesInventory,
          GameStatistics, Puzzles,
          VoiceRewardsSettings, GameChannelSettings, EventsSettings, 
          Pets, Gifts, UserPets, PetBattleSettings, AuctionPet, AuctionMail, FontainCounter)


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


def recreate_tables() -> None:
    """drop & create tables in DB"""
    psql_db.drop_tables(tables)
    psql_db.create_tables(tables)
    psql_db.close()


def create_tables() -> None:
    psql_db.create_tables(tables)
    psql_db.close()