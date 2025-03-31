#!/bin/bash

# Replace with your actual hostname
HOSTNAME="amrs-maintenance.dscloud.me"

echo "Checking hostname resolution for $HOSTNAME..."
echo

echo "Local DNS lookup:"
nslookup $HOSTNAME

echo
echo "Testing connectivity to your Synology NAS:"
ping -c 3 localhost

echo
echo "If the hostname doesn't resolve, consider adding it to your hosts file temporarily:"
echo "Add this line to /etc/hosts (on Linux/Mac) or C:\\Windows\\System32\\drivers\\etc\\hosts (on Windows):"
echo "127.0.0.1    $HOSTNAME"
