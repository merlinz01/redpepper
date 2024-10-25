import secrets
from typing import Any

from redpepper.manager.config import ManagerConfig
from redpepper.manager.manager import Manager

from .data import get_data_manager

defaults = {
    "command_log_file": "config/commands.sqlite",
    "tls_cert_file": "config/manager-cert.pem",
    "tls_key_file": "config/manager-key.pem",
    "tls_key_file_allow_insecure": True,
    "tls_ca_file": "config/ca-cert.pem",
    "tls_check_hostname": False,
    "api_session_secret_key": secrets.token_urlsafe(32),
    "api_tls_cert_file": "config/manager-cert.pem",
    "api_tls_key_file": "config/manager-key.pem",
    "api_tls_key_file_allow_insecure": True,
    "bind_host": "localhost",
    "bind_port": 7051,
    "data_base_dir": get_data_manager().data_dir,
}


def setup_manager(config: dict[str, Any] = {}) -> Manager:
    """Setup a Manager instance with the given configuration"""

    config = defaults | config
    manager = Manager(ManagerConfig(**config))
    return manager
    return manager
