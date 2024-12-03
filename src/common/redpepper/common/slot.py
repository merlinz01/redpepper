import trio


class Slot[T]:
    def __init__(self):
        self._value: T
        self._event = trio.Event()

    def is_set(self) -> bool:
        return self._event.is_set()

    async def set(self, value: T) -> None:
        self._value = value
        self._event.set()

    async def get(self, timeout: float | None = None) -> T:
        if self._event.is_set():
            return self._value
        if timeout is None:
            await self._event.wait()
        else:
            with trio.fail_after(timeout):
                await self._event.wait()
        return self._value
