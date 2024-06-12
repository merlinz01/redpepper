from redpepper.manager.manager import AgentConnection
from redpepper.requests import RequestError


def call(conn: AgentConnection, state_name: str | None = None):
    try:
        state = conn.manager.data_manager.get_state_definition_for_agent(
            conn.agent_id, state_name
        )
    except ValueError as e:
        raise RequestError(str(e)) from e
    return state


call.__qualname__ = "request stateDefinition"
