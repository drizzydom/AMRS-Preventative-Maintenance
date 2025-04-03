#!/bin/bash
# =============================================================================
# AMRS 502 Error Fix Script
# This script diagnoses and fixes common causes of 502 Gateway errors
# =============================================================================

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BOLD}AMRS 502 Gateway Error Fix Script${NC}"
echo "============================="
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

# Define container names
APP_CONTAINER="amrs-maintenance-tracker"
NGINX_CONTAINER="amrs-nginx"

echo -e "${BOLD}1. Checking container status...${NC}"
if docker ps | grep -q $APP_CONTAINER; then
    echo -e "${GREEN}✓ App container is running${NC}"
    APP_RUNNING=true
else
    echo -e "${RED}✗ App container is not running${NC}"
    APP_RUNNING=false
    
    # Check if it's restarting
    if docker ps -a | grep -q "$APP_CONTAINER.*Restarting"; then
        echo -e "${RED}! App container is crash-looping${NC}"
    fi
fi

if docker ps | grep -q $NGINX_CONTAINER; then
    echo -e "${GREEN}✓ Nginx container is running${NC}"
    NGINX_RUNNING=true
else
    echo -e "${RED}✗ Nginx container is not running${NC}"
    NGINX_RUNNING=false
fi
echo

echo -e "${BOLD}2. Checking app container logs for errors...${NC}"
# Get the last 50 lines from the app container logs
if [ "$APP_RUNNING" = true ]; then
    ERROR_LOG=$(docker logs --tail 50 $APP_CONTAINER 2>&1 | grep -i "error\|exception\|failed\|traceback\|fatal" | grep -v "DEBUG")
    
    if [ -n "$ERROR_LOG" ]; then
        echo -e "${RED}✗ Found errors in app container logs:${NC}"
        echo "$ERROR_LOG"
        
        # Look for common error patterns
        if echo "$ERROR_LOG" | grep -q "database\|sqlite\|db"; then
            DB_ERROR=true
            echo -e "${YELLOW}! Database-related errors detected${NC}"
        fi
        
        if echo "$ERROR_LOG" | grep -q "port\|socket\|bind\|address"; then
            PORT_ERROR=true
            echo -e "${YELLOW}! Port binding issues detected${NC}"
        fi
        
        if echo "$ERROR_LOG" | grep -q "permission\|denied\|access"; then
            PERM_ERROR=true
            echo -e "${YELLOW}! Permission issues detected${NC}"
        fi
    else
        echo -e "${GREEN}✓ No obvious errors in app container logs${NC}"
    fi
else
    echo -e "${YELLOW}! App container not running, can't check logs${NC}"
fi
echo

echo -e "${BOLD}3. Checking network connectivity between containers...${NC}"
if [ "$APP_RUNNING" = true ] && [ "$NGINX_RUNNING" = true ]; then
    # Check if app can reach nginx
    if docker exec $APP_CONTAINER ping -c 1 $NGINX_CONTAINER > /dev/null 2>&1; then
        echo -e "${GREEN}✓ App container can reach Nginx container${NC}"
    else
        echo -e "${RED}✗ App container cannot reach Nginx container${NC}"
        NETWORK_ERROR=true
    fi
    
    # Check if nginx can reach app
    if docker exec $NGINX_CONTAINER ping -c 1 $APP_CONTAINER > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Nginx container can reach App container${NC}"
    else
        echo -e "${RED}✗ Nginx container cannot reach App container${NC}"
        NETWORK_ERROR=true
        
        # Add app container to nginx's hosts file as a workaround
        echo -e "${YELLOW}! Adding app container to Nginx's hosts file...${NC}"
        APP_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $APP_CONTAINER)
        docker exec $NGINX_CONTAINER bash -c "echo '$APP_IP $APP_CONTAINER app' >> /etc/hosts"
    fi
else
    echo -e "${YELLOW}! Both containers need to be running to check connectivity${NC}"
fi
echo

echo -e "${BOLD}4. Testing direct API access...${NC}"
if [ "$APP_RUNNING" = true ]; then
    # Test the API health endpoint directly from the app container
    if docker exec $APP_CONTAINER curl -s http://localhost:9000/api/health > /dev/null; then
        echo -e "${GREEN}✓ API health endpoint is responding inside container${NC}"
    else
        echo -e "${RED}✗ API health endpoint not responding inside container${NC}"
        
        # Check if Flask is listening on the correct address
        LISTENING=$(docker exec $APP_CONTAINER bash -c "netstat -tuln | grep -E ':9000|LISTEN'" 2>/dev/null)
        if [ -z "$LISTENING" ]; then
            echo -e "${RED}✗ Flask app is not listening on port 9000${NC}"
            BIND_ERROR=true
        else
            echo -e "${GREEN}✓ Something is listening on port 9000:${NC}"
            echo "$LISTENING"
        fi
    fi
    
    # Check if Flask app is running
    if docker exec $APP_CONTAINER ps aux | grep -q "[p]ython.*app"; then
        echo -e "${GREEN}✓ Flask process is running${NC}"
    else
        echo -e "${RED}✗ No Flask process found running${NC}"
    fi
else
    echo -e "${YELLOW}! App container not running, can't test API${NC}"
fi
echo

echo -e "${BOLD}5. Checking Nginx configuration...${NC}"
if [ "$NGINX_RUNNING" = true ]; then
    # Check if the target in Nginx config matches the app container name
    TARGET=$(docker exec $NGINX_CONTAINER grep -r "proxy_pass" /etc/nginx/conf.d/ 2>/dev/null | head -1)
    
    if echo "$TARGET" | grep -q "http://app:9000\|http://$APP_CONTAINER:9000"; then
        echo -e "${GREEN}✓ Nginx is configured to proxy to correct target${NC}"
    else
        echo -e "${RED}✗ Nginx proxy_pass may be incorrect:${NC}"
        echo "$TARGET"
        CONFIG_ERROR=true
    fi
    
    # Test nginx config syntax
    if docker exec $NGINX_CONTAINER nginx -t > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Nginx configuration is valid${NC}"
    else
        echo -e "${RED}✗ Nginx configuration has syntax errors${NC}"
        docker exec $NGINX_CONTAINER nginx -t
        CONFIG_ERROR=true
    fi
else
    echo -e "${YELLOW}! Nginx container not running, can't check configuration${NC}"
fi
echo

echo -e "${BOLD}6. Checking database file...${NC}"
DB_FILE="$DATA_DIR/data/app.db"
ALT_DB_FILE="$DATA_DIR/app.db"

if [ -f "$DB_FILE" ]; then
    echo -e "${GREEN}✓ Database file exists at $DB_FILE${NC}"
    
    # Check permissions
    PERMS=$(stat -c "%a" "$DB_FILE" 2>/dev/null || stat -f "%Lp" "$DB_FILE" 2>/dev/null)
    if [ "$PERMS" = "666" ] || [ "$PERMS" = "777" ] || [ "$PERMS" = "644" ]; then
        echo -e "${GREEN}✓ Database has good permissions: $PERMS${NC}"
    else
        echo -e "${RED}✗ Database has restricted permissions: $PERMS${NC}"
        chmod 666 "$DB_FILE"
        echo "Updated database permissions to 666"
    fi
    
    # Check if container can access database
    if [ "$APP_RUNNING" = true ]; then
        if docker exec $APP_CONTAINER bash -c "test -f /app/data/app.db && echo 'DB exists'"; then
            echo -e "${GREEN}✓ App container can access database file${NC}"
        else
            echo -e "${RED}✗ App container cannot access database file${NC}"
            DB_ACCESS=true
        fi
    fi
elif [ -f "$ALT_DB_FILE" ]; then
    echo -e "${YELLOW}! Database file found at alternate location: $ALT_DB_FILE${NC}"
    
    # Create database directory and copy file to correct location
    mkdir -p "$DATA_DIR/data"
    cp "$ALT_DB_FILE" "$DB_FILE"
    chmod 666 "$DB_FILE"
    echo -e "${GREEN}✓ Copied database to correct location with proper permissions${NC}"
else
    echo -e "${RED}✗ Database file not found${NC}"
    DB_MISSING=true
fi
echo

echo -e "${BOLD}7. Applying fixes based on diagnosis...${NC}"

# Fix 1: Database issues
if [ "$DB_ERROR" = true ] || [ "$DB_MISSING" = true ] || [ "$DB_ACCESS" = true ]; then
    echo "Fixing database issues..."
    
    # Ensure directory exists with proper permissions
    mkdir -p "$DATA_DIR/data"
    chmod -R 777 "$DATA_DIR/data"
    
    # If database doesn't exist or is corrupted, create a new one
    if [ "$DB_MISSING" = true ] || [ ! -s "$DB_FILE" ]; then
        echo "Creating minimal database..."
        cat > "$DATA_DIR/data/minimal_db.py" << 'EOF'
#!/usr/bin/env python3
import sqlite3
import os

DB_PATH = '/app/data/app.db'  # This path is inside the container
LOCAL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')  # This is the local path

def create_minimal_db():
    """Create a minimal working database with admin user"""
    try:
        # Connect to database
        conn = sqlite3.connect(LOCAL_PATH)
        cursor = conn.cursor()
        
        # Create user table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            active BOOLEAN NOT NULL DEFAULT 1
        )
        ''')
        
        # Check if admin user exists
        cursor.execute("SELECT COUNT(*) FROM user WHERE username = 'techsupport'")
        if cursor.fetchone()[0] == 0:
            # Add admin user with hashed password equal to "Sm@rty123"
            cursor.execute(
                "INSERT INTO user (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
                ("techsupport", "techsupport@amrs-maintenance.com", 
                 "pbkdf2:sha256:260000$gEv81A7qSCwKW7AX$d16c4780521640d58707f8af594a5ddfe0b86e89b08c488e0d39a39a1b70e613", "admin")
            )
        
        # Create other necessary tables
        cursor.execute('CREATE TABLE IF NOT EXISTS site (id INTEGER PRIMARY KEY, name TEXT, location TEXT)')
        cursor.execute('CREATE TABLE IF NOT EXISTS machine (id INTEGER PRIMARY KEY, name TEXT, site_id INTEGER, model TEXT)')
        cursor.execute('CREATE TABLE IF NOT EXISTS part (id INTEGER PRIMARY KEY, name TEXT, machine_id INTEGER, maintenance_interval INTEGER)')
        cursor.execute('CREATE TABLE IF NOT EXISTS maintenance_record (id INTEGER PRIMARY KEY, part_id INTEGER, user_id INTEGER, timestamp TIMESTAMP, notes TEXT)')
        
        # Commit changes and close
        conn.commit()
        conn.close()
        
        # Set permissions
        os.chmod(LOCAL_PATH, 0o666)
        
        print(f"Database created at {LOCAL_PATH}")
        return True
    except Exception as e:
        print(f"Error creating database: {e}")
        return False

if __name__ == "__main__":
    create_minimal_db()
EOF

        chmod +x "$DATA_DIR/data/minimal_db.py"
        
        # Try to run python script
        if command -v python3 &>/dev/null; then
            cd "$DATA_DIR/data" && python3 minimal_db.py
            echo -e "${GREEN}✓ Created new database file${NC}"
        else
            # Fallback to docker python
            docker run --rm -v "$DATA_DIR/data:/work" -w /work python:3.9-slim python minimal_db.py
            echo -e "${GREEN}✓ Created new database using Docker Python${NC}"
        fi
        
        # Ensure proper permissions
        chmod 666 "$DATA_DIR/data/app.db"
    fi
fi

# Fix 2: Network issues
if [ "$NETWORK_ERROR" = true ]; then
    echo "Fixing network issues..."
    
    # Get current network
    NETWORK=$(docker inspect $APP_CONTAINER -f '{{range $net, $conf := .NetworkSettings.Networks}}{{$net}}{{end}}')
    echo "Current network: $NETWORK"
    
    # Restart containers on the same network
    docker-compose down
    sleep 2
    docker-compose up -d
    echo -e "${GREEN}✓ Restarted containers to fix network issues${NC}"
fi

# Fix 3: Nginx configuration
if [ "$CONFIG_ERROR" = true ]; then
    echo "Fixing Nginx configuration..."
    
    # Create correct configuration
    mkdir -p "$DATA_DIR/nginx/conf.d"
    cat > "$DATA_DIR/nginx/conf.d/default.conf" << EOF
server {
    listen 80;
    server_name _;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl;
    server_name _;
    
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    
    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options SAMEORIGIN;
    
    location / {
        proxy_pass http://$APP_CONTAINER:9000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Extended timeouts for slow application startup
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # Add custom error page
        error_page 502 503 504 /502.html;
    }
    
    # Custom error page
    location = /502.html {
        root /etc/nginx/html;
        internal;
    }
    
    # Health check endpoint
    location = /api/health {
        proxy_pass http://$APP_CONTAINER:9000/api/health;
    }
}
EOF

    # Create 502 error page
    mkdir -p "$DATA_DIR/nginx/html"
    cat > "$DATA_DIR/nginx/html/502.html" << EOF
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
EOF

    # Restart nginx container
    docker-compose restart $NGINX_CONTAINER
    echo -e "${GREEN}✓ Nginx configuration fixed and restarted${NC}"
fi

# Fix 4: Port binding issues
if [ "$BIND_ERROR" = true ]; then
    echo "Fixing port binding issues..."
    
    # Create entrypoint script that ensures binding to 0.0.0.0
    cat > "$DATA_DIR/flask_entrypoint.py" << 'EOF'
#!/usr/bin/env python3
"""
Simplified Flask entrypoint script
"""
import os
import sys

# Always force the host to bind to all interfaces
os.environ["HOST"] = "0.0.0.0"

# Force debug mode off to avoid binding issues
os.environ["DEBUG"] = "False"

# Make app.py importable
sys.path.insert(0, "/app")

try:
    from app import app
    port = int(os.environ.get("PORT", 9000))
    app.run(host="0.0.0.0", port=port)
except Exception as e:
    print(f"Error starting Flask app: {e}")
    sys.exit(1)
EOF

    chmod +x "$DATA_DIR/flask_entrypoint.py"
    echo -e "${GREEN}✓ Created explicit Flask entrypoint script${NC}"
    echo -e "${YELLOW}! You'll need to restart the container for this change to take effect${NC}"
fi

echo
echo -e "${BOLD}8. Restarting containers...${NC}"
docker-compose restart
echo -e "${GREEN}✓ Containers restarted${NC}"

echo
echo -e "${GREEN}${BOLD}Fix attempts completed!${NC}"
echo "Wait approximately 30 seconds, then try accessing the application again."
echo "If the issue persists, try the following additional steps:"
echo "1. Set up a new clean database: ./scripts/database_fix.sh $DATA_DIR"
echo "2. Run the full deployment: ./scripts/master_deployment.sh"
echo

echo -e "${BOLD}Troubleshooting Information:${NC}"
echo "App Container Logs:"
docker logs --tail 10 $APP_CONTAINER 2>&1 | grep -v "DEBUG"
echo
echo "Nginx Container Logs:"
docker logs --tail 5 $NGINX_CONTAINER 2>&1
