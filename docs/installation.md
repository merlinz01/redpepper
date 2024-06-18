## Installing the Manager

To install the Manager, run the following command:

```bash
curl https://raw.githubusercontent.com/merlinz01/redpepper/main/setup/bootstrap-manager.sh |  bash -
```

You can set up the Smallstep CA for use with RedPepper by running this command after installing the Manager:

```bash
sudo bash /opt/redpepper/setup/smallstep-ca-setup.sh
```

If your Manager server has a public domain name, you can use this command to set up the API server to use free certificates from LetsEncrypt:

```bash
sudo bash /opt/redpepper/setup/setup-certbot-api-keypair.sh
```


Alternatively, you can generate certificates for the API server with the Smallstep CA by running this command after setting up the CA:

```bash
sudo bash /opt/redpepper/setup/create-api-keypair-stepca.sh
```

You can generate certificates for agent communication with the Smallstep CA by running this command after setting up the CA:

```bash
sudo bash /opt/redpepper/setup/create-manager-keypair-stepca.sh
```

## Installing the Agent

To install the Agent, run the following command:

```bash
curl https://raw.githubusercontent.com/merlinz01/redpepper/main/setup/bootstrap-agent.sh | bash -
```

On agent machines, you can generate certificates for manager communication with the Smallstep CA by running this command after setting up the CA on the manager machine:

```bash
sudo bash /opt/redpepper-agent/setup/create-agent-keypair-stepca.sh
```

You can run the following command to set up communication and authentication paramenters for an agent:

```bash
sudo bash /opt/redpepper-agent/setup/basic-agent-configuration.sh
```

## Uninstallation

If you ran into trouble during setup and want to remove all the files set up by any of these install scripts, **_including deleting all your precious configuration files_**, run this one-liner:

```bash
curl https://raw.githubusercontent.com/merlinz01/redpepper/main/setup/uninstall-everything.sh | sudo bash -
```
