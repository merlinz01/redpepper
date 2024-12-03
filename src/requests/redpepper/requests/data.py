from redpepper.manager.manager import AgentConnection
from redpepper.requests import RequestError


async def call(conn: AgentConnection, name: str):
    assert conn.agent_id
    try:
        return conn.manager.data_manager.get_data_for_agent(conn.agent_id, name)
    except KeyError:
        raise RequestError(f"Data not found: {name}")


call.__qualname__ = "request data"
