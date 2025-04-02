#!/bin/bash
# =============================================================================
# AMRS Build and Start Containers Script
# This script builds and starts the Docker containers for the AMRS system
# =============================================================================

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BOLD}AMRS Build and Start Containers${NC}"
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

# Get network name from argument or from temporary file
if [ -n "$2" ]; then
    NETWORK_NAME="$2"
    echo "Using provided network name: $NETWORK_NAME"
elif [ -f /tmp/amrs_network_name ]; then
    NETWORK_NAME=$(cat /tmp/amrs_network_name)
    echo "Using network name from file: $NETWORK_NAME"
else
    NETWORK_NAME="amrs_network_$(date +%s)"
    echo "No network name provided, using generated name: $NETWORK_NAME"
fi

# Get ports from arguments or use defaults
APP_PORT=${3:-9000}
HTTP_PORT=${4:-8080}
HTTPS_PORT=${5:-8443}

echo "Using ports:"
echo "- App port: $APP_PORT"
echo "- HTTP port: $HTTP_PORT"
echo "- HTTPS port: $HTTPS_PORT" 

# Get script directory and project directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BOLD}1. Creating Docker Compose file...${NC}"

# Create docker-compose.yml file
cat > "$PROJECT_DIR/docker-compose.yml" << EOL
version: '3'

services:
  app:
    build: 
      context: ./server
    ports:
      - "$APP_PORT:$APP_PORT"
    environment:
      - SECRET_KEY=secure_$(date +%s)_key
      - DEBUG=true
      - PYTHONUNBUFFERED=1
      - HOST=0.0.0.0
      - PORT=$APP_PORT
      - DATABASE_PATH=/app/data/app.db
      - FLASK_APP=app.py
    volumes:
      - $DATA_DIR:/app/data:rw
    restart: unless-stopped
    user: "1000:1000"
    container_name: amrs-maintenance-tracker
    healthcheck:
      test: ["CMD", "python", "-c", "import os; exit(0 if os.path.exists('/app/data/app.db') or os.access('/app/data', os.W_OK) else 1)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - default

  nginx:
    image: nginx:alpine
    ports:
      - "$HTTP_PORT:80"
      - "$HTTPS_PORT:443"
    volumes:
      - $DATA_DIR/nginx/conf.d:/etc/nginx/conf.d
      - $DATA_DIR/ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped
    container_name: amrs-nginx
    networks:
      - default

networks:
  default:
    name: $NETWORK_NAME
    external: true
EOL

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Docker Compose file created${NC}"
else
    echo -e "${RED}✗ Failed to create Docker Compose file${NC}"
    exit 1
fi

# Create entrypoint script in data directory
echo -e "${BOLD}2. Creating entrypoint script...${NC}"

mkdir -p "$DATA_DIR"
cat > "$DATA_DIR/entrypoint.sh" << 'EOL'
#!/bin/bash
set -e

echo "Starting AMRS Maintenance Tracker entrypoint script..."

# Create necessary directories
mkdir -p /app/data
mkdir -p /app/templates
mkdir -p /app/static

# Copy templates if needed
if [ -d "/app/data/templates" ] && [ "$(ls -A /app/data/templates)" ]; then
    echo "Copying template files from data directory..."
    cp -n /app/data/templates/* /app/templates/ 2>/dev/null || true
fi

# Copy static files if needed
if [ -d "/app/data/static" ] && [ "$(ls -A /app/data/static)" ]; then
    echo "Copying static files from data directory..."
    cp -r /app/data/static/* /app/static/ 2>/dev/null || true
fi

# Initialize the database if it doesn't exist
if [ ! -f /app/data/app.db ]; then
    echo "Initializing database..."
    python /app/data/init_db.py || python /app/init_db.py || {
        echo "Database initialization failed! Creating a minimal database..."
        python - << EOF
import sqlite3
import os
conn = sqlite3.connect('/app/data/app.db')
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS user (id INTEGER PRIMARY KEY, username TEXT, email TEXT, password_hash TEXT)')
cursor.execute('INSERT OR IGNORE INTO user VALUES (1, "techsupport", "admin@example.com", "Sm@rty123")')
conn.commit()
conn.close()
EOF
    }
fi

# Make sure database file has proper permissions
chmod 666 /app/data/app.db 2>/dev/null || true

# Print important diagnostic information
echo "Environment variables:"
env | grep -v PASSWORD
echo "Python version: $(python --version)"
echo "Pip packages:"
pip list

# Start the Flask application
echo "Starting Flask application..."
export FLASK_DEBUG=1
export PYTHONUNBUFFERED=1

# Check for gunicorn vs regular flask
if command -v gunicorn &>/dev/null; then
    echo "Starting with gunicorn..."
    exec gunicorn --bind 0.0.0.0:$PORT --workers=2 --timeout=30 --log-level=info app:app
else
    echo "Starting with Flask development server..."
    exec python -m flask run --host=0.0.0.0 --port=$PORT
fi
EOL

chmod +x "$DATA_DIR/entrypoint.sh"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Entrypoint script created${NC}"
else
    echo -e "${RED}✗ Failed to create entrypoint script${NC}"
    exit 1
fi

# Create database initialization script
echo -e "${BOLD}3. Creating database initialization script...${NC}"

cat > "$DATA_DIR/init_db.py" << 'EOL'
#!/usr/bin/env python3
"""
Database initialization script for AMRS Maintenance Tracker
"""
import os
import sys
import sqlite3
from datetime import datetime

try:
    from werkzeug.security import generate_password_hash
except ImportError:
    # Simple fallback if werkzeug is not available
    def generate_password_hash(password):
        return f"hash_{password}"

DB_PATH = '/app/data/app.db'

def init_db():
    """Initialize the database with required tables and admin user"""
    print(f"Initializing database at {DB_PATH}")
    
    # Ensure database directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    try:
        # Connect to SQLite database (will create if it doesn't exist)
        conn = sqlite3.connect(DB_PATH)
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
        
        # Create site table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS site (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create machine table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS machine (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            site_id INTEGER NOT NULL,
            model TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES site (id)
        )
        ''')
        
        # Create part table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS part (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            machine_id INTEGER NOT NULL,
            maintenance_interval INTEGER,
            last_maintenance TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (machine_id) REFERENCES machine (id)
        )
        ''')
        
        # Create maintenance record table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS maintenance_record (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_id INTEGER NOT NULL,
            user_id INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (part_id) REFERENCES part (id),
            FOREIGN KEY (user_id) REFERENCES user (id)
        )
        ''')
        
        conn.commit()
        print("Tables created successfully")
        
        # Add admin user if it doesn't exist
        cursor.execute("SELECT id FROM user WHERE username = ?", ("techsupport",))
        if not cursor.fetchone():
            print("Creating techsupport admin account...")
            cursor.execute(
                "INSERT INTO user (username, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
                ("techsupport", "techsupport@amrs-maintenance.com", generate_password_hash("Sm@rty123"), "admin", datetime.now())
            )
            conn.commit()
            print("Admin user created")
        else:
            print("Admin user already exists")
        
        # Create sample data if database is empty
        cursor.execute("SELECT COUNT(*) FROM site")
        if cursor.fetchone()[0] == 0:
            print("Adding sample data...")
            
            # Add sites
            cursor.execute("INSERT INTO site (name, location) VALUES (?, ?)", 
                         ("Main Factory", "123 Industrial Ave"))
            site_id = cursor.lastrowid
            
            # Add machines
            cursor.execute("INSERT INTO machine (name, site_id, model) VALUES (?, ?, ?)",
                         ("Pump System A", site_id, "PS-2000"))
            machine_id = cursor.lastrowid
            
            # Add parts
            cursor.execute("INSERT INTO part (name, machine_id, maintenance_interval) VALUES (?, ?, ?)",
                         ("Motor", machine_id, 30))
            
            conn.commit()
            print("Sample data added")
        
        # Set proper permissions
        try:
            os.chmod(DB_PATH, 0o666)  # rw-rw-rw- permissions
            print("Database file permissions set to 666")
        except Exception as e:
            print(f"Warning: Could not set database file permissions: {e}")
        
        conn.close()
        print("Database initialization completed")
        return True
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_db()
    sys.exit(0 if success else 1)
EOL

chmod +x "$DATA_DIR/init_db.py"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Database initialization script created${NC}"
else
    echo -e "${RED}✗ Failed to create database initialization script${NC}"
    exit 1
fi

echo -e "${BOLD}4. Stopping any existing containers...${NC}"
docker-compose -f "$PROJECT_DIR/docker-compose.yml" down --remove-orphans

echo -e "${BOLD}5. Building and starting containers...${NC}"
echo "This may take several minutes..."
docker-compose -f "$PROJECT_DIR/docker-compose.yml" build --no-cache
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Container build failed${NC}"
    echo "Check the error messages above and fix any issues."
    exit 1
fi

echo "Starting containers..."
docker-compose -f "$PROJECT_DIR/docker-compose.yml" up -d
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to start containers${NC}"
    exit 1
fi

# Wait for containers to start
echo "Waiting for containers to start up..."
sleep 10

echo -e "${BOLD}6. Verifying containers are running...${NC}"
if docker ps | grep -q amrs-maintenance-tracker; then
    echo -e "${GREEN}✓ App container is running${NC}"
else
    echo -e "${RED}✗ App container failed to start${NC}"
fi

if docker ps | grep -q amrs-nginx; then
    echo -e "${GREEN}✓ Nginx container is running${NC}"
else
    echo -e "${RED}✗ Nginx container failed to start${NC}"
fi

# Wait a bit longer for Flask to initialize
echo "Waiting for Flask application to initialize..."
sleep 10

# Check if the health endpoint is responding
echo "Testing API health endpoint..."
if curl -s http://localhost:$APP_PORT/api/health | grep -q "status"; then
    echo -e "${GREEN}✓ API is responding correctly${NC}"
else
    echo -e "${YELLOW}! API is not responding yet${NC}"
    echo "This may be normal if the application is still initializing."
    echo "You can check the logs with: docker logs amrs-maintenance-tracker"
fi

echo
echo -e "${GREEN}${BOLD}Build and start completed!${NC}"
echo "Your application should now be available at:"
echo "- Direct Flask access: http://localhost:$APP_PORT"
echo "- Via Nginx: http://localhost:$HTTP_PORT or https://localhost:$HTTPS_PORT"
echo
echo "Default login credentials:"
echo "- Username: techsupport"
echo "- Password: Sm@rty123"
echo
echo "To check logs:"
echo "docker logs amrs-maintenance-tracker"
echo "docker logs amrs-nginx"
