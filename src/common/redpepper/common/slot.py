import threading
from typing import Any

import trio


class Slot:
    def __init__(self, value: Any = None):
        self.value = value
        self.event = trio.Event()
        self.threading_event = threading.Event()

    async def set(self, value: Any) -> None:
        self.value = value
        self.event.set()
        self.threading_event.set()

    async def get(self, timeout: float | None = None) -> Any:
        if self.event.is_set():
            return self.value
        if timeout is None:
            await self.event.wait()
            return self.value
        with trio.fail_after(timeout):
            await self.event.wait()
        return self.value

    def get_threadsafe(self, timeout: float | None = None) -> Any:
        if not self.threading_event.wait(timeout):
            raise trio.TooSlowError("Timeout awaiting slot value")
        return self.value
