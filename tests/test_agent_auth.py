import pytest
import trio

from redpepper.common.errors import AuthenticationError
from redpepper.manager.manager import Manager
from tests.agent import setup_agent
from tests.data import get_data_manager


async def test_agent_auth_failed_unknown_agent_id(
    nursery: trio.Nursery, manager: Manager
):
    with get_data_manager().yamlfile("agents.yml") as agents:
        agents.clear()
    agent = setup_agent({"agent_id": "nonexistent_agent_id"})
    with pytest.raises(AuthenticationError, match="authentication failed"):
        await agent.run()


async def test_agent_auth_failed_wrong_secret(nursery: trio.Nursery, manager: Manager):
    get_data_manager().setup_agent("test_agent", "correct_secret")
    agent = setup_agent({"agent_id": "test_agent", "agent_secret": "wrong_secret"})
    with pytest.raises(AuthenticationError, match="authentication failed"):
        await agent.run()


async def test_agent_auth_failed_non_allowed_ip(
    nursery: trio.Nursery, manager: Manager
):
    get_data_manager().setup_agent(
        "test_agent", "correct_secret", ["127.0.0.2/32", "::2/128"]
    )
    agent = setup_agent({"agent_id": "test_agent"})
    with pytest.raises(AuthenticationError, match="authentication failed"):
        await agent.run()


async def test_agent_auth_succeeds(nursery: trio.Nursery, manager: Manager):
    get_data_manager().setup_agent("test_agent", "correct_secret")
    agent = setup_agent({"agent_id": "test_agent", "agent_secret": "correct_secret"})
    nursery.start_soon(agent.run)
    await agent.connected.wait()
    await agent.shutdown()
