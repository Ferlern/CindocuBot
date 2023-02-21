from enum import Enum, auto


class GameState(Enum):
    # TODO move state logic to state machine
    WAIT_FOR_PLAYER = auto()
    WAIT_FOR_INPUT = auto()
    END = auto()


class WrongState(Exception):
    pass
