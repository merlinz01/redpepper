import threading

import trio


class Slot:
    def __init__(self, value=None, type=None):
        self.value = value
        self.event = trio.Event()
        self.threading_event = threading.Event()

    async def set(self, value):
        self.value = value
        self.event.set()
        self.threading_event.set()

    async def get(self, timeout=None):
        if self.event.is_set():
            return self.value
        if timeout is None:
            await self.event.wait()
            return self.value
        with trio.fail_after(timeout):
            await self.event.wait()
        return self.value

    def get_threadsafe(self, timeout=None):
        if not self.threading_event.wait(timeout):
            raise trio.TooSlowError("Timeout awaiting slot value")
        return self.value
