#!/bin/bash

# Exit on error
set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "This script must be run as root. Exiting."
fi

# Create redpepper user and group and home directory
if ! getent group redpepper > /dev/null; then
    groupadd -f redpepper
fi
if ! getent passwd redpepper > /dev/null; then
    useradd -r -s /bin/false -g redpepper -m -d /opt/redpepper redpepper
fi
if [ ! -d /opt/redpepper ]; then
    mkdir /opt/redpepper
    chown redpepper:redpepper /opt/redpepper
fi

cd /opt/redpepper

# Run the next part of the script as the redpepper user
sudo -u redpepper bash << SCRIPTEOF
set -e

# Install uv
if [ ! -f /opt/redpepper/.cargo/bin/uv ]; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Sanity check to make sure uv is installed as we expect
if [ ! -f /opt/redpepper/.cargo/bin/uv ]; then
    echo "Error! uv not found at /opt/redpepper/.cargo/bin/uv. Exiting."
    exit 1
fi

# Add uv to path
source /opt/redpepper/.cargo/env

# Install Python
uv python install 3.12

# Install/upgrade the agent via uv
echo "Installing/upgrading the RedPepper Agent..."
uv tool install redpepper-agent --with redpepper-operations | grep -v "already installed" || uv tool upgrade redpepper-agent

# Sanity check
if [ ! -f /opt/redpepper/.local/bin/redpepper-agent ]; then
    echo "Error! RedPepper Agent not found at /opt/redpepper/.local/bin/redpepper-agent. Exiting."
    exit 1
fi

# Install/upgrade the tools via uv
echo "Installing/upgrading the RedPepper tools..."
uv tool install redpepper-tools | grep -v "already installed" || uv tool upgrade redpepper-tools

SCRIPTEOF

# Set the umask to keep files and directories secure
umask 077

# Create the config directory
if [ ! -d /etc/redpepper ]; then
    echo "Creating the config directory..."
    mkdir /etc/redpepper
    chown redpepper:redpepper /etc/redpepper
fi

# Create the config file
if [ ! -f /etc/redpepper/agent.yml ]; then
    echo "Creating the config file..."
    cat << EOF > /etc/redpepper/agent.yml
# RedPepper Agent configuration file
# To view available options, see https://github.com/merlinz01/redpepper/blob/main/src/agent/redpepper/agent.yml

include:
  - /etc/redpepper/agent.d/*.yml
EOF
    chown redpepper:redpepper /etc/redpepper/agent.yml
fi

# Create the config subdirectory
if [ ! -d /etc/redpepper/agent.d ]; then
    echo "Creating the config subdirectory..."
    mkdir /etc/redpepper/agent.d
    chown redpepper:redpepper /etc/redpepper/agent.d
fi

# Create the /var/lib directory
if [ ! -d /var/lib/redpepper-agent ]; then
    echo "Creating the /var/lib directory..."
    mkdir /var/lib/redpepper-agent
    chown redpepper:redpepper /var/lib/redpepper-agent
fi

# Create the log directory
if [ ! -d /var/log/redpepper-agent ]; then
    echo "Creating the log directory..."
    mkdir /var/log/redpepper-agent
    chown redpepper:redpepper /var/log/redpepper-agent
fi

# Set up the service
echo "Setting up the service..."
cat << EOF > /etc/systemd/system/redpepper-agent.service
[Unit]
Description=RedPepper Agent
Documentation=https://github.com/merlinz01/redpepper
After=network.target network-online.target
Requires=network-online.target

[Service]
User=root
Group=root
ExecStart=/opt/redpepper/.cargo/bin/uv tool run redpepper-agent --config-file /etc/redpepper/agent.yml
TimeoutStopSec=5s
PrivateTmp=true
Restart=always
StartLimitBurst=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload

# Done
echo
echo -e "\e[32mSetup complete!\e[0m"
echo
echo "You can start the RedPepper Agent service with:"
echo "    sudo systemctl enable redpepper-agent"
echo "    sudo systemctl start redpepper-agent"
echo
echo -e "You may want to run configuration tools using \e[36msudo -u redpepper redpepper-tools\e[0m to configure basic settings."