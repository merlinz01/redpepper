from typing import Any

from redpepper.agent.agent import Agent
from redpepper.agent.config import AgentConfig

defaults = {
    "tls_cert_file": "config/agent-cert.pem",
    "tls_key_file": "config/agent-key.pem",
    "tls_ca_file": "config/ca-cert.pem",
    "tls_check_hostname": False,
    "manager_host": "localhost",
    "manager_port": 7050,
    "agent_id": "test_agent",
    "agent_secret": "notasecret",
}


def setup_agent(config: dict[str, Any] = {}) -> Agent:
    """Setup a Manager instance with the given configuration"""

    config = defaults | config
    manager = Agent(AgentConfig(**config))
    return manager
