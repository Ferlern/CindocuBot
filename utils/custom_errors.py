class ConfirmationError(Exception):
    pass


class WaitError(Exception):
    pass


class BonusAlreadyReceived(Exception):
    pass


class NotEnoughMoney(Exception):
    pass


class OnlyAuthorError(Exception):
    pass


class UserAlreadyMarried(Exception):
    pass


class TargetAlreadyMarried(Exception):
    pass


class NotMarried(Exception):
    pass


class MarriedWithAnother(Exception):
    pass


class VoiceAlreadyCreated(Exception):
    pass


class MaxSlotsAmount(Exception):
    pass


class MaxBitrateReached(Exception):
    pass


class AlreadyLiked(Exception):
    pass


class NotConfigured(Exception):
    pass
