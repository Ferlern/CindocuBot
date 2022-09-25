from typing import Optional, Sequence, TypeVar, Generic


T = TypeVar('T')


class Cycle(Generic[T]):
    def __init__(self, items: Sequence[T]):
        self._items = list(items)
        self._index = 0

    def __iter__(self):
        return self

    def __next__(self) -> Optional[T]:
        if not self._items:
            return None

        self._index = self._index % len(self._items)
        current = self._index
        self._index += 1
        return self._items[current]

    def remove(self, item: T) -> None:
        index = self._items.index(item)
        if self._index > index:
            self._index -= 1
        self._items.remove(item)
