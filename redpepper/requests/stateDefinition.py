from redpepper.manager.manager import AgentConnection


def call(conn: AgentConnection, state_name: str | None = None):
    state = conn.manager.data_manager.get_state_definition_for_agent(
        conn.agent_id, state_name
    )
    return state
