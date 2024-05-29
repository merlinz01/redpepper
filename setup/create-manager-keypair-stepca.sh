#!/bin/bash

# Exit on error
set -e

export TOKEN="$(sudo -u step-ca step ca token "RedPepper Manager" --root /etc/step-ca/certs/root_ca.crt --password-file /etc/step-ca/secrets/provisioner-password --ca-url https://$(hostname):5003)"

sudo -u redpepper step ca certificate "RedPepper Manager" \
    /etc/redpepper/manager-cert.pem \
    /etc/redpepper/manager-key.pem \
    --not-after 168h \
    --ca-url https://localhost:5003 \
    --token $TOKEN

cat << EOF > /etc/cron.d/step-ca-renew
# Check for possible certificate renewal every half hour
*/30 * * * *   root   step ca renew --force --expires-in 24h /etc/redpepper/manager-cert.pem /etc/redpepper/manager-key.pem --exec "systemctl restart redpepper-manager"
EOF
