#!/bin/bash
# =============================================================================
# AMRS Synology Security Hardening Script
# This script applies security best practices for AMRS on Synology
# =============================================================================

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BOLD}AMRS Synology Security Hardening${NC}"
echo "==============================="
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

# Get script directory and project directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BOLD}1. Checking for SSL certificate...${NC}"
SSL_DIR="$DATA_DIR/ssl"
if [ -f "$SSL_DIR/fullchain.pem" ] && [ -f "$SSL_DIR/privkey.pem" ]; then
    echo -e "${GREEN}✓ SSL certificates found${NC}"
    
    # Check if self-signed
    ISSUER=$(openssl x509 -in "$SSL_DIR/fullchain.pem" -issuer -noout 2>/dev/null | grep -i "Let's Encrypt")
    if [ -n "$ISSUER" ]; then
        echo -e "${GREEN}✓ Using Let's Encrypt certificate${NC}"
    else
        echo -e "${YELLOW}! Using self-signed or non-Let's Encrypt certificate${NC}"
        echo "   Consider upgrading to a Let's Encrypt certificate for production use"
        echo "   Run: ./scripts/generate_ssl.sh $DATA_DIR your-domain.com"
    fi
else
    echo -e "${RED}✗ SSL certificates not found${NC}"
    echo "   Run: ./scripts/generate_ssl.sh $DATA_DIR"
fi
echo

echo -e "${BOLD}2. Updating Nginx security headers...${NC}"
NGINX_CONF="$DATA_DIR/nginx/conf.d/default.conf"

if [ -f "$NGINX_CONF" ]; then
    # Backup the config file
    cp "$NGINX_CONF" "${NGINX_CONF}.bak"
    
    # Check if security headers already exist
    if grep -q "add_header X-Content-Type-Options" "$NGINX_CONF"; then
        echo -e "${GREEN}✓ Security headers already present${NC}"
    else
        echo "Adding security headers to Nginx configuration..."
        
        # Add security headers right after the server_name directive
        sed -i '/server_name/a \
    # Security headers\
    add_header X-Content-Type-Options nosniff;\
    add_header X-Frame-Options SAMEORIGIN;\
    add_header X-XSS-Protection "1; mode=block";\
    add_header Content-Security-Policy "default-src '\''self'\''; script-src '\''self'\'' '\''unsafe-inline'\''; style-src '\''self'\'' '\''unsafe-inline'\'' https://cdnjs.cloudflare.com; font-src '\''self'\'' https://cdnjs.cloudflare.com; img-src '\''self'\'' data:";\
    add_header Referrer-Policy strict-origin-when-cross-origin;\
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;' "$NGINX_CONF"
        
        echo -e "${GREEN}✓ Security headers added${NC}"
    fi
    
    # Ensure HTTPS-only configuration
    if grep -q "return 301 https" "$NGINX_CONF"; then
        echo -e "${GREEN}✓ HTTP to HTTPS redirection already configured${NC}"
    else
        echo "Configuring HTTP to HTTPS redirection..."
        # Look for the first server block
        sed -i '0,/server {/s//server {\n    # Redirect all HTTP to HTTPS\n    listen 80;\n    server_name _;\n    return 301 https:\/\/$host$request_uri;\n}\n\nserver {/' "$NGINX_CONF"
        echo -e "${GREEN}✓ HTTP to HTTPS redirection configured${NC}"
    fi
    
    # Restart Nginx to apply changes
    docker-compose restart nginx
    echo -e "${GREEN}✓ Nginx restarted to apply new configuration${NC}"
else
    echo -e "${RED}✗ Nginx configuration not found${NC}"
    echo "   Run: ./scripts/configure_nginx.sh $DATA_DIR"
fi
echo

echo -e "${BOLD}3. Checking database permissions...${NC}"
DB_FILE="$DATA_DIR/data/app.db"
if [ -f "$DB_FILE" ]; then
    # Get current permissions
    PERMS=$(stat -c "%a" "$DB_FILE" 2>/dev/null || stat -f "%Lp" "$DB_FILE" 2>/dev/null)
    
    if [ "$PERMS" = "666" ]; then
        echo -e "${YELLOW}! Database file has very permissive permissions (666)${NC}"
        echo "   This is required for container access but should be restricted if possible"
    elif [ "$PERMS" = "664" ]; then
        echo -e "${GREEN}✓ Database has good permissions (664)${NC}"
    else
        echo "Setting database permissions to 664..."
        chmod 664 "$DB_FILE"
        echo -e "${GREEN}✓ Database permissions updated${NC}"
    fi
else
    echo -e "${YELLOW}! Database file not found at $DB_FILE${NC}"
    echo "   It may be in another location or not created yet"
fi
echo

echo -e "${BOLD}4. Checking Docker container security...${NC}"
# Check if containers are running with default network
if docker network ls | grep -q "amrs_network"; then
    echo -e "${GREEN}✓ Using dedicated Docker network${NC}"
else
    echo -e "${YELLOW}! Using default bridge network${NC}"
    echo "   Consider creating a dedicated network with: ./scripts/create_docker_network.sh"
fi

# Check container restart policy
RESTART_POLICY=$(docker inspect --format='{{.HostConfig.RestartPolicy.Name}}' amrs-maintenance-tracker 2>/dev/null)
if [ "$?" -eq 0 ]; then
    if [ "$RESTART_POLICY" = "unless-stopped" ] || [ "$RESTART_POLICY" = "always" ]; then
        echo -e "${GREEN}✓ Container has appropriate restart policy: $RESTART_POLICY${NC}"
    else
        echo -e "${YELLOW}! Container has restart policy: $RESTART_POLICY${NC}"
        echo "   Consider changing to 'unless-stopped' in docker-compose.yml"
    fi
else
    echo -e "${YELLOW}! Container not running, cannot check restart policy${NC}"
fi
echo

echo -e "${BOLD}5. Setting up firewall rules (informational)...${NC}"
echo -e "${YELLOW}! Synology has its own firewall system${NC}"
echo "To enhance security with firewall rules:"
echo "1. Access your Synology DSM Control Panel"
echo "2. Open 'Security' > 'Firewall'"
echo "3. Create rules to only allow necessary ports:"
echo "   - Allow HTTP (80) and HTTPS (443) for web access"
echo "   - Restrict direct access to the application port (9000)"
echo "   - Consider limiting SSH access to specific IP addresses"
echo

echo -e "${BOLD}6. Securing sensitive files...${NC}"
echo "Securing SSL private key..."
if [ -f "$SSL_DIR/privkey.pem" ]; then
    chmod 600 "$SSL_DIR/privkey.pem"
    echo -e "${GREEN}✓ SSL private key permissions set to 600${NC}"
fi

# Create a more restrictive configuration for production
echo -e "${BOLD}7. Creating production-ready configuration...${NC}"
PROD_CONFIG="$DATA_DIR/production.env"

cat > "$PROD_CONFIG" << EOL
# Production environment settings for AMRS application
DEBUG=False
SECRET_KEY=$(openssl rand -hex 32)
HOST=0.0.0.0
PORT=9000
# Add other production-specific configuration here
EOL

echo -e "${GREEN}✓ Production configuration created at $PROD_CONFIG${NC}"
echo "   You can use this file for production deployments with:"
echo "   docker-compose --env-file $PROD_CONFIG up -d"
echo

echo -e "${GREEN}${BOLD}Security hardening completed!${NC}"
echo "Your AMRS installation on Synology has been secured according to best practices."
echo
echo "Recommended additional steps:"
echo "1. Implement Let's Encrypt for a trusted SSL certificate"
echo "2. Regularly update your Synology DSM and Docker images"
echo "3. Set up automated backups with the backup_config.sh script"
echo "4. Enable Synology's built-in firewall and security features"
echo "5. Set up a strong password policy for your application users"
echo
echo "For production use, consider running in production mode:"
echo "COMPOSE_HTTP_TIMEOUT=180 docker-compose --env-file $PROD_CONFIG up -d"
