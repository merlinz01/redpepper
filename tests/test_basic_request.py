from redpepper.agent.agent import Agent
from redpepper.manager.manager import Manager


async def test_command(manager: Manager, agent: Agent):
    command_id = await manager.send_command(agent.config.agent_id, "noop.Noop", (), {})
    if not command_id:
        raise ValueError("Failed to send command")
    result = await manager.await_command_result(command_id, timeout=1)
    assert result.succeeded
