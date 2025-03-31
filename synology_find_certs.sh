#!/bin/bash

echo "Finding Synology SSL Certificates"
echo "================================="

# Create directory for certificates if it doesn't exist
mkdir -p nginx/ssl

# Potential certificate locations on Synology
echo "Searching for certificate locations..."
echo "Common locations include:"
echo " - /usr/syno/etc/certificate"
echo " - /usr/local/etc/certificate"
echo " - /volume1/@appstore/CertManager"

# Check if any certificates exist in these locations
for location in "/usr/syno/etc/certificate" "/usr/local/etc/certificate" "/volume1/@appstore/CertManager"; do
    if [ -d "$location" ]; then
        echo "Found certificates directory: $location"
        echo "Look for certificate files in subdirectories using:"
        echo "  find $location -name \"*.pem\""
    fi
done

echo
echo "To copy your certificates to nginx/ssl:"
echo "1. Find your certificate files first"
echo "2. Once found, run these commands (adjust paths as needed):"
echo "   cp /path/to/your/fullchain.pem ./nginx/ssl/"
echo "   cp /path/to/your/privkey.pem ./nginx/ssl/"
echo
echo "Alternatively, create self-signed certificates with:"
echo "  ./setup_temp_ssl.sh"
