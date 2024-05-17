
![](redpepper.png)

# RedPepper

RedPepper is a state-based configuration management system written in Python.
It has two basic components: a central manager and one or more agents on controlled servers.
Redpepper is used to distribute configuration to servers and ensure that the servers remain in a consistent state.

RedPepper is primarily targeted for Linux-based systems although it could be partially functional on other OS's as well.

RedPepper is inspired by [Salt](https://github.com/saltstack/salt) but aims to be more reliable and intuitive although it is possibly slightly less scalable.

> Please note: This project is in pre-alpha state! No guarantees of any sort but I would be glad for your help in developing it.

## Documentation

See [here](docs/index.md) for documentation.

## Installation

> Installation is manual at this point.

See [Installation](docs/installation.md) for installation instructions.

## Usage

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

See [Configuration](docs/configuration.md) for more info.

## Security

RedPepper aims to be fully secure by default where possible.

See [SECURITY.md](SECURITY.md) and [Security Features](docs/security-features.md) for more info.

## License
RedPepper is licensed under the MIT license.