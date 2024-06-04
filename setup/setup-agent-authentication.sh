#!/bin/sh

# Exit on error
set -e

# Ask for the Manager host and port if not provided
if [ -z "$REDPEPPER_MANAGER_HOST" ]; then
    echo -e "Enter the Manager host (e.g. \e[1;32mmanager.example.com\e[0m):"
    read -r REDPEPPER_MANAGER_HOST
fi

if [ -z "$REDPEPPER_MANAGER_PORT" ]; then
    echo -e "Enter the Manager port (e.g. \e[1;32m7050\e[0m):"
    read -r REDPEPPER_MANAGER_PORT
fi

# Ask for the Agent ID if not provided
if [ -z "$REDPEPPER_AGENT_ID" ]; then
    echo -e "Enter the Agent ID (e.g. \e[1;32mwebserver1\e[0m):"
    read -r REDPEPPER_AGENT_ID
fi

# Ask for the Agent secret if not provided
if [ -z "$REDPEPPER_AGENT_SECRET" ]; then
    echo -e "Enter the Agent secret:"
    read -r REDPEPPER_AGENT_SECRET
fi

# Write the authentication file
cat << EOF > /etc/redpepper-agent/agent.d/01-authentication.yml
manager_host: $REDPEPPER_MANAGER_HOST
manager_port: $REDPEPPER_MANAGER_PORT
agent_id: $REDPEPPER_AGENT_ID
agent_secret: "$REDPEPPER_AGENT_SECRET"
EOF