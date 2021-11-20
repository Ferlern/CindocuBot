from core_elements import logger
from core_elements.data_controller.db_clear import create_database
from core_elements.data_controller.models import (Likes, PersonalVoice,
                                                  Relationship, ShopRoles,
                                                  Suggestions, UserInfo,
                                                  UserRoles, ModLog)
from core_elements.logs import Logs
from core_elements.user import MemberDataController

logger.create_logger('DEBUG')
