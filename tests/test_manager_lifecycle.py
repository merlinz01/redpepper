import pytest
import trio

from redpepper.manager.manager import Manager
from tests.manager import setup_manager


@pytest.fixture
async def manager(nursery: trio.Nursery):
    manager = setup_manager()
    nursery.start_soon(manager.run)
    yield manager
    await manager.shutdown()


async def test_start_stop(manager: Manager):
    # If we got here, something must be working
    pass
