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
sudo apt-get install -q -y python3-pip python3-venv python3-wheel git wget | grep upgraded

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
PATH=\$NODE_DIR/bin:\$PATH npm install > /dev/null
PATH=\$NODE_DIR/bin:\$PATH npm run build > /dev/null
cd /opt/redpepper

# Install Python dependencies
echo "Installing Python dependencies..."
python3 -m venv /opt/redpepper/.venv
source /opt/redpepper/.venv/bin/activate
pip install -r /opt/redpepper/redpepper/manager/requirements.txt -q

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

# Generate the API session secret
if [ ! -f /etc/redpepper/manager.d/00-autogenerated-api-session-secret-key.yml ]; then
    echo "Generating the API session secret..."
    echo "api_session_secret_key: \"\$(openssl rand -base64 128)\"" > /etc/redpepper/manager.d/00-autogenerated-api-session-secret-key.yml
    chown redpepper:redpepper /etc/redpepper/manager.d/00-autogenerated-api-session-secret-key.yml
fi

# Generate a default login
if [ ! -f /etc/redpepper/manager.d/00-autogenerated-default-login.yml ]; then
    echo "Generating the default login..."
    DEFAULT_PASSWORD="\$(openssl rand -hex 32)"
    TOTP_SECRET="\$(openssl rand -hex 16 | base32)"
    cat << EOF1 > /etc/redpepper/manager.d/00-autogenerated-default-login.yml
api_logins:
    - username: "admin"
      password: "\$DEFAULT_PASSWORD"
      totp_secret: "\$TOTP_SECRET"
EOF1
    chown redpepper:redpepper /etc/redpepper/manager.d/00-autogenerated-default-login.yml
    echo
    echo -e "\e[33mThe autogenerated default login is:\e[0m"
    echo -e "    Username: \e[1madmin\e[0m"
    echo -e "    Password: \e[1m\$DEFAULT_PASSWORD\e[0m"
    echo -e "    TOTP Secret: \e[1m\$TOTP_SECRET\e[0m"
    echo -e "This login is configured in \e[1m/etc/redpepper/manager.d/00-autogenerated-default-login.yml\e[0m."
    echo "You should remove that file and configure your own logins in the manager.yml file."
    echo
fi

# Create the data directory and files
if [ ! -d /var/lib/redpepper ]; then
    echo "Creating the data directory..."
    mkdir /var/lib/redpepper
    chown redpepper:redpepper /var/lib/redpepper
    chmod 700 /var/lib/redpepper
fi
if [ ! -d /var/lib/redpepper/data ]; then
    echo "Creating the config data directory..."
    mkdir /var/lib/redpepper/data
    chown redpepper:redpepper /var/lib/redpepper/data
    chmod 700 /var/lib/redpepper/data
fi
if [ ! -f /var/lib/redpepper/data/agents.yml ]; then
    echo "Creating the agents file..."
    touch -a /var/lib/redpepper/data/agents.yml
    chown redpepper:redpepper /var/lib/redpepper/data/agents.yml
fi
if [ ! -f /var/lib/redpepper/data/groups.yml ]; then
    echo "Creating the groups file..."
    touch -a /var/lib/redpepper/data/groups.yml
    chown redpepper:redpepper /var/lib/redpepper/data/groups.yml
fi
if [ ! -d /var/lib/redpepper/data/state ]; then
    echo "Creating the state directory..."
    mkdir /var/lib/redpepper/data/state
    chown redpepper:redpepper /var/lib/redpepper/data/state
    chmod 700 /var/lib/redpepper/data/state
fi
if [ ! -d /var/lib/redpepper/data/data ]; then
    echo "Creating the data directory..."
    mkdir /var/lib/redpepper/data/data
    chown redpepper:redpepper /var/lib/redpepper/data/data
    chmod 700 /var/lib/redpepper/data/data
fi
if [ ! -d /var/lib/redpepper/data/operations ]; then
    echo "Creating the custom operations modules directory..."
    mkdir /var/lib/redpepper/data/operations
    chown redpepper:redpepper /var/lib/redpepper/data/operations
    chmod 700 /var/lib/redpepper/data/operations
fi
if [ ! -d /var/lib/redpepper/data/requests ]; then
    echo "Creating the requests directory..."
    mkdir /var/lib/redpepper/data/requests
    chown redpepper:redpepper /var/lib/redpepper/data/requests
    chmod 700 /var/lib/redpepper/data/requests
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