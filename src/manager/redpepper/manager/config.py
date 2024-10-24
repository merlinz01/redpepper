"""RedPepper Manager configuration"""

import pathlib

import pydantic

from redpepper.common.config import BaseConfig, ConnectionConfig, TLSConfig

DEFAULT_CONFIG_FILE = "/etc/redpepper/manager.yml"


class APILogin(pydantic.BaseModel):
    username: str
    password_hash: str
    totp_secret: pydantic.SecretStr | None = None


class APIConfig(pydantic.BaseModel):
    api_bind_host: str = "0.0.0.0"
    api_bind_port: int = 7050
    api_tls_cert_file: pydantic.FilePath = pathlib.Path("/etc/redpepper/api.pem")
    api_tls_key_file: pydantic.FilePath = pathlib.Path("/etc/redpepper/api-key.pem")
    api_tls_key_file_allow_insecure: bool = False
    api_tls_key_password: pydantic.SecretStr | None = None

    api_session_secret_key: pydantic.SecretStr
    api_session_max_age: int = 43200
    api_static_dir: pydantic.DirectoryPath | None = None
    api_logins: list[APILogin] = []

    data_base_dir: pydantic.DirectoryPath


class ManagerConfig(BaseConfig, ConnectionConfig, TLSConfig, APIConfig):
    # Server
    bind_host: str = "0.0.0.0"
    bind_port: int = 7051

    # Data
    data_base_dir: pydantic.DirectoryPath = pathlib.Path("/var/lib/redpepper/data")

    # Command log
    command_log_max_age: int = 2592000
    command_log_purge_interval: int = 86400
    command_log_file: pathlib.Path = pathlib.Path(
        "/var/lib/redpepper-manager/commands.sqlite"
    )
