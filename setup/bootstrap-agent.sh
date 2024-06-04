#!/bin/bash

# Exit on error
set -e

# Install sudo if not already installed and if running as root (for freshly installed systems)
if [ "$EUID" -eq 0 ]; then
    if ! command -v sudo > /dev/null; then
        echo "Installing sudo..."
        apt-get update > /dev/null
        apt-get install -y sudo
    fi
fi

# Update and install dependencies
echo "Updating and installing dependencies..."
sudo apt-get update > /dev/null
sudo apt-get install -q -y python3-pip python3-venv python3-wheel git | grep upgraded

# Create redpepper user and group
if ! getent group redpepper-agent > /dev/null; then
    echo "Creating the redpepper-agent group..."
    sudo groupadd -f redpepper-agent
fi
if ! getent passwd redpepper-agent > /dev/null; then
    echo "Creating the redpepper-agent user..."
    sudo useradd -r -s /bin/false -g redpepper-agent -g root -d /opt/redpepper-agent redpepper-agent
fi

# Create the directory
if [ ! -d /opt/redpepper-agent ]; then
    echo "Creating the RedPepper Agent directory..."
    sudo mkdir -p /opt/redpepper-agent
    sudo chown -R redpepper-agent:redpepper-agent /opt/redpepper-agent
fi

# Run the next part of the setup as the redpepper-agent user
sudo -u redpepper-agent /bin/bash << EOF

# Exit on error
set -e

# Clone the repository
echo "Cloning/updating the repository..."
if [ -d /opt/redpepper-agent/.git ]; then
    git -C /opt/redpepper-agent pull
else
    git clone https://github.com/merlinz01/redpepper.git /opt/redpepper-agent
fi

# Install Python dependencies
echo "Installing Python dependencies..."
python3 -m venv /opt/redpepper-agent/.venv
source /opt/redpepper-agent/.venv/bin/activate
pip install -r /opt/redpepper-agent/redpepper/agent/requirements.txt -q

EOF

# Run the next part of the setup as the root user
sudo -u root /bin/bash << EOF

# Exit on error
set -e

# Create the config directory
if [ ! -d /etc/redpepper-agent ]; then
    echo "Creating the config directory..."
    mkdir /etc/redpepper-agent
    chown redpepper-agent:redpepper-agent /etc/redpepper-agent
    chmod 700 /etc/redpepper-agent
fi
if [ ! -d /etc/redpepper-agent/agent.d ]; then
    echo "Creating the agent config directory..."
    mkdir /etc/redpepper-agent/agent.d
    chown redpepper-agent:redpepper-agent /etc/redpepper-agent/agent.d
fi

# Copy the config file
if [ ! -f /etc/redpepper-agent/agent.yml ]; then
    echo "Copying the agent config file..."
    cp /opt/redpepper-agent/redpepper/agent/agent.yml /etc/redpepper-agent/agent.yml
    chown redpepper-agent:redpepper-agent /etc/redpepper-agent/agent.yml
fi

# Create the state cache directory
if [ ! -d /var/lib/redpepper-agent/states ]; then
    echo "Creating the state cache directory..."
    mkdir -p /var/lib/redpepper-agent/states
    chown -R redpepper-agent:redpepper-agent /var/lib/redpepper-agent
    chmod 700 /var/lib/redpepper-agent
fi

# Set up the service
echo "Setting up the service..."
ln -fs /opt/redpepper-agent/setup/redpepper-agent.service /etc/systemd/system/redpepper-agent.service
systemctl daemon-reload
systemctl enable redpepper-agent

EOF

# Done
echo
echo -e "\e[32mSetup complete!\e[0m"
echo
echo "You can now start the RedPepper Agent service with:"
echo "    sudo systemctl start redpepper-agent"
echo
