import os
import ssl
from pathlib import Path

import pytest
from pydantic import ValidationError

from redpepper.agent.config import AgentConfig
from tests.data import get_data_manager


def test_load_agent_config():
    data_manager = get_data_manager()
    with data_manager.yamlfile("config/agent.yml") as agent_yml:
        agent_yml["agent_id"] = "agent-x"
        agent_yml["include"] = [str(data_manager.path / "config" / "included.yml")]
    with data_manager.yamlfile("config/included.yml") as included_yml:
        included_yml["manager_host"] = "manager.x"
    config = AgentConfig.from_file(str(data_manager.path / "config" / "agent.yml"))
    assert config.agent_id == "agent-x"
    assert config.manager_host == "manager.x"


def test_load_config_with_non_mapping_yaml():
    data_manager = get_data_manager()
    open(data_manager.path / "config" / "agent.yml", "w").write("[]")
    with pytest.raises(ValueError):
        AgentConfig.from_file(str(data_manager.path / "config" / "agent.yml"))


def test_load_config_with_nonexistent_include():
    data_manager = get_data_manager()
    with data_manager.yamlfile("config/agent.yml") as agent_yml:
        agent_yml["include"] = ["/nonexistent.yml"]
    AgentConfig.from_file(str(data_manager.path / "config" / "agent.yml"))


def test_load_tls_context():
    with pytest.raises(ValidationError):
        AgentConfig(tls_cert_file=Path("/nonexistent.pem"))
    with pytest.raises(ValidationError):
        AgentConfig(tls_key_file=Path("/nonexistent.pem"))
    with pytest.raises(ValidationError):
        AgentConfig(tls_ca_file=Path("/nonexistent.pem"))
    config = {
        "tls_cert_file": "config/agent-cert.pem",
        "tls_key_file": "config/agent-key.pem",
        "tls_ca_file": "config/ca-cert.pem",
        "tls_key_password": "",
        "tls_check_hostname": True,
        "tls_verify_mode": "optional",
    }
    os.chmod(config["tls_key_file"], 0o600)
    ctx = AgentConfig(**config).load_tls_context(ssl.Purpose.CLIENT_AUTH)  # type: ignore
    assert ctx.check_hostname
    assert ctx.verify_mode == ssl.CERT_OPTIONAL
    config["tls_verify_mode"] = "required"
    ctx = AgentConfig(**config).load_tls_context(ssl.Purpose.CLIENT_AUTH)  # type: ignore
    assert ctx.verify_mode == ssl.CERT_REQUIRED
    config["tls_check_hostname"] = False
    config["tls_verify_mode"] = "none"
    ctx = AgentConfig(**config).load_tls_context(ssl.Purpose.CLIENT_AUTH)  # type: ignore
    assert not ctx.check_hostname
    assert ctx.verify_mode == ssl.CERT_NONE
    config["tls_verify_mode"] = "invalid"
    with pytest.raises(ValueError):
        AgentConfig(**config).load_tls_context(ssl.Purpose.CLIENT_AUTH)  # type: ignore
    keyfile = get_data_manager().path / "config" / "agent-key.pem"
    keyfile.touch(mode=0o777)
    with pytest.raises(ValueError):
        AgentConfig(tls_key_file=keyfile).load_tls_context(ssl.Purpose.CLIENT_AUTH)  # type: ignore
