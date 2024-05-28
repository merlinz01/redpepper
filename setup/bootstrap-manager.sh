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
    sudo chown -R redpepper:redpepper /opt/redpepper
fi

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

# Fix example TLS key permissions
sudo chmod 600 /opt/redpepper/example/*.pem

# Create the log directory
if [ ! -d /var/log/redpepper ]; then
    sudo mkdir -p /var/log/redpepper
    sudo chown redpepper:redpepper /var/log/redpepper
    sudo chmod 700 /var/log/redpepper
fi

# Create the config directory
if [ ! -d /etc/redpepper ]; then
    sudo mkdir /etc/redpepper
    chown redpepper:redpepper /etc/redpepper
fi
if [ ! -d /etc/redpepper/manager.d ]; then
    sudo mkdir /etc/redpepper/manager.d
    chown redpepper:redpepper /etc/redpepper/manager.d
fi

# Copy the config file
if [ ! -f /etc/redpepper/manager.yml ]; then
    sudo cp /opt/redpepper/redpepper/manager/manager.yml /etc/redpepper/manager.yml
fi

# Create the data directory and files
if [ ! -d /var/lib/redpepper ]; then
    sudo mkdir /var/lib/redpepper
    sudo chown redpepper:redpepper /var/lib/redpepper
    sudo chmod 700 /var/lib/redpepper
fi
if [ ! -f /var/lib/redpepper/agents.yml ]; then
    touch -a /var/lib/redpepper/agents.yml
fi
if [ ! -f /var/lib/redpepper/agents.yml ]; then
    touch -a /var/lib/redpepper/agents.yml
fi
if [ ! -d /var/lib/redpepper/state ]; then
    sudo mkdir /var/lib/redpepper/state
    sudo chown redpepper:redpepper /var/lib/redpepper/state
    sudo chmod 700 /var/lib/redpepper/state
fi
if [ ! -d /var/lib/redpepper/data ]; then
    sudo mkdir /var/lib/redpepper/data
    sudo chown redpepper:redpepper /var/lib/redpepper/data
    sudo chmod 700 /var/lib/redpepper/data
fi
if [ ! -d /var/lib/redpepper/custom-states ]; then
    sudo mkdir /var/lib/redpepper/custom-states
    sudo chown redpepper:redpepper /var/lib/redpepper/custom-states
    sudo chmod 700 /var/lib/redpepper/custom-states
fi


# Set up the service
sudo ln -fs /opt/redpepper/setup/redpepper-manager.service /etc/systemd/system/redpepper-manager.service
sudo systemctl daemon-reload
sudo systemctl enable redpepper-manager