## Installing the Manager

### Basic installation

To install the Manager, run the following command:

```bash
curl https://raw.githubusercontent.com/merlinz01/redpepper/main/setup/bootstrap-manager.sh |  bash -
```

### Install the Smallstep CA for mutual TLS (recommended)

Set up the [Smallstep CA](https://github.com/smallstep/certificates)
for use with RedPepper by running this command after installing the Manager:

> Note: Make sure to enter the correct hostname when asked,
> or agents will not be able to request certificates from the CA.

```bash
sudo bash /opt/redpepper/setup/smallstep-ca-setup.sh
```

### Obtain API + web console certificates

If your Manager server has a public domain name,
use this command to set up the API (and the web console) to use free certificates from LetsEncrypt:

> Note: Make sure to enter the same hostname both when certbot asks for it and when this script asks for it.

```bash
sudo bash /opt/redpepper/setup/setup-certbot-api-keypair.sh
```

Alternatively, generate certificates for the API server
with the Smallstep CA by running this command after setting up the CA:

```bash
sudo bash /opt/redpepper/setup/create-api-keypair-stepca.sh
```

### Generate certificates for agent communication

Generate certificates for agent communication
by running this command after setting up the CA:

```bash
sudo bash /opt/redpepper/setup/create-manager-keypair-stepca.sh
```

## Installing the Agent

### Basic installation

To install the Agent, run the following command:

```bash
curl https://raw.githubusercontent.com/merlinz01/redpepper/main/setup/bootstrap-agent.sh | bash -
```

### Manager communication setup

Run the following command to set up communication and authentication paramenters for an agent:

```bash
sudo bash /opt/redpepper-agent/setup/basic-agent-configuration.sh
```

### Generate certificates

On agent machines, generate certificates for manager communication
by running this command after setting up the CA on the manager machine:

```bash
sudo bash /opt/redpepper-agent/setup/create-agent-keypair-stepca.sh
```

The root certificate fingerprint is displayed by the install script,
and can be viewed by running this command on the manager server:

```
step certificate fingerprint /etc/redpepper-step-ca/certs/root_ca.pem
```

The provisioner password for the CA is at `/etc/redpepper-step-ca/secrets/provisioner-password`.

## Uninstallation

If you ran into trouble during setup and want to remove all the files
set up by any of these install scripts,
**_including deleting all your precious configuration files_**,
run this one-liner:

```bash
curl https://raw.githubusercontent.com/merlinz01/redpepper/main/setup/uninstall-everything.sh | sudo bash -
```
