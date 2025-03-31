#!/bin/bash

# Create directories
mkdir -p nginx/ssl

# Check if certificates exist, if not create self-signed ones
if [ ! -f nginx/ssl/fullchain.pem ] || [ ! -f nginx/ssl/privkey.pem ]; then
    echo "SSL certificates not found, creating temporary self-signed certificates..."
    
    # Create self-signed certificate
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/privkey.pem \
        -out nginx/ssl/fullchain.pem \
        -subj "/CN=temporary-cert" \
        -addext "subjectAltName=DNS:localhost,DNS:amrs-maintenance.dscloud.me"
    
    echo "Temporary certificates created. Replace these with real certificates when available."
else
    echo "SSL certificates found in nginx/ssl directory."
fi

echo "You can now run docker-compose up"
