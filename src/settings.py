import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = 'CindocuBot'
LOGS_PATH = 'logs'
IMAGE_CHANNELS = []
# Just show more log messages
DEBUG = False

# Test settings. Used to simplify development
DEVELOPMENT = True
TEST_GUILD_IDS = [591972703888605195]
TESTERS_DISCORD_IDS = [511090102542270475]
# If there is no test guild, a new one will be created automatically,
# link will be sent to stdout
CREATE_NEW_TEST_GUILD = False
# Required when changing the database schema (models)
RECREATE_DATABASE_SCHEMA = False
# Data in the database will be set to standard for testing
PREPARE_DATABASE = False
# Require PREPARE_DATABASE
# If TEST guild does not have any required channels or roles,
# they will be created automatically and added to the database
# If any of the settings in the database are missing for the specified testing guilds,
# they will be filled automatically.
PREPARE_GUILDS = False
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
    'game.play_cog',
    # ? 'ext.system.status',
    # ? 'ext.sync.sync',
    'up_listener.up_listener',
    'up_listener.up_reminder',
)

DATABASE = {
    'dbname': os.getenv('POSTGRES_NAME'),
    'host': os.getenv('POSTGRES_HOST'),
    'port': os.getenv('POSTGRES_PORT'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASS'),
}
