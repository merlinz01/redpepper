import glob
import os
import ssl
from typing import Any, Self

import pydantic
import yaml


def load_config_from_file(
    config_file: str, overrides: dict[str, Any]
) -> dict[str, Any]:
    conf = {}
    process_single_file(config_file, conf)
    process_includes(conf, [config_file])
    conf.update(overrides)
    return conf


def process_single_file(config_file: str, conf: dict[str, Any]) -> None:
    with open(config_file, "r") as stream:
        yml = yaml.safe_load(stream)
    if yml is not None:
        if not isinstance(yml, dict):
            raise ValueError(f"The YAML file {config_file} is not a mapping")
        conf.update(yml)


def process_includes(conf: dict[str, Any], included_files: list[str]) -> None:
    if "include" not in conf:
        return
    for pattern in conf.pop("include"):
        for filename in glob.glob(pattern):
            if filename in included_files:
                continue  # pragma: no cover
            included_files.append(filename)
            process_single_file(filename, conf)
            process_includes(conf, included_files)


class BaseConfig(pydantic.BaseModel):
    model_config = {
        "extra": "forbid",
        "frozen": True,
    }

    @classmethod
    def from_file(
        cls, config_file: str, overrides: dict[str, Any] | None = None
    ) -> Self:
        conf = load_config_from_file(config_file, overrides or {})
        return cls(**conf)


class ConnectionConfig(pydantic.BaseModel):
    ping_timeout: int = 5
    ping_interval: int = 30
    max_message_size: int = 1024 * 1024


class TLSConfig(pydantic.BaseModel):
    tls_cert_file: pydantic.FilePath
    tls_key_file: pydantic.FilePath
    tls_key_file_allow_insecure: bool = False
    tls_key_password: pydantic.SecretStr | None = None
    tls_check_hostname: bool = True
    tls_verify_mode: str = "required"

    tls_ca_file: pydantic.FilePath | None = None
    tls_ca_path: pydantic.DirectoryPath | None = None
    tls_ca_data: str | None = None

    def load_tls_context(self, purpose: ssl.Purpose) -> ssl.SSLContext:
        if (
            self.tls_key_file
            and not self.tls_key_file_allow_insecure
            and os.stat(self.tls_key_file).st_mode & 0o77 != 0
        ):
            raise ValueError(
                "TLS key file %s is insecure, please set permissions to 600"
                % self.tls_key_file,
            )
        ctx = ssl.create_default_context(purpose)
        if self.tls_cert_file:
            ctx.load_cert_chain(
                self.tls_cert_file,
                keyfile=self.tls_key_file,
                password=self.tls_key_password.get_secret_value()
                if self.tls_key_password
                else None,
            )
        ctx.check_hostname = self.tls_check_hostname
        match self.tls_verify_mode:
            case "none":
                ctx.verify_mode = ssl.CERT_NONE
            case "optional":
                ctx.verify_mode = ssl.CERT_OPTIONAL
            case "required":
                ctx.verify_mode = ssl.CERT_REQUIRED
            case _:
                raise ValueError("Unknown TLS verify mode: %s" % self)
        if self.tls_ca_file or self.tls_ca_path or self.tls_ca_data:
            ctx.load_verify_locations(
                cafile=self.tls_ca_file,
                capath=self.tls_ca_path,
                cadata=self.tls_ca_data,
            )
        return ctx
