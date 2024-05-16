
# Pepper

Pepper is a state-based configuration management system written in Python.
It has two basic components: a central manager and one or more agents on controlled servers.

Pepper is primarily focused on Linux-based systems although it probably would be partially functional on other OS's as well.

Pepper uses Protobuf-encoded messages sent over TLS connections initiated by agents.
With configurable keep-alive pinging, this allows agents behind NAT to function smoothly.

Pepper is inspired by [Salt](https://github.com/saltstack/salt) but aims to be more reliable and intuitive although it is possibly slightly less scalable.

> Please note: This project is in pre-alpha state!

> Please note: I don't have TLS implemented yet! For now the data travels on UNENCRYPTED connections. No security claims whatsoever! (for now)


## Installation

Installation is manual at this point. Python dependencies are in `requirements.txt`.

I intend to provide a .deb package and/or a Linux installation one-liner once I get this project far enough along.

## Usage
### Pepper Agent

The Pepper Agent can be started with the following command:

```
python -m pepper.agent
```

### Pepper Manager
The Pepper Manager can be started with the following command:

```
python -m pepper.manager
```

## Configuration
Both the Pepper Agent and Manager are configured using YAML files. The configuration files allow you to set various parameters such as the manager host and port for the agent, and the bind address and port for the manager.

For more details on the configuration options, refer to the example configuration files: agent.yml and manager.yml.

### State configuration

All state configuration is in YAML files in a (configurable) directory.
See the example files for more info.

> Goal: I want to keep the builtin state functions minimal and provide a
> framework for retrieving third-party state functions from git repositories
> (inspired by the Go package system).

## Authentication

> Please note: No authentication system is implemented yet.
> Any agent can claim to be WHATEVER server it likes and get access to associated data AND SECRETS. Again, no security claims whatsoever! (for now)

> I like Salt's system of key fingerprints being accepted/rejected.
> I intend to do something similar.

## License
Pepper is licensed under the MIT license.