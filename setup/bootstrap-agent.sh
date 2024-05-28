#!/bin/bash

# Exit on error
set -e

# Update and install dependencies
sudo apt-get -q update
sudo apt-get install -q -y python3-pip python3-venv python3-wheel git

# Create redpepper user and group
sudo groupadd -f redpepper-agent
if ! getent passwd redpepper-agent > /dev/null; then
    sudo useradd -r -s /bin/false -g redpepper-agent -g root -d /opt/redpepper-agent redpepper-agent
fi

# Create the directory
if [ ! -d /opt/redpepper-agent ]; then
    sudo mkdir -p /opt/redpepper-agent
fi
sudo chown -R redpepper-agent:redpepper-agent /opt/redpepper-agent

# Clone the repository
if [ -d /opt/redpepper-agent/.git ]; then
    sudo --user=redpepper-agent git -C /opt/redpepper-agent pull
else
    sudo --user=redpepper-agent git clone https://github.com/merlinz01/redpepper.git /opt/redpepper-agent
fi

# Install Python dependencies
sudo --user=redpepper-agent python3 -m venv /opt/redpepper-agent/.venv
sudo --user=redpepper-agent /opt/redpepper-agent/.venv/bin/pip install -r /opt/redpepper-agent/redpepper/agent/requirements.txt -q

# Set up the service
sudo ln -fs /opt/redpepper/setup/redpepper-agent.service /etc/systemd/system/redpepper-agent.service
sudo systemctl daemon-reload
sudo systemctl enable redpepper-agent

# Fix example TLS key permissions
sudo chmod 600 /opt/redpepper-agent/example/*.pem
