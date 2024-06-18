#!/bin/bash

# Exit on error
set -e

# Install certbot
echo "Installing certbot..."
sudo apt-get update > /dev/null
sudo apt-get install -y certbot | grep upgraded

# Run certbot
echo "Running certbot..."
sudo certbot certonly --standalone

# Make private key readable by the redpepper user
echo "Making the private key readable by the redpepper user..."
sudo chown redpepper:redpepper /etc/letsencrypt/live/*/privkey.pem
sudo chmod 600 /etc/letsencrypt/live/*/privkey.pem
sudo chmod 755 /etc/letsencrypt/{live,archive}

# Ask for the server hostname if not set
if [ -z "$REDPEPPER_HOSTNAME" ]; then
    # Set it to the current hostname
    export REDPEPPER_HOSTNAME=$(hostname)
    # Verify the hostname
    echo -e "\e[0;33mIs this the hostname that the certificates are for?\e[0m"
    read -i "$REDPEPPER_HOSTNAME" -e REDPEPPER_HOSTNAME
fi
echo "Configuring certificates from /etc/letsencrypt/live/$REDPEPPER_HOSTNAME"

# Make sure that hostname is correct
if [ ! -f /etc/letsencrypt/live/$REDPEPPER_HOSTNAME/fullchain.pem ]; then
    echo -e "\e[0;31mCould not find certificate in /etc/letsencrypt/live/$REDPEPPER_HOSTNAME. You must have entered a different hostname for the LetsEncrypt certificates.\e[0m"
    echo "Try running this script again and enter the correct hostname."
    exit 1
fi

# Configure the Manager to use the new key pair
echo "Configuring the Manager to use the new key pair..."
sudo -u redpepper bash << EOF
cat << EOF1 > /etc/redpepper/manager.d/01-letsencrypt-api-keypair.yml
api_tls_cert_file: /etc/letsencrypt/live/$(hostname)/fullchain.pem
api_tls_key_file: /etc/letsencrypt/live/$(hostname)/privkey.pem
EOF1
EOF
