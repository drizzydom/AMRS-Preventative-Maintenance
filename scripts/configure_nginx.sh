#!/bin/bash
# =============================================================================
# AMRS Nginx Configuration Script
# This script sets up Nginx as a reverse proxy for the AMRS application
# =============================================================================

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BOLD}AMRS Nginx Configuration${NC}"
echo "======================="
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

# Get application port (default: 9000)
APP_PORT=${2:-9000}
echo "Using application port: $APP_PORT"

# Get external ports (defaults: 8080 for HTTP, 8443 for HTTPS)
HTTP_PORT=${3:-8080}
HTTPS_PORT=${4:-8443}
echo "External HTTP port: $HTTP_PORT"
echo "External HTTPS port: $HTTPS_PORT"

# Create Nginx config directory if it doesn't exist
NGINX_CONFIG_DIR="$DATA_DIR/nginx/conf.d"
mkdir -p "$NGINX_CONFIG_DIR"

echo -e "${BOLD}1. Creating Nginx configuration...${NC}"

# Create a comprehensive Nginx configuration file
cat > "$NGINX_CONFIG_DIR/default.conf" << EOL
server {
    listen 80;
    server_name _;
    
    # Redirect all HTTP to HTTPS
    return 301 https://\$host:\$server_port\$request_uri;
}

server {
    listen 443 ssl;
    server_name _;
    
    # SSL certificates
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    
    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 5m;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options SAMEORIGIN;
    
    # Main proxy configuration
    location / {
        proxy_pass http://app:${APP_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Extended timeouts for slow application startup
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Custom error page with auto-refresh
        error_page 502 504 /502.html;
    }
    
    # Custom error page for 502 Gateway errors
    location = /502.html {
        add_header Content-Type text/html;
        return 502 '
<!DOCTYPE html>
<html>
<head>
    <title>Server Temporarily Unavailable</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body { font-family: Arial, sans-serif; margin: 0 auto; max-width: 600px; padding: 20px; text-align: center; }
        h1 { color: #e74c3c; }
        .spinner { display: inline-block; width: 50px; height: 50px; border: 5px solid rgba(0,0,0,0.1); 
                  border-radius: 50%; border-top-color: #3498db; animation: spin 1s linear infinite; margin-bottom: 20px; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .countdown { margin-top: 20px; color: #666; }
    </style>
    <script>
        window.onload = function() {
            var seconds = 5;
            var countdown = document.getElementById("countdown");
            setInterval(function() {
                seconds--;
                countdown.textContent = seconds;
                if (seconds <= 0) location.reload();
            }, 1000);
        }
    </script>
</head>
<body>
    <div class="spinner"></div>
    <h1>Server Temporarily Unavailable</h1>
    <p>The application server is starting up. This page will refresh in <span id="countdown">5</span> seconds.</p>
    <div class="countdown">The application may take up to 30 seconds to initialize.</div>
</body>
</html>
        ';
    }
    
    # Health check endpoint
    location = /api/health {
        proxy_pass http://app:${APP_PORT}/api/health;
        proxy_set_header Host \$host;
    }
    
    # Static files
    location /static/ {
        proxy_pass http://app:${APP_PORT}/static/;
        proxy_set_header Host \$host;
        add_header Cache-Control "public, max-age=3600";
    }
    
    # SSL info page
    location = /ssl-info {
        proxy_pass http://app:${APP_PORT}/ssl-info;
        proxy_set_header Host \$host;
    }
}
EOL

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Nginx configuration created successfully${NC}"
else
    echo -e "${RED}✗ Failed to create Nginx configuration${NC}"
    exit 1
fi

# Verify the configuration structure
echo -e "${BOLD}2. Verifying configuration structure...${NC}"
if [ -f "$NGINX_CONFIG_DIR/default.conf" ]; then
    echo -e "${GREEN}✓ Configuration file exists${NC}"
    
    # Basic syntax check (we can't fully verify without nginx binary)
    if grep -q "listen 443 ssl" "$NGINX_CONFIG_DIR/default.conf" && \
       grep -q "proxy_pass http://app:${APP_PORT}" "$NGINX_CONFIG_DIR/default.conf"; then
        echo -e "${GREEN}✓ Configuration contains expected directives${NC}"
    else
        echo -e "${RED}✗ Configuration is missing expected directives${NC}"
    fi
else
    echo -e "${RED}✗ Configuration file not found${NC}"
    exit 1
fi

# Create an SSL info page in the templates directory
echo -e "${BOLD}3. Creating SSL info page...${NC}"
mkdir -p "$DATA_DIR/templates"
cat > "$DATA_DIR/templates/ssl_info.html" << 'EOL'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>About SSL Certificate Warning</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            max-width: 800px;
            margin: 0 auto;
            color: #333;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }
        .card {
            background: #f8f9fa;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin-bottom: 20px;
        }
        .warning {
            border-left-color: #e74c3c;
        }
        .steps {
            background: #f1f9ff;
            padding: 15px;
            border-radius: 4px;
        }
        .steps h3 {
            margin-top: 0;
        }
    </style>
</head>
<body>
    <h1>About the SSL Certificate Warning</h1>
    
    <div class="card">
        <p>You're seeing a certificate warning because this system is using a self-signed certificate.
        This is expected and doesn't mean the site is unsafe - it just means the certificate wasn't issued
        by a globally trusted Certificate Authority.</p>
    </div>
    
    <h2>Why am I seeing this warning?</h2>
    <p>When you access a website with HTTPS, your browser verifies that its SSL certificate was issued by a trusted 
    Certificate Authority (CA). Self-signed certificates are created locally and not issued by a trusted CA,
    so browsers display a warning.</p>
    
    <div class="card warning">
        <p><strong>Important:</strong> You're seeing this warning because you're accessing an internal system.
        For internet-facing production systems, we recommend using a proper certificate from Let's Encrypt or another certificate authority.</p>
    </div>
    
    <h2>How to proceed safely</h2>
    
    <div class="steps">
        <h3>Google Chrome</h3>
        <ol>
            <li>Click on "Advanced"</li>
            <li>Click on "Proceed to [site] (unsafe)"</li>
        </ol>
        
        <h3>Mozilla Firefox</h3>
        <ol>
            <li>Click on "Advanced"</li>
            <li>Click on "Accept the Risk and Continue"</li>
        </ol>
        
        <h3>Microsoft Edge</h3>
        <ol>
            <li>Click on "Advanced"</li>
            <li>Click on "Continue to [site] (unsafe)"</li>
        </ol>
        
        <h3>Apple Safari</h3>
        <ol>
            <li>Click on "Show Details"</li>
            <li>Click on "visit this website"</li>
            <li>Click "Visit Website" in the confirmation dialog</li>
        </ol>
    </div>
</body>
</html>
EOL

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ SSL info page created${NC}"
else
    echo -e "${RED}✗ Failed to create SSL info page${NC}"
    # Non-critical error, continue
fi

echo
echo -e "${GREEN}${BOLD}Nginx configuration complete!${NC}"
echo "Configuration is stored in: $NGINX_CONFIG_DIR"
echo "The server is configured to listen on ports $HTTP_PORT (HTTP) and $HTTPS_PORT (HTTPS)"
echo "and proxy requests to the application on port $APP_PORT"
