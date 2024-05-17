
# RedPepper

RedPepper is a state-based configuration management system written in Python.
It has two basic components: a central manager and one or more agents on controlled servers.

RedPepper is primarily focused on Linux-based systems although it probably would be partially functional on other OS's as well.

RedPepper uses Protobuf-encoded messages sent over TLS connections initiated by agents.
With configurable keep-alive pinging, this allows agents behind NAT to function smoothly.

RedPepper is inspired by [Salt](https://github.com/saltstack/salt) but aims to be more reliable and intuitive although it is possibly slightly less scalable.

> Please note: This project is in pre-alpha state! No guarantees of any sort but I would be glad for your help in developing it.

## Installation

Installation is manual at this point. Python dependencies are in `requirements.txt`.

I intend to provide a .deb package and/or a Linux installation one-liner once I get this project far enough along.

## Usage
### RedPepper Agent

The RedPepper Agent can be started with the following command:

```
python -m redpepper.agent
```

### RedPepper Manager
The RedPepper Manager can be started with the following command:

```
python -m redpepper.manager
```

## Configuration
Both the RedPepper Agent and Manager are configured using YAML files. The configuration files allow you to set various parameters such as the manager host and port for the agent, and the bind address and port for the manager.

For more details on the configuration options, refer to the example configuration files: agent.yml and manager.yml.

### State configuration

All state configuration is in YAML files in a (configurable) directory.
See the example files for more info.

> TODO: I want to keep the builtin state functions minimal and provide a
> framework for retrieving third-party state functions from git repositories
> (inspired by the Go package system).

## Security features

RedPepper errors if the TLS keys specified have insecure permissions.

### Authentication

Agents are authenticated by the SHA256 hash of their TLS certificate and a pre-shared secret.
Additionally, agent connections can (and should) be authenticated with MTLS to prevent unauthorized connections.
An IP address range must be specified for each agent which also can be used to increase security.

## License
RedPepper is licensed under the MIT license.