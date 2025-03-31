#!/bin/bash

echo "Fixing port conflicts for AMRS Maintenance Tracker"
echo "================================================="

# Set new ports
HTTP_PORT=8080
HTTPS_PORT=8443
echo "Setting external ports to: HTTP=$HTTP_PORT, HTTPS=$HTTPS_PORT"

# Update docker-compose.yml to use the new ports
if grep -q "\"80:80\"" docker-compose.yml; then
    echo "Changing port 80 mapping..."
    sed -i "s/- \"80:80\"/- \"$HTTP_PORT:80\"/" docker-compose.yml
elif grep -q "\".*:80\"" docker-compose.yml; then
    echo "Changing port 80 mapping (alternative format)..."
    sed -i "s/- \".*:80\"/- \"$HTTP_PORT:80\"/" docker-compose.yml
fi

if grep -q "\"443:443\"" docker-compose.yml; then
    echo "Changing port 443 mapping..."
    sed -i "s/- \"443:443\"/- \"$HTTPS_PORT:443\"/" docker-compose.yml
elif grep -q "\".*:443\"" docker-compose.yml; then
    echo "Changing port 443 mapping (alternative format)..."
    sed -i "s/- \".*:443\"/- \"$HTTPS_PORT:443\"/" docker-compose.yml
fi

echo "Updates complete!"
echo "docker-compose.yml now uses ports $HTTP_PORT and $HTTPS_PORT instead of 80 and 443"
echo 
echo "Next steps:"
echo "1. Restart containers: docker-compose down && docker-compose up -d"
echo "2. Update port forwarding on your router:"
echo "   - External port 80 → Synology port $HTTP_PORT"
echo "   - External port 443 → Synology port $HTTPS_PORT"
echo
echo "Alternative: Use Synology built-in reverse proxy"
echo "See reverse_proxy_guide.txt for instructions"
