from typing import Optional

from src.translation import get_translator


t = get_translator()


class BaseCustomException(Exception):
    """Base class for all exceptions called by bot code"""


class CriticalException(BaseCustomException):
    """
    Base class for exceprions about code errors
    """


class RegularException(BaseCustomException):
    """
    Base class for discord user invalid usage,
    e.g. unexpected or missed argument
    """


class UsedNotOnGuild(CriticalException):
    pass


class DailyAlreadyReceived(RegularException):
    pass


class NotEnoughMoney(RegularException):
    def __init__(self, amount: int, message: Optional[str] = None) -> None:
        if message is None:
            message = t('not_enough_money_default', amount=amount)
        self.message = message
        self.amount = amount
        super().__init__(self.message)


class CannotUseTwice(RegularException):
    def __init__(self, message: Optional[str] = None) -> None:
        if message is None:
            message = t('cannot_use_twice_default')
        self.message = message
        super().__init__(self.message)


class UserAlreadyInRelationship(RegularException):
    pass


class TargetAlreadyInRelationship(RegularException):
    pass


class MaxSlotsAmount(RegularException):
    pass


class MaxBitrateReached(RegularException):
    pass


class BadConfigured(RegularException):
    def __init__(self, message: Optional[str] = None) -> None:
        if message is None:
            message = t('bad_configured')
        self.message = message
        super().__init__(self.message)


class ActionRestricted(RegularException):
    def __init__(self, message: Optional[str] = None) -> None:
        if message is None:
            message = t('action_restricted')
        self.message = message
        super().__init__(self.message)


class BadProjectSettings(CriticalException):
    pass
