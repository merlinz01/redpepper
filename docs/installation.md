# Installation

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
