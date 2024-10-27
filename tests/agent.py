from typing import Any

import pytest
import trio

from redpepper.agent.agent import Agent
from redpepper.agent.config import AgentConfig
from redpepper.manager.manager import Manager
from tests.data import get_data_manager

defaults = {
    "tls_cert_file": "config/agent-cert.pem",
    "tls_key_file": "config/agent-key.pem",
    "tls_key_file_allow_insecure": True,
    "tls_ca_file": "config/ca-cert.pem",
    "tls_check_hostname": False,
    "manager_host": "localhost",
    "manager_port": 7051,
    "agent_id": "test_agent",
    "agent_secret": "notasecret",
}


def setup_agent(config: dict[str, Any] = {}) -> Agent:
    """Setup an Agent instance with the given configuration"""

    config = defaults | config
    agent = Agent(AgentConfig(**config))
    return agent


@pytest.fixture
async def agent(nursery: trio.Nursery, manager: Manager):
    agent = setup_agent({"agent_id": "test_agent_1"})
    get_data_manager().setup_agent(
        agent.config.agent_id,
        agent.config.agent_secret.get_secret_value(),
    )
    nursery.start_soon(agent.run)
    with trio.fail_after(5):
        await agent.connected.wait()
    yield agent
    await agent.shutdown()


@pytest.fixture
async def agent2(nursery: trio.Nursery, manager: Manager):
    agent = setup_agent({"agent_id": "test_agent_2"})
    get_data_manager().setup_agent(
        agent.config.agent_id,
        agent.config.agent_secret.get_secret_value(),
    )
    nursery.start_soon(agent.run)
    with trio.fail_after(5):
        await agent.connected.wait()
    yield agent
    await agent.shutdown()
