#!/bin/bash
# Script to manually configure DDNS and SSL on Synology

DDNS_HOSTNAME="amrs-maintenance.dscloud.me"

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p /volume1/docker/amrs-data
mkdir -p /volume1/docker/amrs-data/ssl
mkdir -p /volume1/docker/amrs-data/nginx/conf.d

# Generate self-signed certificate
echo "Generating self-signed SSL certificate..."
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /volume1/docker/amrs-data/ssl/privkey.pem \
    -out /volume1/docker/amrs-data/ssl/fullchain.pem \
    -subj "/CN=$DDNS_HOSTNAME" \
    -addext "subjectAltName=DNS:$DDNS_HOSTNAME,DNS:localhost"

echo "Self-signed certificate created successfully."
echo

echo "DSM Manual Configuration Steps:"
echo "==============================="
echo
echo "1. To configure DDNS:"
echo "   - Go to Control Panel → External Access → DDNS"
echo "   - Click 'Add' and set up your DDNS provider"
echo
echo "2. To set up a proper SSL certificate:"
echo "   - Go to Control Panel → Security → Certificate"
echo "   - Click 'Add' → 'Add a new certificate'"
echo "   - Choose 'Get a certificate from Let's Encrypt'"
echo "   - Follow the wizard with domain: $DDNS_HOSTNAME"
echo
echo "3. Copy the Let's Encrypt certificate (after it's issued):"
echo "   - Find your certificate files (typically in /usr/syno/etc/certificate/)"
echo "   - Copy files to your Docker volume:"
echo "     cp /path/to/fullchain.pem /volume1/docker/amrs-data/ssl/"
echo "     cp /path/to/privkey.pem /volume1/docker/amrs-data/ssl/"
echo
echo "4. Restart the NGINX container:"
echo "   - docker-compose restart nginx"
