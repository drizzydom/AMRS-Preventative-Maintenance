#!/bin/bash

# Find Synology SSL certificates for a specific domain
# This script will search common locations for certificates

set -e

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'  # No Color

# Get domain name from command line or prompt
DOMAIN="$1"
if [ -z "$DOMAIN" ]; then
    read -p "Enter domain name to search for: " DOMAIN
fi

OUTPUT_DIR="./found_certificates"
mkdir -p "$OUTPUT_DIR"

echo -e "${BOLD}${BLUE}Searching for SSL certificates for domain: ${DOMAIN}${NC}"
echo

# Define common certificate locations on Synology
CERT_LOCATIONS=(
    "/usr/local/etc/certificate"
    "/usr/syno/etc/certificate"
    "/usr/syno/etc/certificate/system/default"
    "/usr/local/share/ca-certificates"
    "/etc/ssl/certs"
    "/volume1/@appstore/CertManager/etc"
    "/etc/letsencrypt/live"
    "/usr/local/etc/letsencrypt/live"
    "/volume1/docker/letsencrypt/etc/live"
)

CERT_FOUND=false

echo -e "${BOLD}STAGE 1: Looking for directories matching domain name...${NC}"
for LOC in "${CERT_LOCATIONS[@]}"; do
    if [ -d "$LOC" ]; then
        echo "Checking $LOC..."
        if [ -d "$LOC/$DOMAIN" ]; then
            if [ -f "$LOC/$DOMAIN/fullchain.pem" ] && [ -f "$LOC/$DOMAIN/privkey.pem" ]; then
                echo -e "${GREEN}✓ Found certificates in $LOC/$DOMAIN${NC}"
                cp "$LOC/$DOMAIN/fullchain.pem" "$OUTPUT_DIR/fullchain.pem"
                cp "$LOC/$DOMAIN/privkey.pem" "$OUTPUT_DIR/privkey.pem"
                chmod 644 "$OUTPUT_DIR/fullchain.pem"
                chmod 600 "$OUTPUT_DIR/privkey.pem"
                CERT_FOUND=true
                break
            else
                echo -e "${YELLOW}! Found directory but missing certificate files in $LOC/$DOMAIN${NC}"
            fi
        fi
    fi
done

echo
echo -e "${BOLD}STAGE 2: Searching for certificate files containing domain name...${NC}"
if [ "$CERT_FOUND" = false ]; then
    for LOC in "${CERT_LOCATIONS[@]}"; do
        if [ -d "$LOC" ]; then
            echo "Searching in $LOC..."
            # Find all certificate files recursively (depth limit for speed)
            FOUND_CERTS=$(find "$LOC" -maxdepth 3 -type f -name "fullchain.pem" 2>/dev/null)
            for CERT in $FOUND_CERTS; do
                CERT_DIR=$(dirname "$CERT")
                echo "  Checking $CERT..."
                if [ -f "$CERT_DIR/privkey.pem" ]; then
                    if openssl x509 -in "$CERT" -noout -text | grep -q "$DOMAIN"; then
                        echo -e "${GREEN}✓ Found matching certificate in $CERT_DIR${NC}"
                        cp "$CERT" "$OUTPUT_DIR/fullchain.pem"
                        cp "$CERT_DIR/privkey.pem" "$OUTPUT_DIR/privkey.pem"
                        chmod 644 "$OUTPUT_DIR/fullchain.pem"
                        chmod 600 "$OUTPUT_DIR/privkey.pem"
                        CERT_FOUND=true
                        break 2
                    fi
                fi
            done
        fi
    done
fi

if [ "$CERT_FOUND" = true ]; then
    echo
    echo -e "${GREEN}${BOLD}SUCCESS! Certificates found and copied to $OUTPUT_DIR${NC}"
    echo
    echo -e "${BOLD}Certificate details:${NC}"
    openssl x509 -in "$OUTPUT_DIR/fullchain.pem" -noout -subject -issuer -dates
    
    echo
    echo -e "${BOLD}To use these certificates with your Docker setup:${NC}"
    echo "1. Copy them to your data directory:"
    echo "   cp $OUTPUT_DIR/fullchain.pem /volume1/docker/amrs-data/ssl/"
    echo "   cp $OUTPUT_DIR/privkey.pem /volume1/docker/amrs-data/ssl/"
    echo "2. Restart your Nginx container:"
    echo "   docker-compose restart nginx"
else
    echo
    echo -e "${RED}${BOLD}No certificates found for $DOMAIN${NC}"
    echo
    echo -e "${BOLD}Options:${NC}"
    echo "1. Generate a self-signed certificate:"
    echo "   ./setup_temp_ssl.sh $DOMAIN"
    echo "2. Set up Let's Encrypt through Synology DSM:"
    echo "   Control Panel → Security → Certificate"
    echo "3. Manually check for certificates using find command:"
    echo "   find /usr -name \"*.pem\" -type f | grep -i cert"
fi
