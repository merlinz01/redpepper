
![](redpepper.png)

# RedPepper

RedPepper is a state-based configuration management system written in Python.
It has two basic components: a central manager and one or more agents on controlled servers.

RedPepper is primarily focused on Linux-based systems although it probably would be partially functional on other OS's as well.

RedPepper uses Protobuf-encoded messages sent over TLS connections initiated by agents.
With configurable keep-alive pinging, this allows agents behind NAT to function smoothly.

RedPepper is inspired by [Salt](https://github.com/saltstack/salt) but aims to be more reliable and intuitive although it is possibly slightly less scalable.

> Please note: This project is in pre-alpha state! No guarantees of any sort but I would be glad for your help in developing it.

## Installation and Usage

Installation is manual at this point.

I intend to provide a .deb package and/or a Linux installation one-liner once I get this project far enough along.

```bash
git clone https://github.com/merlinz01/redpepper.git
cd redpepper
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### RedPepper Manager
The RedPepper Manager can be started with the following command:

```bash
python -m redpepper.manager --config-file ./example/manager.yml
```

### RedPepper Agent

The RedPepper Agent demo can be started with the following command:

```bash
python -m redpepper.agent --config-file ./example/agent.yml
```

## Configuration
Both the RedPepper Agent and Manager are configured using YAML files. The configuration files allow you to set various parameters such as the manager host and port for the agent, and the bind address and port for the manager.

For more details on the configuration options, refer to the example configuration files: agent.yml and manager.yml.

### State configuration

All state configuration is in YAML files in a (configurable) directory.
See the `example/conf` directory for more examples.

"Data" in this context refers to data stored in YAML files under the `data` directory in the manager's configuration directory.

"State" in this context refers to a set of parameters describing a condition which may or may not be exist on an agent's machine, and parameters describing how to get it into that state.
For example, a `package.Installed` type of state describes a system package that the agent should make sure is installed.

Individual agents are authenticated against the data in `agents.yml`.

Agents are assigned to groups according to the patterns specified in `groups.yml`.

An agent can access states and data for its groups.

Data for a group is defined in a YAML file with the group's name in the `data` directory.
Any data you wish for the agent to be able to access can be defined in these files (passwords etc.).
You can also put files you wish for the agent to access in a subdirectory of `data` with the group's name.

States for a group are defined in a YAML file with the group's name in the `data` directory.
These are YAML mappings with various parameters, most importantly a `type` parameter which specifies the type of state and determines the allowed other parameters.
All states can have a `if` parameter which defines a condition which if false prevents the state from being ensured.

Any state or data defined in any group is overridden by state or data with the same name in subsequently defined groups.


> TODO: I want to keep the builtin state functions minimal and provide a
> framework for retrieving third-party state functions from git repositories
> (inspired by the Go package system).

## Security features

RedPepper aims to be fully secure by default where possible.
You will still have to provide your own TLS key-pairs.
DO NOT use the certificates and keys in the `example` directory in production.
Check out [Smallstep CA](https://github.com/smallstep/certificates) for a recommended certificate management system.

RedPepper errors if the TLS keys provided have insecure permissions.

Agents can only access data and states for the groups to which they belong.

### Authentication

Agents are authenticated by the SHA256 hash of their TLS certificate and the SHA256 hash of a pre-shared secret.
Additionally, agent connections can (and should) be authenticated with MTLS to prevent unauthorized connections.
An allowed IP address range (or ranges) must be specified for each agent which also can be used to increase security.

## License
RedPepper is licensed under the MIT license.