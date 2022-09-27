APP_NAME = 'CindocuBot'

DEBUG = False
TEST_GUILD_IDS = []
IMAGE_CHANNELS = []

TOKEN = ''
DEFAULT_PREFIXES = ['.']
INITIAL_EXTENSIONS = (
    'eval.eval',
    'economy.economy',
    'economy.economy_control',
    'activity.text_activity',
    'activity.voice_activity',
    'relationship.relationship',
    'moderation.moderation',
    'history.history',
    'members.profile',
    'members.top',
    'suggestions.suggestions',
    'reputation.reputation',
    'premoderation.premoderation',
    # ? 'ext.system.status',
    # ? 'ext.sync.sync',
    'up_listener.up_listener',
)

DATABASE = {
    'dbname': 'cindocu',
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',
}

LOGS_PATH = 'logs'
