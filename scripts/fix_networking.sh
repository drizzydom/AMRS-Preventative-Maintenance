#!/bin/bash
# =============================================================================
# AMRS Network and Permissions Fix Script
# This script fixes network connectivity and permission issues
# =============================================================================

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BOLD}AMRS Network and Permissions Fix Script${NC}"
echo "======================================"
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

echo -e "${BOLD}1. Creating hosts file fix for containers...${NC}"
cat > "$DATA_DIR/hosts_fix.sh" << 'EOF'
#!/bin/bash
# Add container hostname mappings to /etc/hosts
APP_IP=$(getent hosts app 2>/dev/null || getent hosts amrs-maintenance-tracker 2>/dev/null || echo "172.17.0.2")
NGINX_IP=$(getent hosts nginx 2>/dev/null || getent hosts amrs-nginx 2>/dev/null || echo "172.17.0.3")

echo "Adding host entries:"
echo "$APP_IP app amrs-maintenance-tracker"
echo "$NGINX_IP nginx amrs-nginx"

echo "$APP_IP app amrs-maintenance-tracker" >> /etc/hosts
echo "$NGINX_IP nginx amrs-nginx" >> /etc/hosts

echo "Current hosts file:"
cat /etc/hosts
EOF
chmod +x "$DATA_DIR/hosts_fix.sh"
echo -e "${GREEN}✓ Created hosts fix script${NC}"
echo

echo -e "${BOLD}2. Ensuring proper nginx configuration...${NC}"
mkdir -p "$DATA_DIR/nginx/conf.d"
cat > "$DATA_DIR/nginx/conf.d/default.conf" << 'EOF'
server {
    listen 80;
    server_name _;
    
    # For troubleshooting, allow direct HTTP access
    location / {
        proxy_pass http://app:9000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Extended timeouts
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # Required for websockets
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Custom error handling
        error_page 502 504 /502.html;
    }

    # Health check endpoint
    location = /api/health {
        proxy_pass http://app:9000/api/health;
    }
}

server {
    listen 443 ssl;
    server_name _;
    
    # Default self-signed certificates (replace with your own)
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    
    # Security settings
    ssl_protocols TLSv1.2 TLSv1.3;
    
    location / {
        proxy_pass http://app:9000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Extended timeouts
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # Custom error handling
        error_page 502 504 /502.html;
    }
}
EOF
echo -e "${GREEN}✓ Created simplified nginx configuration${NC}"
echo

echo -e "${BOLD}3. Creating custom error pages...${NC}"
mkdir -p "$DATA_DIR/nginx/html"
cat > "$DATA_DIR/nginx/html/502.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Temporarily Unavailable</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
        .spinner { 
            display: inline-block;
            width: 50px;
            height: 50px;
            border: 3px solid rgba(0,0,0,.3);
            border-radius: 50%;
            border-top-color: #007bff;
            animation: spin 1s ease-in-out infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="spinner"></div>
    <h1>Server starting up...</h1>
    <p>The application is initializing. This page will refresh automatically.</p>
    <p>If this page persists, please check server logs for errors.</p>
</body>
</html>
EOF
echo -e "${GREEN}✓ Created custom error page${NC}"
echo

echo -e "${BOLD}4. Creating directory structure with correct permissions...${NC}"
mkdir -p "$DATA_DIR/templates"
mkdir -p "$DATA_DIR/static/css"
mkdir -p "$DATA_DIR/static/js"
chmod -R 777 "$DATA_DIR"
echo -e "${GREEN}✓ Created directories with proper permissions${NC}"
echo

echo -e "${BOLD}5. Modifying docker-compose.yml...${NC}"
# Backup the original
if [ -f "docker-compose.yml" ]; then
    cp docker-compose.yml docker-compose.yml.bak
    
    # Update the container user to root temporarily for debugging
    sed -i'.tmp' 's/user:.*"/user: "root"/' docker-compose.yml 2>/dev/null || sed -i 's/user:.*"/user: "root"/' docker-compose.yml
    
    # Ensure hostname is set
    if ! grep -q "hostname:" docker-compose.yml; then
        sed -i'.tmp' '/container_name: amrs-maintenance-tracker/a\    hostname: app' docker-compose.yml 2>/dev/null || sed -i '/container_name: amrs-maintenance-tracker/a\    hostname: app' docker-compose.yml
        sed -i'.tmp' '/container_name: amrs-nginx/a\    hostname: nginx' docker-compose.yml 2>/dev/null || sed -i '/container_name: amrs-nginx/a\    hostname: nginx' docker-compose.yml
    fi
    
    echo -e "${GREEN}✓ Modified docker-compose.yml to use root user temporarily${NC}"
else
    echo -e "${YELLOW}! docker-compose.yml not found${NC}"
fi
echo

echo -e "${BOLD}6. Stopping and recreating containers...${NC}"
docker-compose down
docker-compose up -d
echo -e "${GREEN}✓ Containers recreated${NC}"
echo

echo -e "${BOLD}7. Applying hosts file fix to containers...${NC}"
# Execute the hosts fix in both containers
docker exec amrs-maintenance-tracker bash -c "echo '127.0.0.1 app amrs-maintenance-tracker' >> /etc/hosts"
docker exec amrs-maintenance-tracker bash -c "ping -c 1 nginx || ping -c 1 amrs-nginx || echo nginx >> /etc/hosts"
docker exec amrs-nginx bash -c "echo '127.0.0.1 nginx amrs-nginx' >> /etc/hosts"
docker exec amrs-nginx bash -c "ping -c 1 app || ping -c 1 amrs-maintenance-tracker || echo app >> /etc/hosts"

echo -e "${GREEN}✓ Applied hosts fixes to containers${NC}"
echo

echo -e "${BOLD}8. Testing connectivity...${NC}"
echo "Testing app -> nginx connectivity:"
docker exec amrs-maintenance-tracker ping -c 1 nginx
echo "Testing nginx -> app connectivity:"
docker exec amrs-nginx ping -c 1 app
echo "Testing app health endpoint:"
docker exec amrs-maintenance-tracker curl -s http://localhost:9000/api/health
echo

echo -e "${GREEN}${BOLD}Network and permission fixes completed!${NC}"
echo "The system should now have proper networking between containers"
echo "and file permissions have been corrected."
echo
echo "Important: This script temporarily runs the containers as root for"
echo "troubleshooting. Once everything is working, you may want to revert"
echo "to a non-root user by editing docker-compose.yml:"
echo "user: \"1000:1000\""
echo
echo "Check the application is working properly by visiting:"
echo "http://localhost:8080"
