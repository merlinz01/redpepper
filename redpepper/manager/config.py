"""RedPepper Manager configuration"""

import glob

import yaml

DEFAULT_CONFIG_FILE = "/etc/redpepper/manager.yml"

defaults = {
    "api_bind_host": "0.0.0.0",
    "api_bind_port": 7050,
    "api_logins": [],
    "api_session_secret_key": None,
    "api_session_max_age": 3600,
    "api_static_dir": "/usr/share/redpepper/static",
    "api_tls_cert_file": "/etc/redpepper/api-cert.pem",
    "api_tls_key_file": "/etc/redpepper/api-key.pem",
    "api_tls_key_password": None,
    "bind_host": "0.0.0.0",
    "bind_port": 7051,
    "data_base_dir": "/var/lib/redpepper",
    "event_log_max_age": 2592000,
    "event_log_file": "/var/log/redpepper/events.sqlite",
    "include": ["/etc/redpepper/manager.d/*.yml"],
    "ping_frequency": 30,
    "ping_timeout": 5,
    "tls_ca_file": None,
    "tls_ca_path": None,
    "tls_ca_data": None,
    "tls_cert_file": "/etc/redpepper/manager-cert.pem",
    "tls_check_hostname": False,
    "tls_key_file": "/etc/redpepper/manager-key.pem",
    "tls_key_password": None,
    "tls_verify_mode": "none",
}


def load_manager_config(config_file=None):
    if config_file is None:
        config_file = DEFAULT_CONFIG_FILE
    conf = defaults.copy()
    with open(config_file, "r") as stream:
        yml = yaml.safe_load(stream)
    conf.update(yml)
    process_includes(conf, [config_file])
    return conf


def process_includes(conf, included_files):
    if "include" not in conf:
        return
    for pattern in conf["include"]:
        for filename in glob.glob(pattern):
            if filename in included_files:
                continue
            included_files.append(filename)
            with open(filename, "r") as stream:
                included_yml = yaml.safe_load(stream)
            conf.update(included_yml)
            process_includes(included_yml, included_files)
