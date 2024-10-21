import secrets
from typing import Any

from redpepper.manager.config import defaults
from redpepper.manager.manager import Manager

defaults = defaults | {
    "command_log_file": ":memory:",
    "tls_cert_file": "config/manager-cert.pem",
    "tls_key_file": "config/manager-key.pem",
    "tls_ca_file": "config/ca-cert.pem",
    "api_session_secret_key": secrets.token_urlsafe(32),
    "api_tls_cert_file": "config/manager-cert.pem",
    "api_tls_key_file": "config/manager-key.pem",
    "bind_host": "localhost",
    "bind_port": 8080,
}


def setup_manager(config: dict[str, Any] = {}) -> Manager:
    """Setup a Manager instance with the given configuration"""

    config = defaults | config
    manager = Manager(config)
    return manager
