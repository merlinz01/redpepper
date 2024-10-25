import pytest
import trio

from redpepper.manager.manager import Manager
from tests.agent import setup_agent
from tests.data import get_data_manager
from tests.manager import setup_manager


@pytest.fixture
async def manager(nursery: trio.Nursery):
    manager = setup_manager()
    nursery.start_soon(manager.run)
    await manager.running.wait()

    yield manager

    await manager.shutdown()


async def test_start_stop(nursery: trio.Nursery, manager: Manager):
    agent = setup_agent()
    get_data_manager().setup_agent(
        agent.config.agent_id,
        agent.config.agent_secret.get_secret_value(),
        ["127.0.0.1/32", "::1/128"],
    )
    nursery.start_soon(agent.run)
    with trio.fail_after(5):
        await agent.connected.wait()
    await agent.shutdown()
