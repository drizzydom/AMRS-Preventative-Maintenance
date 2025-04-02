#!/bin/bash
# =============================================================================
# AMRS Common Fixes Installer
# This script applies various fixes for common issues with AMRS
# =============================================================================

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BOLD}AMRS Common Fixes Installer${NC}"
echo "=========================="
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

# Fix 1: Create error handling page for 502 gateway errors
echo -e "${BOLD}1. Applying fix for 502 gateway errors...${NC}"
NGINX_CONF_DIR="$DATA_DIR/nginx/conf.d"
mkdir -p "$NGINX_CONF_DIR"

# Check if nginx config exists first
if [ -f "$NGINX_CONF_DIR/default.conf" ]; then
    # Make a backup
    cp "$NGINX_CONF_DIR/default.conf" "$NGINX_CONF_DIR/default.conf.bak"
    
    # Check if the error page already exists
    if grep -q "error_page 502" "$NGINX_CONF_DIR/default.conf"; then
        echo -e "${GREEN}✓ 502 error page already configured${NC}"
    else
        # Add error page configuration
        sed -i '/location \/ {/a \        error_page 502 504 /502.html;' "$NGINX_CONF_DIR/default.conf"
        
        # Add custom error page location block
        cat >> "$NGINX_CONF_DIR/default.conf" << 'EOL'

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
EOL
        echo -e "${GREEN}✓ Added 502 error page configuration${NC}"
    fi
else
    echo -e "${YELLOW}! Nginx configuration not found, skipping 502 error page fix${NC}"
    echo "This fix will be applied when the nginx configuration is created."
fi

# Fix 2: Create simple healthcheck script for troubleshooting
echo -e "${BOLD}2. Creating healthcheck script...${NC}"
cat > "$DATA_DIR/healthcheck.sh" << 'EOL'
#!/bin/bash
# AMRS System Health Check Script

echo "AMRS System Health Check"
echo "======================="
echo

# Check if containers are running
echo "Checking container status..."
if docker ps | grep -q amrs-maintenance-tracker; then
    echo "✓ App container is running"
else
    echo "✗ App container is not running"
fi

if docker ps | grep -q nginx; then
    echo "✓ Nginx container is running"
else
    echo "✗ Nginx container is not running"
fi

echo
echo "Checking application health endpoint..."
curl -s http://localhost:9000/api/health || echo "Failed to connect to application"

echo
echo "Checking database..."
docker exec -it amrs-maintenance-tracker bash -c 'sqlite3 /app/data/app.db .tables' || echo "Failed to check database"

echo
echo "Recent container logs:"
docker logs --tail 10 amrs-maintenance-tracker

echo
echo "Health check complete."
EOL

chmod +x "$DATA_DIR/healthcheck.sh"
echo -e "${GREEN}✓ Healthcheck script created${NC}"

# Fix 3: Create database verification and repair script
echo -e "${BOLD}3. Creating database verification script...${NC}"
cat > "$DATA_DIR/verify_db.py" << 'EOL'
#!/usr/bin/env python3
"""
Database verification and repair script for AMRS
"""
import os
import sqlite3
import sys
from datetime import datetime

try:
    from werkzeug.security import generate_password_hash
except ImportError:
    def generate_password_hash(password):
        return f"hash_{password}"

def verify_and_repair_db():
    """Verify database integrity and repair if needed"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
    data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'app.db')
    
    # Check both possible locations
    if os.path.exists(db_path):
        print(f"Found database at {db_path}")
        target_db = db_path
    elif os.path.exists(data_path):
        print(f"Found database at {data_path}")
        target_db = data_path
    else:
        print("Database not found, creating a new one...")
        # Prefer data subdirectory if it exists
        if os.path.exists(os.path.dirname(data_path)):
            target_db = data_path
        else:
            target_db = db_path
    
    try:
        # Connect to database
        conn = sqlite3.connect(target_db)
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Found tables: {', '.join(tables)}")
        
        required_tables = ['user', 'site', 'machine', 'part', 'maintenance_record']
        missing_tables = []
        
        # Check for missing tables
        for table in required_tables:
            if table not in tables:
                missing_tables.append(table)
        
        if missing_tables:
            print(f"Missing tables: {', '.join(missing_tables)}")
            print("Repairing database structure...")
            
            # Create missing tables
            if 'user' not in tables:
                cursor.execute('''
                CREATE TABLE user (
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
                print("Created user table")
            
            if 'site' not in tables:
                cursor.execute('''
                CREATE TABLE site (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    location TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')
                print("Created site table")
            
            if 'machine' not in tables:
                cursor.execute('''
                CREATE TABLE machine (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    site_id INTEGER NOT NULL,
                    model TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (site_id) REFERENCES site (id)
                )
                ''')
                print("Created machine table")
            
            if 'part' not in tables:
                cursor.execute('''
                CREATE TABLE part (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    machine_id INTEGER NOT NULL,
                    maintenance_interval INTEGER,
                    last_maintenance TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (machine_id) REFERENCES machine (id)
                )
                ''')
                print("Created part table")
            
            if 'maintenance_record' not in tables:
                cursor.execute('''
                CREATE TABLE maintenance_record (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    part_id INTEGER NOT NULL,
                    user_id INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (part_id) REFERENCES part (id),
                    FOREIGN KEY (user_id) REFERENCES user (id)
                )
                ''')
                print("Created maintenance_record table")
        
        # Check for admin user
        if 'user' in tables:
            cursor.execute("SELECT COUNT(*) FROM user WHERE username = 'techsupport'")
            if cursor.fetchone()[0] == 0:
                print("Admin user not found, creating...")
                cursor.execute(
                    "INSERT INTO user (username, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
                    ("techsupport", "techsupport@amrs-maintenance.com", generate_password_hash("Sm@rty123"), "admin", datetime.now())
                )
                print("Admin user created")
            else:
                print("Admin user exists")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        # Set proper permissions
        try:
            os.chmod(target_db, 0o666)
            print(f"Set permissions on {target_db}")
        except:
            print("Warning: Could not set database file permissions")
        
        print("Database verification and repair completed successfully")
        return True
        
    except Exception as e:
        print(f"Error verifying database: {e}")
        return False

if __name__ == "__main__":
    if verify_and_repair_db():
        sys.exit(0)
    else:
        sys.exit(1)
EOL

chmod +x "$DATA_DIR/verify_db.py"
echo -e "${GREEN}✓ Database verification script created${NC}"

# Fix 4: Create minimal Flask app for testing
echo -e "${BOLD}4. Creating minimal Flask test app...${NC}"
cat > "$DATA_DIR/minimal_app.py" << 'EOL'
#!/usr/bin/env python3
"""
Minimal Flask application for testing Docker/nginx setup without dependencies
"""
import os
from datetime import datetime

# Create a minimal Flask-like application that doesnt require dependencies
def simple_app(environ, start_response):
    """WSGI application function"""
    path = environ.get('PATH_INFO', '').lstrip('/')
    
    if path == '' or path == 'index':
        # Index page
        response_body = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>AMRS Test Page</title>
            <style>
                body { font-family: Arial; margin: 40px; line-height: 1.6; color: #333; }
                header { background: #f4f4f4; padding: 20px; border-bottom: 1px solid #ddd; }
                .content { padding: 20px 0; }
                .success { color: green; }
            </style>
        </head>
        <body>
            <header>
                <h1>AMRS Maintenance Tracker</h1>
            </header>
            <div class="content">
                <h2>Test Page</h2>
                <p class="success">✓ Application is running!</p>
                <p>Current time: {time}</p>
                <p>This is a minimal test page to verify the container is working.</p>
                <div>
                    <a href="/api/health">Check API health</a>
                </div>
            </div>
        </body>
        </html>
        '''.format(time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        status = '200 OK'
        headers = [('Content-Type', 'text/html')]
    
    elif path == 'api/health':
        # Health check endpoint
        response_body = '{"status": "ok", "message": "Service is operational"}'
        status = '200 OK'
        headers = [('Content-Type', 'application/json')]
    
    else:
        # 404 page
        response_body = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>404 - Page Not Found</title>
            <style>
                body { font-family: Arial; margin: 40px; text-align: center; }
                h1 { color: #d9534f; }
            </style>
        </head>
        <body>
            <h1>404 - Page Not Found</h1>
            <p>The page you're looking for doesn't exist.</p>
            <a href="/">Go back home</a>
        </body>
        </html>
        '''
        status = '404 Not Found'
        headers = [('Content-Type', 'text/html')]
    
    start_response(status, headers)
    return [response_body.encode('utf-8')]

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 9000))
    
    # Create and run the server
    httpd = make_server('0.0.0.0', port, simple_app)
    print(f"Serving minimal test app on port {port}...")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Server stopped")
EOL

chmod +x "$DATA_DIR/minimal_app.py"
echo -e "${GREEN}✓ Minimal test app created${NC}"

# Fix 5: Create helper script for common Docker commands
echo -e "${BOLD}5. Creating Docker helper script...${NC}"
cat > "$DATA_DIR/docker_helper.sh" << 'EOL'
#!/bin/bash
# Docker Helper Script for AMRS

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BOLD}AMRS Docker Helper${NC}"
echo "================="
echo
echo "Select an action:"
echo "1. View container status"
echo "2. View container logs"
echo "3. Restart containers"
echo "4. Fix database permissions"
echo "5. Run minimal test app"
echo "6. Back up database"
echo "7. Verify network connections"
echo "8. Exit"
echo

read -p "Enter your choice (1-8): " choice

case $choice in
    1)
        echo "Container Status:"
        docker ps -a | grep -E "amrs|nginx"
        ;;
    2)
        echo "Which container logs do you want to see?"
        echo "1. App (amrs-maintenance-tracker)"
        echo "2. Nginx"
        read -p "Enter choice (1-2): " log_choice
        
        if [ "$log_choice" = "1" ]; then
            docker logs amrs-maintenance-tracker
        elif [ "$log_choice" = "2" ]; then
            docker logs amrs-nginx || docker logs $(docker ps -a | grep nginx | awk '{print $1}')
        else
            echo "Invalid choice"
        fi
        ;;
    3)
        echo "Restarting containers..."
        docker restart amrs-maintenance-tracker
        docker restart amrs-nginx || docker restart $(docker ps -a | grep nginx | awk '{print $1}')
        echo "Containers restarted"
        ;;
    4)
        echo "Fixing database permissions..."
        docker exec amrs-maintenance-tracker bash -c 'chmod 666 /app/data/app.db || true; chmod 666 /app/app.db || true'
        echo "Done"
        ;;
    5)
        echo "Running minimal test app..."
        echo "This will stop the current app container and run a minimal test app instead."
        read -p "Continue? (y/n): " confirm
        
        if [ "$confirm" = "y" ]; then
            # Stop the current app container
            docker stop amrs-maintenance-tracker
            
            # Run minimal app
            echo "Starting minimal app container..."
            docker run --rm -d --name amrs-test-app \
              -v $(dirname "$0"):/app/data \
              -p 9000:9000 \
              python:3.9-slim \
              python /app/data/minimal_app.py
              
            echo "Minimal app started on port 9000"
            echo "To stop it and restore the regular container, press Ctrl+C"
            sleep 2
            
            # Wait for user to stop
            read -p "Press Enter to stop the minimal app and restore regular container..."
            
            # Stop minimal app
            docker stop amrs-test-app
            
            # Restart regular container
            docker start amrs-maintenance-tracker
            echo "Regular container restored"
        else
            echo "Operation cancelled"
        fi
        ;;
    6)
        echo "Backing up database..."
        BACKUP_FILE="app_db_backup_$(date +%Y%m%d_%H%M%S).db"
        if docker exec amrs-maintenance-tracker bash -c 'cat /app/data/app.db' > "$BACKUP_FILE"; then
            echo "Database backed up to: $BACKUP_FILE"
        else
            echo "Failed to back up from /app/data/app.db, trying alternative path..."
            if docker exec amrs-maintenance-tracker bash -c 'cat /app/app.db' > "$BACKUP_FILE"; then
                echo "Database backed up to: $BACKUP_FILE"
            else
                echo "Failed to back up database"
            fi
        fi
        ;;
    7)
        echo "Verifying network connections..."
        echo "Testing connection from app to nginx..."
        docker exec amrs-maintenance-tracker bash -c 'ping -c 3 nginx || ping -c 3 amrs-nginx'
        
        echo "Testing connection from nginx to app..."
        docker exec $(docker ps -a | grep nginx | awk '{print $1}') bash -c 'ping -c 3 amrs-maintenance-tracker || ping -c 3 app'
        
        echo "Testing API connection..."
        docker exec $(docker ps -a | grep nginx | awk '{print $1}') bash -c 'wget -q -O- http://amrs-maintenance-tracker:9000/api/health || wget -q -O- http://app:9000/api/health'
        ;;
    8)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice"
        ;;
esac
EOL

chmod +x "$DATA_DIR/docker_helper.sh"
echo -e "${GREEN}✓ Docker helper script created${NC}"

# Fix extended timeout in Nginx configuration
echo -e "${BOLD}6. Applying extended timeout fix for Nginx...${NC}"
if [ -f "$NGINX_CONF_DIR/default.conf" ]; then
    if ! grep -q "proxy_connect_timeout" "$NGINX_CONF_DIR/default.conf"; then
        # Add timeout settings
        sed -i '/location \/ {/a \        proxy_connect_timeout 300s;\n        proxy_send_timeout 300s;\n        proxy_read_timeout 300s;' "$NGINX_CONF_DIR/default.conf"
        echo -e "${GREEN}✓ Extended timeout settings added to Nginx configuration${NC}"
    else
        echo -e "${GREEN}✓ Extended timeout settings already present${NC}"
    fi
else
    echo -e "${YELLOW}! Nginx configuration not found, skipping timeout fix${NC}"
    echo "This fix will be applied when the nginx configuration is created."
fi

# Fix 6: Create check for hostname resolution
echo -e "${BOLD}7. Creating hostname resolution check script...${NC}"
cat > "$DATA_DIR/check_hostname.sh" << 'EOL'
#!/bin/bash
# Check hostname resolution between containers

# Function to check if containers can resolve each other
check_hostname() {
    echo "Testing hostname resolution between containers..."
    
    # Check if app container can resolve nginx
    echo "From app container to nginx:"
    docker exec amrs-maintenance-tracker bash -c 'getent hosts nginx || getent hosts amrs-nginx || echo "Cannot resolve nginx"'
    
    # Check if nginx container can resolve app
    echo "From nginx container to app:"
    NGINX_CONTAINER=$(docker ps -qf "name=nginx")
    if [ -n "$NGINX_CONTAINER" ]; then
        docker exec $NGINX_CONTAINER bash -c 'getent hosts app || getent hosts amrs-maintenance-tracker || echo "Cannot resolve app"'
    else
        echo "Nginx container not running"
    fi
}

# Check hostname resolution
check_hostname

echo "If hostnames cannot be resolved, modify /etc/hosts inside each container:"
echo "docker exec -it CONTAINER_NAME bash -c 'echo \"172.17.0.X  container_name\" >> /etc/hosts'"
EOL

chmod +x "$DATA_DIR/check_hostname.sh"
echo -e "${GREEN}✓ Hostname resolution check script created${NC}"

echo
echo -e "${GREEN}${BOLD}Common fixes installation completed!${NC}"
echo "All fixes and troubleshooting scripts have been installed."
