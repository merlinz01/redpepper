#!/bin/bash

# Exit on error
set -e

# Update and install dependencies
sudo apt-get -q update
sudo apt-get install -q -y python3-pip python3-venv python3-wheel git wget

# Create redpepper user and group
if ! getent group redpepper > /dev/null; then
    sudo groupadd -f redpepper
fi
if ! getent passwd redpepper > /dev/null; then
    sudo useradd -r -s /bin/false -g redpepper -d /opt/redpepper redpepper
fi

# Create the directory
if [ ! -d /opt/redpepper ]; then
    echo "Creating the RedPepper directory..."
    sudo mkdir -p /opt/redpepper
    sudo chown -R redpepper:redpepper /opt/redpepper
fi

# Run the next part of the setup as the redpepper user
sudo -u redpepper /bin/bash << EOF

# Exit on error
set -e

# Clone the repository
echo "Cloning/updating the repository..."
if [ -d /opt/redpepper/.git ]; then
    git -C /opt/redpepper pull
else
    git clone https://github.com/merlinz01/redpepper.git /opt/redpepper
fi

# Install Node.js
if [ ! -d /opt/redpepper/.node ]; then
    echo "Installing Node.js..."
    cd /tmp
    wget -N https://nodejs.org/dist/v20.13.1/node-v20.13.1-linux-x64.tar.xz
    mkdir /opt/redpepper/.node
    tar -xf /tmp/node-v20.13.1-linux-x64.tar.xz -C /opt/redpepper/.node
fi

# Build the console
echo "Building the console..."
cd /opt/redpepper/redpepper_console
export NODE_DIR=/opt/redpepper/.node/node-v20.13.1-linux-x64
PATH=\$NODE_DIR/bin:\$PATH npm install
PATH=\$NODE_DIR/bin:\$PATH npm run build
cd /opt/redpepper

# Install Python dependencies
echo "Installing Python dependencies..."
python3 -m venv /opt/redpepper/.venv
source /opt/redpepper/.venv/bin/activate
pip install -r /opt/redpepper/redpepper/manager/requirements.txt -q

# Fix example TLS key permissions
chmod 600 /opt/redpepper/example/*.pem

EOF

# Run the next part of the setup as the root user
sudo -u root /bin/bash << EOF

# Exit on error
set -e

# Create the log directory
if [ ! -d /var/log/redpepper ]; then
    echo "Creating the log directory..."
    mkdir -p /var/log/redpepper
    chown redpepper:redpepper /var/log/redpepper
    chmod 700 /var/log/redpepper
fi

# Create the config directories
if [ ! -d /etc/redpepper ]; then
    echo "Creating the config directory..."
    mkdir /etc/redpepper
    chown redpepper:redpepper /etc/redpepper
    chmod 700 /etc/redpepper
fi
if [ ! -d /etc/redpepper/manager.d ]; then
    echo "Creating the manager config directory..."
    mkdir /etc/redpepper/manager.d
    chown redpepper:redpepper /etc/redpepper/manager.d
fi

# Copy the config file
if [ ! -f /etc/redpepper/manager.yml ]; then
    echo "Copying the manager config file..."
    cp /opt/redpepper/redpepper/manager/manager.yml /etc/redpepper/manager.yml
    chown redpepper:redpepper /etc/redpepper/manager.yml
fi

# Create the data directory and files
if [ ! -d /var/lib/redpepper ]; then
    echo "Creating the agent config directory..."
    mkdir /var/lib/redpepper
    chown redpepper:redpepper /var/lib/redpepper
    chmod 700 /var/lib/redpepper
fi
if [ ! -f /var/lib/redpepper/agents.yml ]; then
    echo "Creating the agents file..."
    touch -a /var/lib/redpepper/agents.yml
    chown redpepper:redpepper /var/lib/redpepper/agents.yml
fi
if [ ! -f /var/lib/redpepper/groups.yml ]; then
    echo "Creating the groups file..."
    touch -a /var/lib/redpepper/groups.yml
    chown redpepper:redpepper /var/lib/redpepper/groups.yml
fi
if [ ! -d /var/lib/redpepper/state ]; then
    echo "Creating the state directory..."
    mkdir /var/lib/redpepper/state
    chown redpepper:redpepper /var/lib/redpepper/state
    chmod 700 /var/lib/redpepper/state
fi
if [ ! -d /var/lib/redpepper/data ]; then
    echo "Creating the data directory..."
    mkdir /var/lib/redpepper/data
    chown redpepper:redpepper /var/lib/redpepper/data
    chmod 700 /var/lib/redpepper/data
fi
if [ ! -d /var/lib/redpepper/custom-states ]; then
    echo "Creating the custom states directory..."
    mkdir /var/lib/redpepper/custom-states
    chown redpepper:redpepper /var/lib/redpepper/custom-states
    chmod 700 /var/lib/redpepper/custom-states
fi

# Set up the service
echo "Setting up the service..."
ln -fs /opt/redpepper/setup/redpepper-manager.service /etc/systemd/system/redpepper-manager.service
systemctl daemon-reload
systemctl enable redpepper-manager

EOF

# Done
echo
echo -e "\e[32mSetup complete!\e[0m"
echo
echo "You can now start the RedPepper Manager service with:"
echo "    sudo systemctl start redpepper-manager"
echo