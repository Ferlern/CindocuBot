from enum import Enum

import disnake

from src.translation import get_translator


t = get_translator(route='ext.fun')


class Categories(str, Enum):
    PAT = 'pat'
    KISS = 'kiss'
    HUG = 'hug'
    LICK = 'lick'
    BITE = 'bite'
    SLAP = 'slap'

    def get_embed_text(
        self,
        author: disnake.Member,
        target: disnake.Member,
    ) -> str:
        return t(self.value, user_id=author.id, target_id=target.id)

    def get_translated_name(self) -> str:
        return t(self.value + '_name')
