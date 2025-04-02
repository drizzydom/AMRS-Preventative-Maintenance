#!/bin/bash
# =============================================================================
# AMRS SSL Certificate Setup Script
# This script sets up SSL certificates for secure HTTPS access
# =============================================================================

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BOLD}AMRS SSL Certificate Setup${NC}"
echo "========================="
echo

# Check if data directory is provided as argument
if [ -n "$1" ]; then
    DATA_DIR="$1"
    echo "Using provided data directory: $DATA_DIR"
else
    # Default directory for Synology
    if [ -d "/volume1" ]; then
        DATA_DIR="/volume1/docker/amrs-data"
    else
        DATA_DIR="$HOME/amrs-data"
    fi
    echo "Using default data directory: $DATA_DIR"
fi

SSL_DIR="$DATA_DIR/ssl"
mkdir -p "$SSL_DIR"

# Check if domain is provided as second argument
if [ -n "$2" ]; then
    DOMAIN="$2"
    echo "Using provided domain name: $DOMAIN"
else
    # Use hostname if no domain specified
    DOMAIN=$(hostname)
    echo "Using hostname as domain: $DOMAIN"
fi

# Function to find and use existing Synology certificates
find_synology_certificates() {
    echo "Searching for existing Synology certificates..."
    
    CERT_LOCATIONS=(
        "/usr/syno/etc/certificate/system/default"
        "/usr/local/etc/certificate/_archive"
        "/usr/syno/etc/certificate/ReverseProxy"
        "/usr/local/etc/certificate/ReverseProxy"
        "/volume1/@appstore/CertManager/etc"
        "/etc/letsencrypt/live/$DOMAIN"
    )
    
    for location in "${CERT_LOCATIONS[@]}"; do
        if [ -d "$location" ]; then
            echo "Checking directory: $location"
            
            # For Let's Encrypt certificates
            if [[ $location == *"letsencrypt"* ]]; then
                if [ -f "$location/fullchain.pem" ] && [ -f "$location/privkey.pem" ]; then
                    echo -e "${GREEN}Found Let's Encrypt certificate at $location${NC}"
                    cp "$location/fullchain.pem" "$SSL_DIR/" || return 1
                    cp "$location/privkey.pem" "$SSL_DIR/" || return 1
                    return 0
                fi
                continue
            fi
            
            # For Synology certificates
            for cert_dir in "$location"/*; do
                if [ -d "$cert_dir" ]; then
                    cert_file=""
                    key_file=""
                    
                    # Find certificate file
                    if [ -f "$cert_dir/cert.pem" ]; then
                        cert_file="$cert_dir/cert.pem"
                    elif [ -f "$cert_dir/fullchain.pem" ]; then
                        cert_file="$cert_dir/fullchain.pem"
                    fi
                    
                    # Find key file
                    if [ -f "$cert_dir/privkey.pem" ]; then
                        key_file="$cert_dir/privkey.pem"
                    fi
                    
                    # If both files found, copy them
                    if [ -n "$cert_file" ] && [ -n "$key_file" ]; then
                        echo -e "${GREEN}Found certificate at $cert_dir${NC}"
                        cp "$cert_file" "$SSL_DIR/fullchain.pem" || return 1
                        cp "$key_file" "$SSL_DIR/privkey.pem" || return 1
                        return 0
                    fi
                fi
            done
        fi
    done
    
    return 1
}

# Try to find existing certificates first
echo -e "${BOLD}1. Searching for existing certificates...${NC}"
if find_synology_certificates; then
    echo -e "${GREEN}✓ Using existing certificates${NC}"
else
    echo -e "${YELLOW}! No existing certificates found, generating self-signed certificate${NC}"

    # Generate self-signed certificate
    echo -e "${BOLD}2. Generating self-signed certificate...${NC}"
    
    # Create a temporary OpenSSL config file
    SSL_CONFIG_FILE="$SSL_DIR/openssl_temp.cnf"
    cat > "$SSL_CONFIG_FILE" << EOL
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no

[req_distinguished_name]
CN = $DOMAIN

[v3_req]
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = $DOMAIN
DNS.2 = localhost
IP.1 = 127.0.0.1
EOL
    
    # Try using modern OpenSSL syntax first
    echo "Generating certificate using OpenSSL..."
    if ! openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
        -keyout "$SSL_DIR/privkey.pem" \
        -out "$SSL_DIR/fullchain.pem" \
        -config "$SSL_CONFIG_FILE" 2>/dev/null; then
        
        echo -e "${YELLOW}! Modern OpenSSL syntax failed, trying older syntax...${NC}"
        
        # Try older OpenSSL syntax if the modern one fails
        if ! openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
            -keyout "$SSL_DIR/privkey.pem" \
            -out "$SSL_DIR/fullchain.pem" \
            -subj "/CN=$DOMAIN" 2>/dev/null; then
            
            echo -e "${RED}✗ Failed to generate certificate with OpenSSL${NC}"
            echo "Creating a minimal self-signed certificate as last resort..."
            
            # Extremely minimal certificate generation
            openssl genrsa -out "$SSL_DIR/privkey.pem" 2048
            openssl req -new -x509 -key "$SSL_DIR/privkey.pem" \
                -out "$SSL_DIR/fullchain.pem" \
                -days 3650 -subj "/CN=$DOMAIN"
        fi
    fi

    # Clean up the temporary config file
    rm -f "$SSL_CONFIG_FILE"
    
    echo -e "${GREEN}✓ Self-signed certificate generated${NC}"
fi

# Set proper permissions for the certificates
echo -e "${BOLD}3. Setting certificate permissions...${NC}"
chmod 644 "$SSL_DIR/fullchain.pem"
chmod 600 "$SSL_DIR/privkey.pem"
echo -e "${GREEN}✓ Certificate permissions set${NC}"

# Display certificate information
echo -e "${BOLD}4. Verifying certificate...${NC}"
if openssl x509 -in "$SSL_DIR/fullchain.pem" -text -noout | grep "Subject:" | head -1; then
    echo -e "${GREEN}✓ Certificate verified${NC}"
else
    echo -e "${RED}✗ Certificate verification failed${NC}"
    echo "The certificate may be invalid or corrupted."
fi

echo
echo -e "${GREEN}${BOLD}SSL certificate setup complete!${NC}"
echo "Certificates are stored in: $SSL_DIR"
if ! find_synology_certificates &>/dev/null; then
    echo -e "${YELLOW}Note: Using self-signed certificate - browsers will show a warning${NC}"
else
    echo -e "${GREEN}Using existing Synology certificate${NC}"
fi
