
# Exit on error
set -e

# Make sure RedPepper Manager is installed
if [ ! -d /opt/redpepper ]; then
    echo -e "\e[0;33mThe RedPepper Manager is not installed. Please run the bootstrap-manager.sh script first.\e[0m"
    exit
fi

# Install the required packages
echo "Installing the required packages..."
sudo apt-get update > /dev/null
sudo apt-get install -y wget jq | grep upgraded

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
    sudo useradd -r -s /bin/false step-ca -d /etc/redpepper-step-ca
fi
if [ ! $(getent group step-ca) ]; then
    echo "Creating the step-ca group..."
    sudo groupadd -f step-ca
fi

# Create the CA configuration directory
if [ ! -d /etc/redpepper-step-ca ]; then
    echo "Creating the CA directories..."
    sudo mkdir /etc/redpepper-step-ca/
    sudo chown step-ca:step-ca /etc/redpepper-step-ca
    sudo chmod 700 /etc/redpepper-step-ca
fi

# Run the next part of the setup as the step-ca user
echo "Switching to the step-ca user."
sudo -u step-ca /bin/bash << EOF

# Exit on error
set -e

# Set the base path for the CA
export STEPPATH=/etc/redpepper-step-ca

# Initialize the CA
if [ ! -f \$STEPPATH/config/ca.json ]; then

    # Exit on error
    set -e

    echo "Initializing the CA..."
    if [ ! -d \$STEPPATH/secrets ]; then
        mkdir \$STEPPATH/secrets
        chmod 700 \$STEPPATH/secrets
    fi

    echo "Generating the provisioner password..."
    touch \$STEPPATH/secrets/provisioner-password
    chmod 600 \$STEPPATH/secrets/provisioner-password
    step crypto rand --format hex 256 > \$STEPPATH/secrets/provisioner-password

    echo "Generating the root CA key password..."
    touch \$STEPPATH/secrets/key-password-root
    chmod 600 \$STEPPATH/secrets/key-password-root
    step crypto rand --format hex 256 > \$STEPPATH/secrets/key-password-root

    echo "Generating the intermediate CA key password..."
    touch \$STEPPATH/secrets/key-password-intermediate
    chmod 600 \$STEPPATH/secrets/key-password-intermediate
    step crypto rand --format hex 256 > \$STEPPATH/secrets/key-password-intermediate

    echo "Initializing the CA..."
    step ca init \
        --deployment-type standalone \
        --name "Smallstep CA for RedPepper" \
        --address ":5003" \
        --dns \$(hostname) \
        --dns localhost \
        --password-file \$STEPPATH/secrets/key-password-root \
        --provisioner redpepper \
        --provisioner-password-file \$STEPPATH/secrets/provisioner-password

    echo "Changing the password for the intermediate CA..."
    step crypto change-pass \$STEPPATH/secrets/intermediate_ca_key \
        --password-file \$STEPPATH/secrets/key-password-root \
        --new-password-file \$STEPPATH/secrets/key-password-intermediate \
        --force

    echo "Changing the max validity of leaf certificates to 1 week..."
    jq '.authority.provisioners[0].claims.maxTLSCertDuration = "168h"' \$STEPPATH/config/ca.json > \$STEPPATH/config/ca.json.tmp
    mv \$STEPPATH/config/ca.json.tmp \$STEPPATH/config/ca.json
    
    echo
    echo "The CA has been initialized."
    echo
    echo -e "The root CA certificate fingerprint is \e[1;32m\$(step certificate fingerprint \$STEPPATH/certs/root_ca.crt)\e[0m"
    echo -e "The provisioner password is at \e[1;32m\$STEPPATH/secrets/provisioner-password\e[0m"
    echo
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
echo "Setting up the redpepper-step-ca service..."
sudo ln -sf /opt/redpepper/setup/step-ca.service /etc/systemd/system/redpepper-step-ca.service
sudo systemctl daemon-reload
sudo systemctl enable redpepper-step-ca

# Done
echo
echo -e "\e[32mSetup complete!\e[0m"
echo
echo "You can now start the Smallstep CA service with:"
echo "    sudo systemctl start redpepper-step-ca"
echo