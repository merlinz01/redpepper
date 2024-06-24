#!/bin/bash

# Exit on error
set -e

sudo -u redpepper step ca bootstrap --ca-url https://localhost:5003 --fingerprint "$(sudo -u step-ca step certificate fingerprint /etc/redpepper-step-ca/certs/root_ca.crt)"

export TOKEN="$(sudo -u step-ca step ca token "RedPepper Manager" --root /etc/redpepper-step-ca/certs/root_ca.crt --password-file /etc/redpepper-step-ca/secrets/provisioner-password --ca-url https://localhost:5003)"

sudo -u redpepper bash << EOF

# Exit on error
set -e

# Request a certificate
step ca certificate "RedPepper Manager" \
    /etc/redpepper/manager-cert.pem \
    /etc/redpepper/manager-key.pem \
    --not-after 168h \
    --ca-url https://localhost:5003 \
    --token $TOKEN

# Configure TLS parameters
cat << EOF1 > /etc/redpepper/manager.d/01-smallstep-tls.yml
tls_cert_file: /etc/redpepper/manager-cert.pem
tls_key_file: /etc/redpepper/manager-key.pem
tls_key_password: ""
tls_ca_file: /opt/redpepper/.step/certs/root_ca.crt
tls_verify_mode: required
tls_check_hostname: false
EOF1

EOF

cat << EOF > /etc/cron.d/step-ca-renew-redpepper-manager-cert
# Check for possible certificate renewal every half hour
*/30 * * * *   root   STEPPATH=/etc/redpepper-step-ca/ step ca renew --force --expires-in 24h /etc/redpepper/manager-cert.pem /etc/redpepper/manager-key.pem --exec "systemctl restart redpepper-manager"
EOF
