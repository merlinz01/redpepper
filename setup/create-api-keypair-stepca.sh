#!/bin/bash

# Exit on error
set -e

export TOKEN="$(sudo -u step-ca step ca token "RedPepper API" --root /etc/step-ca/certs/root_ca.crt --password-file /etc/step-ca/secrets/provisioner-password --ca-url https://localhost:5003)"

sudo -u redpepper step ca certificate "RedPepper API" \
    /etc/redpepper/api-cert.pem \
    /etc/redpepper/api-key.pem \
    --not-after 168h \
    --ca-url https://localhost:5003 \
    --token $TOKEN

cat << EOF > /etc/cron.d/step-ca-renew-redpepper-api-cert
# Check for possible certificate renewal every half hour
*/30 * * * *   root   step ca renew --force --expires-in 24h /etc/redpepper/api-cert.pem /etc/redpepper/api-key.pem --exec "systemctl restart redpepper-manager"
EOF
