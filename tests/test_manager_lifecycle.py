import pytest
import trio

from redpepper.manager.manager import Manager
from tests.agent import setup_agent
from tests.manager import setup_manager


@pytest.fixture
async def manager(nursery: trio.Nursery):
    manager = setup_manager()
    nursery.start_soon(manager.run)
    yield manager
    await manager.shutdown()


async def test_start_stop(nursery: trio.Nursery, manager: Manager):
    agent = setup_agent()
    nursery.start_soon(agent.run)
    while not hasattr(agent, "conn"):
        await trio.sleep(0.01)
    await agent.shutdown()
