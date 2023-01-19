import datetime
import re
from typing import NamedTuple
from time import time
from enum import Enum
from functools import reduce
from operator import add

import disnake

from src.translation import get_translator


t = get_translator()


class TimeEnum(int, Enum):
    SECOND = 1
    MINUTE = 60
    HOUR = 60 * 60
    DAY = 60 * 60 * 24
    WEEK = 60 * 60 * 24 * 30
    YEAR = 60 * 60 * 24 * 30 * 12

    def localizable_name(self) -> str:
        return self.name.lower()


class TimeUnit(NamedTuple):
    time_type: TimeEnum
    amount: float


DISPLAYABLE_TIME = (
    TimeEnum.HOUR,
    TimeEnum.MINUTE,
    TimeEnum.SECOND,
)
ADDITIONAL_AUTOCOMPLATE_UNITS = (
    TimeUnit(TimeEnum.MINUTE, 10),
    TimeUnit(TimeEnum.MINUTE, 30),
    TimeUnit(TimeEnum.HOUR, 1),
    TimeUnit(TimeEnum.HOUR, 3),
    TimeUnit(TimeEnum.DAY, 1),
)
PARSE_TOKENS = {
    'с': TimeEnum.SECOND,
    'ми': TimeEnum.MINUTE,
    'м': TimeEnum.MINUTE,
    'ч': TimeEnum.HOUR,
    'д': TimeEnum.DAY,
    'ме': TimeEnum.WEEK,
    'г': TimeEnum.YEAR,
    's': TimeEnum.SECOND,
    'm': TimeEnum.MINUTE,
    'h': TimeEnum.HOUR,
    'd': TimeEnum.DAY,
    'w': TimeEnum.WEEK,
    'y': TimeEnum.YEAR,
}
PARSE_PATTERN = re.compile(
    rf"""
    \b
    (\d+(?:\.\d+)?)
    \s*
    ([{"".join({t[0] for t in PARSE_TOKENS})}]\w*)
    \b
    """,
    flags=re.VERBOSE
)


def get_current_day() -> int:
    return int(time() // TimeEnum.DAY)


def second_until_end_of_day() -> int:
    current = datetime.datetime.now()
    tomorrow = current + datetime.timedelta(days=1)
    return (datetime.datetime.combine(
        tomorrow, datetime.time.min
    ) - current).seconds


def display_time(
    seconds: float,
    granularity: int = 3,
    full: bool = False
) -> str:
    if seconds == 0:
        return '0'
    result = []

    for item in DISPLAYABLE_TIME:
        name, count = item.localizable_name(), item.value
        value = int(seconds // count)
        if value:
            seconds -= value * count
            name = t(name, count=value)
            if full:
                result.append(f"{value} {name}")
            else:
                result.append(f"{value}{name[:1]}")
    return ' '.join(result[:granularity])


def parse_time(message: str) -> list[TimeUnit]:
    matches = re.findall(PARSE_PATTERN, message)

    units = []
    for match in matches:
        time_number, time_word = match
        time_type = PARSE_TOKENS.get(
            time_word[:2],
            PARSE_TOKENS[time_word[:1]],
        )
        units.append(TimeUnit(time_type, float(time_number)))
    return units


def parse_time_to_seconds(message: str) -> float:
    units = parse_time(message)
    return reduce(add, (unit.time_type * unit.amount for unit in units))


def localize_time_unit(unit: TimeUnit) -> str:
    return f"{unit.amount:g} {t(unit.time_type.localizable_name(), count=unit.amount)}"  # noqa


async def time_autocomplate(
    _: disnake.ApplicationCommandInteraction,
    user_input: str,
) -> list[str]:
    if len(user_input) > 50:
        return [t('autocomplate_to_long_line')]

    units = parse_time(user_input)
    normalized_current_input = ', '.join([
        localize_time_unit(unit) for unit in units
    ])

    options = []
    if normalized_current_input:
        options.append(normalized_current_input)
        normalized_current_input += ', '

    options.extend([
        normalized_current_input + localize_time_unit(
            unit
        ) for unit in ADDITIONAL_AUTOCOMPLATE_UNITS
    ])
    return options
