import asyncio
import typing
import weakref


class AsyncioLockManager:
    def __init__(self) -> None:
        self._locks = weakref.WeakValueDictionary()

    def __call__(self, key: typing.Hashable) -> asyncio.Lock:
        locks = self._locks
        if key in locks:
            return locks[key]

        lock = asyncio.Lock()
        locks[key] = lock
        return lock
