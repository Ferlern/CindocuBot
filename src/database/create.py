from src.database.models import *

tables = (UserRoles, Likes, Members,
          Relationships, RelationshipParticipant,
          ShopRoles, Suggestions, Codes, SuggestionSettings,
          RelationshipsSettings, ModerationSettings, EconomySettings,
          ExperienceSettings, PersonalVoice, Users, Guilds,
          History, PremoderationSettings, PremoderationItem,
          WelcomeSettings, ReminderSettings, Reminders, CreatedShopRoles, RolesInventory)


def create_tables() -> None:
    """drop & create tables in DB"""
    psql_db.drop_tables(tables)
    psql_db.create_tables(tables)
    psql_db.close()

    print('DB created succesfuly')
