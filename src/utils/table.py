import re
from typing import Sequence


NOT_UA_RU_EN_PATTERN = r"[^єЄїЇіІёЁа-яА-ЯA-Za-z0-9\s!@#₴$№\"%^&*()_+=\-`~\\\]\[{}|';:/.,?><]+"  # noqa
DASH_SYMBOL = '—'


class DiscordTable:
    """Create 40-max-length table-like code block"""

    def __init__(
        self,
        max_columns_length: Sequence[int],
        columns: Sequence[str],
    ) -> None:
        """Create 40-max-length table-like code block

        kwargs
        --------
        columns `(list[str])`:
        list of column names.

        max_columns_length `(list[int])`:
        list of maximum length per columns.
        if the information in the column (or even the name of this column)
        is longer than the specified value, it will be truncated to max-1,
        "…" will be added.

        values `(list[list[str]])`:
        one list for one row in table.
        """
        self._columns = columns
        self._max_columns_length = max_columns_length
        self._values: list[Sequence[str]] = []

    def clear(self) -> None:
        self._values = []

    def add_row(self, row: Sequence[str]) -> None:
        self._values.append(row)

    def __len__(self) -> int:
        return sum(self._max_columns_length)

    def __str__(self) -> str:
        string = '```\n'
        string += " ".join(self._prepared_columns())
        string += "\n"
        string += self._get_dashes_string()
        string += "\n"
        string += "\n".join(
            [' '.join(row) for row in self._prepared_values()]
        )
        string += '\n```'
        return string

    def _get_dashes_string(self) -> str:
        return " ".join(
            [DASH_SYMBOL * max_length
             for max_length in self._max_columns_length]
        )

    def _prepared_columns(self) -> list[str]:
        return [
            self._prepare_string(column, max_length)
            for column, max_length in zip(self._columns, self._max_columns_length)
        ]

    def _prepared_values(self) -> list[list[str]]:
        return [
            [self._prepare_string(
                value,
                max_length,
            ) for value, max_length in zip(row, self._max_columns_length)]
            for row in self._values
        ]

    def _prepare_string(self, string: str, max_length: int) -> str:
        string = normalize_and_cut_string(string, max_length)
        return f'{string:{max_length}}'


def normalize_and_cut_string(text: str, max_length: int) -> str:
    text = normalize_string(text)
    if len(text) > max_length:
        text = text[:max_length - 1] + "…"
    return text


def normalize_string(string: str) -> str:
    string = re.sub(NOT_UA_RU_EN_PATTERN, '', string)
    return string.replace('\n', ' ').replace('\r', ' ')
