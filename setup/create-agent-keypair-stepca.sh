#!/bin/bash

# Exit on error
set -e

# Ask for the Manager Step CA host if not provided
if [ -z "$REDPEPPER_STEPCA_HOST" ]; then
    echo -e "Enter the Manager host (e.g. \e[1;32mmanager.example.com\e[0m):"
    read -r REDPEPPER_STEPCA_HOST
fi

# Ask for the Manager Step CA fingerprint if not provided
if [ -z "$REDPEPPER_STEPCA_FINGERPRINT" ]; then
    echo -e "Enter the Manager Step CA fingerprint (e.g. \e[1;32m1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef\e[0m):"
    read -r REDPEPPER_STEPCA_FINGERPRINT
fi

# Run the following commands as the redpepper-agent user
sudo -u redpepper-agent bash << EOF

# Bootstrap the CA configuration
step ca bootstrap --ca-url https://$REDPEPPER_STEPCA_HOST:5003 --fingerprint $REDPEPPER_STEPCA_FINGERPRINT

step ca certificate "RedPepper Agent" \
    /etc/redpepper-agent/agent-cert.pem \
    /etc/redpepper-agent/agent-key.pem \
    --not-after 168h \
    --ca-url https://$REDPEPPER_STEPCA_HOST:5003

EOF

cat << EOF1 > /etc/cron.d/step-ca-renew-redpepper-agent-cert
# Check for possible certificate renewal every half hour
*/30 * * * *   root   step ca renew --force --expires-in 24h /etc/redpepper-agent/agent-cert.pem /etc/redpepper/agent-key.pem --exec "systemctl restart redpepper-agent"
EOF1

# Clean up
unset REDPEPPER_STEPCA_HOST
unset REDPEPPER_STEPCA_FINGERPRINT

# Done
echo -e "\e[1;32mAgent keypair has been created successfully.\e[0m"
