#!/bin/bash

# Exit on error
set -e

# Install the Smallstep CLI
if [ ! -f /usr/bin/step ]; then
    echo "Downloading and installing the Smallstep CLI..."
    cd /tmp
    wget -N https://dl.smallstep.com/gh-release/cli/gh-release-header/v0.26.1/step-cli_0.26.1_amd64.deb -q
    sudo dpkg -i step-cli_0.26.1_amd64.deb
fi

# Ask for the Manager Step CA host if not provided
if [ -z "$REDPEPPER_STEPCA_HOST" ]; then
    echo -e "Enter the Manager host (e.g. \e[1;32mmanager.example.com\e[0m):"
    read -r REDPEPPER_STEPCA_HOST
else
    echo -e "Using the Manager host: \e[1;32m$REDPEPPER_STEPCA_HOST\e[0m"
fi

# Ask for the Manager Step CA fingerprint if not provided
if [ -z "$REDPEPPER_STEPCA_FINGERPRINT" ]; then
    echo -e "Enter the Manager Step CA fingerprint (e.g. \e[1;32m1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef\e[0m):"
    read -r REDPEPPER_STEPCA_FINGERPRINT
else
    echo -e "Using the Manager Step CA fingerprint: \e[1;32m$REDPEPPER_STEPCA_FINGERPRINT\e[0m"
fi

# Run the following commands as the redpepper-agent user
sudo -u redpepper-agent bash << EOF

# Exit on error
set -e

# Bootstrap the CA configuration
step ca bootstrap --ca-url https://$REDPEPPER_STEPCA_HOST:5003 --fingerprint $REDPEPPER_STEPCA_FINGERPRINT

# Request a certificate
step ca certificate "RedPepper Agent" \
    /etc/redpepper-agent/agent-cert.pem \
    /etc/redpepper-agent/agent-key.pem \
    --not-after 168h \
    --ca-url https://$REDPEPPER_STEPCA_HOST:5003

# Configure TLS parameters
cat << EOF1 > /etc/redpepper-agent/agent.d/01-smallstep-tls.yml
tls_cert_file: /etc/redpepper-agent/agent-cert.pem
tls_key_file: /etc/redpepper-agent/agent-key.pem
tls_key_password: ""
tls_ca_file: /opt/redpepper-agent/.step/certs/root_ca.crt
tls_verify_mode: required
tls_check_hostname: false
EOF1

EOF

cat << EOF1 > /etc/cron.d/step-ca-renew-redpepper-agent-cert
# Check for possible certificate renewal every half hour
*/30 * * * *   root   STEPPATH=/opt/redpepper-agent/.step step ca renew --force --expires-in 24h /etc/redpepper-agent/agent-cert.pem /etc/redpepper-agent/agent-key.pem --exec "systemctl restart redpepper-agent > /var/log/redpepper-agent/agent-renew.log 2>&1"
EOF1

# Clean up
unset REDPEPPER_STEPCA_HOST
unset REDPEPPER_STEPCA_FINGERPRINT

# Done
echo -e "\e[1;32mAgent keypair has been created successfully.\e[0m"
