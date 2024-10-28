import pytest
import trio
from trio.testing import MockClock

from redpepper.common.slot import Slot


async def test_slot():
    slot = Slot()
    assert not slot.is_set()
    await slot.set(42)
    assert slot.is_set()
    assert await slot.get() == 42
    assert await slot.get() == 42


def test_slot_timeout():
    async def run():
        async with trio.open_nursery() as nursery:
            slot = Slot()

            async def setit():
                await trio.sleep(6)
                await slot.set(42)

            nursery.start_soon(setit)
            assert not slot.is_set()
            with pytest.raises(trio.TooSlowError):
                await slot.get(timeout=5)
            assert not slot.is_set()
            await trio.sleep(2)
            assert slot.is_set()
            assert await slot.get() == 42

            slot = Slot()
            nursery.start_soon(setit)
            assert not slot.is_set()
            assert await slot.get() == 42

    trio.run(run, clock=MockClock(autojump_threshold=0.01))
