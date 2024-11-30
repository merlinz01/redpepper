# Installation

This document describes how to install RedPepper Manager and Agent on Linux.
If you want to use RedPepper on other platforms, you will have to install and configure it manually.

## Installing the Manager

### Basic installation

To install the Manager, run the following command:

```bash
curl https://raw.githubusercontent.com/merlinz01/redpepper/refs/heads/main/scripts/install-upgrade-manager.sh | sudo bash
```

### Install the Smallstep CA for mutual TLS (recommended)

Set up the [Smallstep CA](https://github.com/smallstep/certificates)
for use with RedPepper by running this command after installing the Manager:

> Note: Make sure to use the correct hostname for the CA server,
> or agents will not be able to request certificates from the CA.

```bash
sudo -u redpepper /opt/redpepper/.local/bin/redpepper-tools install-step-ca
sudo -u redpepper /opt/redpepper/.local/bin/redpepper-tools setup-step-ca
```

### Obtain API server certificates

If your Manager server has a public domain name,
you can use free certificates from LetsEncrypt for the API server and web console.

Alternatively, generate certificates for the API server
with the Smallstep CA by running this command after setting up the CA:

```bash
sudo -u redpepper /opt/redpepper/.local/bin/redpepper-tools install-step-keypair-manager-api
```

### Generate certificates for agent communication

Generate certificates for agent communication
by running this command after setting up the CA:

```bash
sudo -u redpepper /opt/redpepper/.local/bin/redpepper-tools install-step-keypair-manager
```

### Install the RedPepper Console

To install the RedPepper Console, run the following command:

```bash
sudo -u redpepper /opt/redpepper/.local/bin/redpepper-tools install-console
```

## Installing the Agent

### Basic installation

To install the Agent, run the following command:

```bash
curl https://raw.githubusercontent.com/merlinz01/redpepper/refs/heads/main/scripts/install-upgrade-agent.sh | sudo bash
```

### Manager communication setup

Run the following command to set up communication and authentication paramenters for an agent:

```bash
sudo -u redpepper /opt/redpepper/.local/bin/redpepper-tools basic-agent-config
```

### Generate certificates

On agent machines, generate certificates for manager communication
by running this command after setting up the CA on the manager machine:

```bash
sudo -u redpepper /opt/redpepper/.local/bin/redpepper-tools install-step-keypair-agent
```

## Upgrades

To upgrade the Manager, run the following command:

```bash
sudo -u redpepper /opt/redpepper/.local/bin/uv tool upgrade redpepper-manager
```

To upgrade the Agent, run the following command:

```bash
sudo -u redpepper /opt/redpepper/.local/bin/uv tool upgrade redpepper-agent
```

For both the Manager and Agent, you should also upgrade the tools package as well:

```bash
sudo -u redpepper /opt/redpepper/.local/bin/uv tool upgrade redpepper-tools
```

## Uninstall

To uninstall everything, stop the services and delete the following files and directories:

```bash
/opt/redpepper
/etc/redpepper
/var/lib/redpepper
/var/log/redpepper
/etc/systemd/system/redpepper-*.service
```
