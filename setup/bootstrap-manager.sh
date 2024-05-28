#!/bin/bash

# Exit on error
set -e

# Update and install dependencies
sudo apt-get -q update
sudo apt-get install -q -y python3-pip python3-venv python3-wheel git wget

# Create redpepper user and group
sudo groupadd -f redpepper
if ! getent passwd redpepper > /dev/null; then
    sudo useradd -r -s /bin/false -g redpepper -d /opt/redpepper redpepper
fi

# Create the directory
if [ ! -d /opt/redpepper ]; then
    sudo mkdir -p /opt/redpepper
fi
sudo chown -R redpepper:redpepper /opt/redpepper

# Clone the repository
if [ -d /opt/redpepper/.git ]; then
    sudo --user=redpepper git -C /opt/redpepper pull
else
    sudo --user=redpepper git clone https://github.com/merlinz01/redpepper.git /opt/redpepper
fi

# Install Node.js
if [ ! -d /opt/redpepper/.node ]; then
    sudo --user=redpepper bash -c "cd /tmp && wget -N https://nodejs.org/dist/v20.13.1/node-v20.13.1-linux-x64.tar.xz"
    sudo --user=redpepper mkdir /opt/redpepper/.node
    sudo --user=redpepper tar -xf /tmp/node-v20.13.1-linux-x64.tar.xz -C /opt/redpepper/.node
fi

# Build the console
cd /opt/redpepper/redpepper_console
export NODE_DIR=/opt/redpepper/.node/node-v20.13.1-linux-x64
sudo --user=redpepper bash -c "PATH=$NODE_DIR/bin:$PATH npm install"
sudo --user=redpepper bash -c "PATH=$NODE_DIR/bin:$PATH npm run build"
cd /opt/redpepper

# Install Python dependencies
sudo --user=redpepper python3 -m venv /opt/redpepper/.venv
sudo --user=redpepper /opt/redpepper/.venv/bin/pip install -r /opt/redpepper/redpepper/manager/requirements.txt -q

# Set up the service
sudo ln -fs /opt/redpepper/setup/redpepper-manager.service /etc/systemd/system/redpepper-manager.service
sudo systemctl daemon-reload
sudo systemctl enable redpepper-manager

# Fix example TLS key permissions
sudo chmod 600 /opt/redpepper/example/*.pem