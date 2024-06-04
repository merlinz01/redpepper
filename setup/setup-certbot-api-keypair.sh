#!/bin/bash

# Exit on error
set -e

# Install certbot
echo "Installing certbot..."
sudo apt-get install -y certbot

# Run certbot
echo "Running certbot..."
sudo certbot certonly --standalone

# Make private key readable by the redpepper user
echo "Making the private key readable by the redpepper user..."
sudo chown redpepper:redpepper /etc/letsencrypt/live/*/privkey.pem
sudo chmod 755 /etc/letsencrypt/{live,archive}

# Configure the Manager to use the new key pair
echo "Configuring the Manager to use the new key pair..."
sudo -u redpepper bash << EOF
cat << EOF1 > /etc/redpepper/manager.d/01-letsencrypt-api-keypair.yml
api_tls_cert_file: /etc/letsencrypt/live/$(hostname)/fullchain.pem
api_tls_key_file: /etc/letsencrypt/live/$(hostname)/privkey.pem
EOF1
EOF

# Restart the Manager
echo "Restarting the Manager..."
sudo systemctl restart redpepper-manager