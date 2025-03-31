#!/bin/bash

echo "Fixing port conflict for AMRS Maintenance Tracker"
echo "==============================================="

# Set new port
NEW_PORT=8443
echo "Setting external HTTPS port to $NEW_PORT"

# Update docker-compose.yml to use the new port
sed -i "s/- \"443:443\"/- \"$NEW_PORT:443\"/" docker-compose.yml

# If that fails (different format), try another pattern
sed -i "s/- \".*:443\"/- \"$NEW_PORT:443\"/" docker-compose.yml

echo "Updated docker-compose.yml to use port $NEW_PORT instead of 443"
echo "Now restart your containers with:"
echo "docker-compose down && docker-compose up -d"
echo
echo "Important: If you're using Synology's DDNS and Let's Encrypt certificates,"
echo "you should consider using Synology's built-in reverse proxy instead:"
echo "1. Remove the nginx service from docker-compose.yml"
echo "2. Configure a reverse proxy in DSM Control Panel → Login Portal → Advanced"
echo "3. Set it to forward HTTPS (port 443) to your app container (port 9000)"
