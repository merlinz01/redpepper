
# Exit on error
set -e

# Make sure RedPepper Manager is installed
if [ ! -d /opt/redpepper ]; then
    echo -e "\e[0;33mThe RedPepper Manager is not installed. Please run the bootstrap-manager.sh script first.\e[0m"
    exit
fi

# Install the required packages
echo "Installing the required packages..."
sudo apt-get update
sudo apt-get install -y wget jq

# Install the Smallstep CA
if [ ! -f /usr/bin/step-ca ]; then
    echo "Downloading and installing the Smallstep CA..."
    cd /tmp
    wget -N https://dl.smallstep.com/gh-release/certificates/gh-release-header/v0.26.1/step-ca_0.26.1_amd64.deb -q
    sudo dpkg -i step-ca_0.26.1_amd64.deb
fi

# Install the Smallstep CLI
if [ ! -f /usr/bin/step ]; then
    echo "Downloading and installing the Smallstep CLI..."
    cd /tmp
    wget -N https://dl.smallstep.com/gh-release/cli/gh-release-header/v0.26.1/step-cli_0.26.1_amd64.deb -q
    sudo dpkg -i step-cli_0.26.1_amd64.deb
fi

# Create the step-ca user and group
if [ ! $(getent passwd step-ca) ]; then
    echo "Creating the step-ca user..."
    sudo useradd -r -s /bin/false step-ca -d /etc/step-ca
fi
if [ ! $(getent group step-ca) ]; then
    echo "Creating the step-ca group..."
    sudo groupadd -f step-ca
fi

# Create the CA configuration directory
if [ ! -d /etc/step-ca ]; then
    echo "Creating the CA directories..."
    sudo mkdir /etc/step-ca/
    sudo chown step-ca:step-ca /etc/step-ca
    sudo chmod 700 /etc/step-ca
fi

# Run the next part of the setup as the step-ca user
echo "Switching to the step-ca user."
sudo -u step-ca /bin/bash << EOF

# Exit on error
set -e

# Set the base path for the CA
export STEPPATH=/etc/step-ca

# Initialize the CA
if [ ! -f /etc/step-ca/config/ca.json ]; then

    # Exit on error
    set -e

    echo "Initializing the CA..."
    if [ ! -d /etc/step-ca/secrets ]; then
        mkdir /etc/step-ca/secrets
        chmod 700 /etc/step-ca/secrets
    fi

    echo "Generating the provisioner password..."
    touch /etc/step-ca/secrets/provisioner-password
    chmod 600 /etc/step-ca/secrets/provisioner-password
    step crypto rand 256 > /etc/step-ca/secrets/provisioner-password

    echo "Generating the root CA key password..."
    touch /etc/step-ca/secrets/key-password-root
    chmod 600 /etc/step-ca/secrets/key-password-root
    step crypto rand 256 > /etc/step-ca/secrets/key-password-root

    echo "Generating the intermediate CA key password..."
    touch /etc/step-ca/secrets/key-password-intermediate
    chmod 600 /etc/step-ca/secrets/key-password-intermediate
    step crypto rand 256 > /etc/step-ca/secrets/key-password-intermediate

    echo "Initializing the CA..."
    step ca init \
        --deployment-type standalone \
        --name "Smallstep CA for RedPepper" \
        --address ":5003" \
        --password-file /etc/step-ca/secrets/key-password-root \
        --provisioner redpepper \
        --provisioner-password-file /etc/step-ca/secrets/provisioner-password

    echo "Changing the password for the intermediate CA..."
    step crypto change-pass /etc/step-ca/secrets/intermediate_ca_key \
        --password-file /etc/step-ca/secrets/key-password-root \
        --new-password-file /etc/step-ca/secrets/key-password-intermediate \
        --force

    echo "Changing the max validity of leaf certificates to 1 week..."
    jq '.authority.provisioners[0].claims.maxTLSCertDuration = "168h"' /etc/step-ca/config/ca.json > /etc/step-ca/config/ca.json.tmp
    mv /etc/step-ca/config/ca.json.tmp /etc/step-ca/config/ca.json
    
    echo
    echo "The CA has been initialized."
    echo -e "\e[0;31m"
    echo "############################################################################################################"
    echo
    echo "You must now remove the root CA key and its password from the server and store it in a secure location."
    echo
    echo "############################################################################################################"
    echo -e "\e[;33m"
    echo "For increased security, generate the root CA key on an air-gapped machine and use it to bootstrap the CA according to the documentation."
    echo "https://smallstep.com/docs/step-ca/certificate-authority-server-production/#safeguard-your-root-and-intermediate-keys"
    echo -e "\e[0m"
fi
EOF

# Set up the service
echo "Setting up the step-ca service..."
sudo ln -sf /opt/redpepper/setup/step-ca.service /etc/systemd/system/step-ca.service
sudo systemctl daemon-reload
sudo systemctl enable step-ca

# Done
echo
echo -e "\e[32mSetup complete!\e[0m"
echo
echo "You can now start the Smallstep CA service with:"
echo "    sudo systemctl start step-ca"
echo