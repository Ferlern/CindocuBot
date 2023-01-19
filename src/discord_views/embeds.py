from disnake import Embed

from src.translation import get_translator


t = get_translator()


class DefaultEmbed(Embed):
    def __init__(self, **kwargs) -> None:
        super().__init__(color=0x93a5cd, **kwargs)


class ActionFailedEmbed(Embed):
    def __init__(self, reason: str) -> None:
        super().__init__(
            title=t('action_failed'),
            description=t('action_failed_reason', reason=reason),
            color=0x93a5cd,
        )
