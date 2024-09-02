from enum import Enum
from src.translation import get_translator


t = get_translator(route='ext.pet_battle')


class Actions(str, Enum):
    START = "game_started"
    NEW_TURN = "new_turn"
    ATTACK = "attack"
    DODGE = "dodge"
    HIT = "hit"
    SKILL_USAGE = "skill_usage"
    FULL = "full"
    POISON = "poison"
    END = "end"

    def get_translated(self, **kwargs):
        return t(self.value, **kwargs)