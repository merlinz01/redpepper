#!/bin/bash

# Exit on error
set -e

export TOKEN="$(sudo -u step-ca step ca token "RedPepper Manager" --root /etc/step-ca/certs/root_ca.crt --password-file /etc/step-ca/secrets/provisioner-password --ca-url https://localhost:5003)"

sudo -u redpepper step ca certificate "RedPepper Manager" \
    /etc/redpepper/manager-cert.pem \
    /etc/redpepper/manager-key.pem \
    --not-after 168h \
    --ca-url https://localhost:5003 \
    --token $TOKEN
