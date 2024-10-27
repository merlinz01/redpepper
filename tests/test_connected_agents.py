from redpepper.agent.agent import Agent
from redpepper.manager.manager import Manager


async def test_no_agents_present(manager: Manager):
    assert manager.connected_agents() == []


async def test_one_agent_present(manager: Manager, agent: Agent):
    assert manager.connected_agents() == [agent.config.agent_id]


async def test_two_agents_present(manager: Manager, agent: Agent, agent2: Agent):
    assert manager.connected_agents() == [agent.config.agent_id, agent2.config.agent_id]
