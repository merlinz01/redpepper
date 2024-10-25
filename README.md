# RedPepper

[![GitHub license](https://img.shields.io/github/license/merlinz01/redpepper)](LICENSE.txt)
[![GitHub release](https://img.shields.io/github/v/release/merlinz01/redpepper)](https://github.com/merlinz01/redpepper/releases)
[![GitHub issues](https://img.shields.io/github/issues/merlinz01/redpepper)](https://github.com/merlinz01/redpepper/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/merlinz01/redpepper)](https://github.com/merlinz01/redpepper/pulls)
[![GitHub contributors](https://img.shields.io/github/contributors/merlinz01/redpepper)](https://github.com/merlinz01/redpepper/graphs/contributors)
[![Code coverage](https://codecov.io/github/merlinz01/redpepper/graph/badge.svg?token=UB5DDINFJQ)](https://codecov.io/github/merlinz01/redpepper)

![RedPepper logo](redpepper.png)

RedPepper is a state-based configuration management system written in Python.
It has two basic components: a central manager and one or more agents on controlled servers.
Redpepper is used to distribute configuration to servers and ensure that the servers remain in a consistent state.

RedPepper is inspired by [Salt](https://github.com/saltstack/salt) but aims to be more flexible and easy-to-use.

RedPepper has a REST API for integration with tools or user interfaces.
RedPepper comes with an integrated web UI built with [Vue.js](https://vuejs.org) for managing the system.

![Agents view](/console/demo_agents.png)

![Commands view](/console/demo_commands.png)

![Data editor view](/console/demo_dataeditor.png)

> Please note: This project is currently being beta-tested and the bugs are being worked out.
> You can help by testing RedPepper in your own use case and opening issues when you find a flat spot.

## Documentation

See <https://merlinz01.github.io/redpepper>.

## Installation

Installation scripts are provided in the `setup` directory.
See [Installation](docs/installation.md) for installation instructions.

## Usage

RedPepper's user interface is the RedPepper Console, which is installed with the Manager.
See [the documentation for the console](docs/console.md).

## Configuration

See [Configuration](docs/configuration.md) for more info.

### Sample state file

```yaml
Server installed:
  type: package.Installed
  name: nginx

Config file installed:
  type: file.Installed
  source: file-stored-on-manager.conf
  path: /etc/nginx/installed-by-redpepper.conf
  user: nginx
  group: nginx
  mode: 0600
  if:
    - py: not sys.platform.startswith('win')
    - not file exists: /some/other/file

Server running:
  type: service.Running
  name: nginx
  enable: true
  require:
    - Server installed
    - Config file installed
```

## Security

RedPepper aims to be fully secure by default where possible.

See [SECURITY.md](SECURITY.md) and [Security Features](docs/security-features.md) for more info.

## License

RedPepper is licensed under the MIT license.
