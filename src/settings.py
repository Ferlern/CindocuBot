import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = 'CindocuBot'
LOGS_PATH = 'logs'
IMAGE_CHANNELS = []
# Just show more log messages
DEBUG = False

# Test settings. Used to simplify development
DEVELOPMENT = False
TEST_GUILD_IDS = []
TESTERS_DISCORD_IDS = []
# If there is no test guild, a new one will be created automatically,
# link will be sent to stdout
CREATE_NEW_TEST_GUILD = True
# Required when changing the database schema (models)
RECREATE_DATABASE_SCHEMA = True
# Data in the database will be set to standard for testing
PREPARE_DATABASE = True
# Require PREPARE_DATABASE
# If TEST guild does not have any required channels or roles,
# they will be created automatically and added to the database
# If any of the settings in the database are missing for the specified testing guilds,
# they will be filled automatically.
PREPARE_GUILDS = True
# End of test settings

TOKEN = os.getenv('TOKEN')
DEFAULT_PREFIXES = ['.']
INITIAL_EXTENSIONS = (
    'actions.restriction_cog',
    'eval.eval',
    'economy.economy',
    'economy.economy_control',
    'activity.text_activity',
    'activity.voice_activity',
    'relationship.relationship',
    'moderation.moderation',
    'personal_voice.controller',
    'history.history',
    'members.profile',
    'members.top',
    'members.welcome',
    'members.inventory_cog',
    'members.on_guild_cog',
    'members.role_controller',
    'suggestions.suggestions',
    'reputation.reputation',
    'premoderation.premoderation',
    'fun.fun',
    'fun.feb_cog',
    'fun.puzzle',
    'fun.meow_counter',
    'game.play_cog',
    'game.game_channel_cog',
    # ? 'ext.system.status',
    # ? 'ext.sync.sync',
    'up_listener.up_listener',
    'up_listener.up_reminder',
    'events.event_notification',
    'gifts.gifts_cog',
    'pets.pet_profile',
    'pets.pet_battle',
    'pets.pet_auction',
    'pets.pet_creation',
    'fun.fountain',
)

DATABASE = {
    'dbname': os.getenv('POSTGRES_NAME'),
    'host': os.getenv('POSTGRES_HOST'),
    'port': os.getenv('POSTGRES_PORT'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASS'),
}
