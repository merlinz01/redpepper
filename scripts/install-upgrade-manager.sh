#!/bin/bash

# Exit on error
set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "This script must be run as root. Exiting."
fi

# Create redpepper user and group
if ! getent group redpepper > /dev/null; then
    groupadd -f redpepper
fi
if ! getent passwd redpepper > /dev/null; then
    useradd -r -s /bin/false -g redpepper -m -d /opt/redpepper redpepper
fi

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
echo "Installing/upgrading the RedPepper Manager..."
uv tool install redpepper-manager --with redpepper-requests | grep -v "already installed" || uv tool upgrade redpepper-manager

# Sanity check
if [ ! -f /opt/redpepper/.local/bin/redpepper-manager ]; then
    echo "Error! RedPepper Manager not found at /opt/redpepper/.local/bin/redpepper-manager. Exiting."
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
if [ ! -f /etc/redpepper/manager.yml ]; then
    echo "Creating the config file..."
    cat << EOF > /etc/redpepper/manager.yml
# RedPepper Agent configuration file
# To view available options, see https://github.com/merlinz01/redpepper/blob/main/src/manager/redpepper/manager.yml

include:
  - /etc/redpepper/manager.d/*.yml
EOF
    chown redpepper:redpepper /etc/redpepper/manager.yml
fi

# Create the config subdirectory
if [ ! -d /etc/redpepper/manager.d ]; then
    echo "Creating the config subdirectory..."
    mkdir /etc/redpepper/manager.d
    chown redpepper:redpepper /etc/redpepper/manager.d
fi

# Generate the API session secret
if [ ! -f /etc/redpepper/manager.d/00-autogenerated-api-session-secret-key.yml ]; then
    echo "Generating the API session secret..."
    echo "api_session_secret_key: \"$(openssl rand -base64 128)\"" > /etc/redpepper/manager.d/00-autogenerated-api-session-secret-key.yml
    chown redpepper:redpepper /etc/redpepper/manager.d/00-autogenerated-api-session-secret-key.yml
fi

# Create the /var/lib directory
if [ ! -d /var/lib/redpepper-manager ]; then
    echo "Creating the /var/lib directory..."
    mkdir /var/lib/redpepper-manager
    chown redpepper:redpepper /var/lib/redpepper-manager
fi

# Create the log directory
if [ ! -d /var/log/redpepper-manager ]; then
    echo "Creating the log directory..."
    mkdir /var/log/redpepper-manager
    chown redpepper:redpepper /var/log/redpepper-manager
fi

# Set up the service
echo "Setting up the service..."
cat << EOF > /etc/systemd/system/redpepper-manager.service
[Unit]
Description=RedPepper Manager
Documentation=https://github.com/merlinz01/redpepper
After=network.target network-online.target
Requires=network-online.target

[Service]
User=redpepper
Group=redpepper
ExecStart=/opt/redpepper/.cargo/bin/uv tool run redpepper-manager --config-file /etc/redpepper/manager.yml
TimeoutStopSec=5s
PrivateTmp=true
Restart=always
StartLimitBurst=3
ProtectSystem=full
ReadWritePaths=/var/lib/redpepper-manager
ReadWritePaths=/var/log/redpepper-manager

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload

# Done
echo
echo -e "\e[32mSetup complete!\e[0m"
echo
echo "You can start the RedPepper Manager service with:"
echo "    sudo systemctl enable redpepper-manager"
echo "    sudo systemctl start redpepper-manager"
echo
echo -e "You may want to run configuration tools using \e[36msudo -u redpepper redpepper-tools\e[0m to configure basic settings."