#!/bin/bash

# Exit on error
set -e

sudo -u redpepper step ca bootstrap --ca-url https://localhost:5003 --fingerprint "$(sudo -u step-ca step certificate fingerprint /etc/redpepper-step-ca/certs/root_ca.crt)"

export TOKEN="$(sudo -u step-ca step ca token "RedPepper API" --root /etc/redpepper-step-ca/certs/root_ca.crt --password-file /etc/redpepper-step-ca/secrets/provisioner-password --ca-url https://localhost:5003)"

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
