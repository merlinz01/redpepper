#!/bin/bash

# Exit on error
set -e

# Ask for the Manager host and port if not provided
if [ -z "$REDPEPPER_MANAGER_HOST" ]; then
    echo -e "Enter the Manager host (e.g. \e[1;32mmanager.example.com\e[0m):"
    read -r REDPEPPER_MANAGER_HOST
fi

if [ -z "$REDPEPPER_MANAGER_PORT" ]; then
    echo -e "Enter the Manager port (e.g. \e[1;32m7051\e[0m):"
    read -r REDPEPPER_MANAGER_PORT
fi

# Ask for the Agent ID if not provided
if [ -z "$REDPEPPER_AGENT_ID" ]; then
    echo -e "Enter the Agent ID (e.g. \e[1;32mwebserver1\e[0m):"
    read -r REDPEPPER_AGENT_ID
fi

# Generate the Agent secret if not provided
if [ -z "$REDPEPPER_AGENT_SECRET" ]; then
    REDPEPPER_AGENT_SECRET=$(openssl rand -hex 32)
    echo -e "The Agent secret hash is: \e[1;33m$(echo -n "$REDPEPPER_AGENT_SECRET" | sha256sum | cut -d ' ' -f1)\e[0m"
fi

# Run the following commands as the redpepper-agent user
sudo -u redpepper-agent bash << EOF

# Exit on error
set -e

# Write the authentication file
cat << EOF1 > /etc/redpepper-agent/agent.d/01-basic-config.yml
manager_host: $REDPEPPER_MANAGER_HOST
manager_port: $REDPEPPER_MANAGER_PORT
agent_id: $REDPEPPER_AGENT_ID
agent_secret: "$REDPEPPER_AGENT_SECRET"
EOF1

# Set the permissions
chmod 600 /etc/redpepper-agent/agent.d/01-basic-config.yml

EOF

# Clean up
unset REDPEPPER_MANAGER_HOST
unset REDPEPPER_MANAGER_PORT
unset REDPEPPER_AGENT_ID
unset REDPEPPER_AGENT_SECRET

# Done
echo -e "\e[1;32mAgent authentication has been configured successfully.\e[0m"
