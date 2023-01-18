import re
from enum import Enum


class EmbedColors(int, Enum):
    DEFAULT = 0x93a5cd
    ACTION_FAILED = 0x93a5cd
    RELATIONSHIPS = 0xffc0cb
    RELATIONSHIPS_ACCEPT = 0x9cee90
    RELATIONSHIPS_REFUSE = 0xe74c3c


def validate_hex(hex_code: str) -> bool:
    return bool(re.match(r'#(?:[0-9a-fA-F]{1,2}){3}$', hex_code))
