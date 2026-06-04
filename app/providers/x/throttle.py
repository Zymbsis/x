import asyncio
import time


class RequestGapThrottle:
    def __init__(self, gap_sec: float) -> None:
        self._gap_sec = gap_sec
        self._lock = asyncio.Lock()
        self._last_finished_at: float | None = None

    async def wait_turn(self) -> None:
        async with self._lock:
            if self._last_finished_at is None:
                return
            wait = self._gap_sec - (time.monotonic() - self._last_finished_at)
            if wait > 0:
                await asyncio.sleep(wait)

    def mark_finished(self) -> None:
        self._last_finished_at = time.monotonic()
