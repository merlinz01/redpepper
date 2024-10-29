import pytest

from redpepper.agent.agent import Agent
from redpepper.manager.manager import Manager


@pytest.mark.fixture_params(agent_id="test_agent_1")
async def test_noop(manager: Manager, agent: Agent):
    command_id = await manager.send_command(agent.config.agent_id, "noop.Noop", (), {})
    if not command_id:
        raise ValueError("Failed to send command")  # pragma: no cover
    result = await manager.await_command_result(command_id, timeout=1)
    assert result.succeeded
