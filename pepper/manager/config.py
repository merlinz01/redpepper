"""Pepper Manager configuration"""

import glob

import yaml

DEFAULT_CONFIG_FILE = "/etc/pepper/manager.yml"

defaults = {
    "bind_address": "0.0.0.0",
    "bind_port": 7051,
    "data_base_dir": "/var/lib/pepper",
    "include": ["/etc/pepper/manager.d/*.yml"],
    "ping_frequency": 30,
    "ping_timeout": 5,
    "tls_cert_file": "/etc/pepper/manager-cert.pem",
    "tls_check_hostname": False,
    "tls_key_file": "/etc/pepper/manager-key.pem",
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
