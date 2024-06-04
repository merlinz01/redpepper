#!/bin/bash

# Make sure the script is run as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run the uninstall script as root."
    exit
fi

# Confirm the uninstallation
echo
echo -e "\e[31m#################################################################"
echo
echo "This script will uninstall both the RedPepper Agent and Manager."
echo
echo "This will also remove the Smallstep CA."
echo
echo "All configuration files and data will be FOREVER DELETED!"
echo
echo "#################################################################"
echo
read -r -p "Are you sure you want to continue? (yes/no) " response
if [ "$response" != "yes" ]; then
    echo -e "Uninstallation aborted.\e[0m"
    exit
fi
echo -e "\e[33m"
read -r -p "Are you really, really sure you understand what you are about to do? (I understand/I don't understand) " response
if [ "$response" != "I understand" ]; then
    echo -e "Uninstallation aborted.\e[0m"
    exit
fi
echo -e "\e[0m"

# Stop the services
echo "Stopping the RedPepper Agent and Manager and Smallstep CA services..."
systemctl stop redpepper-agent 2> /dev/null
systemctl stop redpepper-manager 2> /dev/null
systemctl stop step-ca 2> /dev/null

# Remove the services
echo "Removing the RedPepper Agent and Manager and Smallstep CA services..."
systemctl disable redpepper-agent 2> /dev/null
systemctl disable redpepper-manager 2> /dev/null
systemctl disable step-ca 2> /dev/null
rm -f /etc/systemd/system/redpepper-agent.service
rm -f /etc/systemd/system/redpepper-manager.service
rm -f /etc/systemd/system/step-ca.service
systemctl daemon-reload

# Remove the RedPepper Manager
echo "Removing the RedPepper Manager..."
rm -rf /opt/redpepper
rm -rf /etc/redpepper
rm -rf /var/lib/redpepper
rm -rf /var/log/redpepper
rm -f /etc/cron.d/step-ca-renew-redpepper-manager-cert
rm -f /etc/cron.d/step-ca-renew-redpepper-api-cert

# Remove the RedPepper Agent
echo "Removing the RedPepper Agent..."
rm -rf /opt/redpepper-agent
rm -rf /etc/redpepper-agent
rm -rf /var/lib/redpepper-agent
rm -f /etc/cron.d/step-ca-renew-redpepper-agent-cert

# Remove the Smallstep CA
echo "Removing the Smallstep CA..."
rm -rf /etc/step-ca

# Done
echo
echo -e "\e[33mUninstallation complete!\e[0m"
echo