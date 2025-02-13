from time import monotonic

from src.logger import get_logger


logger = get_logger()


class Counter:
    def __init__(
        self,
        timer: float,
        amount: int,
        delay: float = 0,
    ) -> None:
        self._timer = timer
        self.amount = amount
        self._delay = delay
        self._last_ready_time: float = 0
        self._adding_times: list[float] = []

    def add(self) -> None:
        self._filter()
        self._adding_times.append(monotonic())

    def remove_delay(self) -> None:
        self._last_ready_time = 0

    @property
    def ready(self) -> bool:
        self._filter()
        if self._delay and self._delay > monotonic() - self._last_ready_time:
            logger.debug("Counter on delay")
            return False

        if len(self._adding_times) > self.amount:
            self._last_ready_time = monotonic()
            return True

        return False

    def _filter(self) -> None:
        current_time = monotonic()
        self._adding_times = [
            time for time in self._adding_times if current_time - time < self._timer]
