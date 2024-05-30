## Installation

To install the Manager, run the following one-liner:

```bash
curl https://raw.githubusercontent.com/merlinz01/redpepper/main/setup/bootstrap-manager.sh |  bash -
```

To install the Agent, run the following one-liner:

```bash
curl https://raw.githubusercontent.com/merlinz01/redpepper/main/setup/bootstrap-agent.sh | bash -
```

You can set up the SmallStep CA for use with RedPepper by running this one-liner after installing the Manager:

```bash
bash /opt/redpepper/setup/smallstep-ca-setup.sh
```

You will have to update the configuration files to suit your application.

## Uninstallation

If you encountered an error during setup want to remove all the files set up by these install scripts, **_including all your configuration files_**, run this one-liner:

```bash
curl https://raw.githubusercontent.com/merlinz01/redpepper/main/setup/uninstall-everything.sh | sudo bash -
```
