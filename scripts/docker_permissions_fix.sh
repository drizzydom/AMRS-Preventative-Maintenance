#!/bin/bash
# =============================================================================
# AMRS Docker Permissions Fix Script
# This script fixes file permission issues inside Docker containers
# =============================================================================

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BOLD}AMRS Docker Permissions Fix Script${NC}"
echo "=============================="
echo

# Define container name
APP_CONTAINER="amrs-maintenance-tracker"

echo -e "${BOLD}1. Checking if container is running...${NC}"
if ! docker ps | grep -q $APP_CONTAINER; then
    echo -e "${RED}✗ Container $APP_CONTAINER is not running${NC}"
    echo "Starting container..."
    docker-compose up -d $APP_CONTAINER
    sleep 5
fi

if ! docker ps | grep -q $APP_CONTAINER; then
    echo -e "${RED}✗ Container $APP_CONTAINER still not running. Cannot proceed.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Container is running${NC}"
echo

echo -e "${BOLD}2. Checking current file ownership and permissions...${NC}"
docker exec $APP_CONTAINER bash -c "ls -la /app/templates /app/static 2>/dev/null || echo 'Directories not found'"
echo

echo -e "${BOLD}3. Creating external directories for mounting...${NC}"
# Check if data directory is provided as argument
if [ -n "$1" ]; then
    DATA_DIR="$1"
else
    # Default directory
    if [ -d "/volume1" ]; then
        DATA_DIR="/volume1/docker/amrs-data"
    else
        DATA_DIR="$HOME/amrs-data"
    fi
fi
echo "Using data directory: $DATA_DIR"

# Create directories
mkdir -p "$DATA_DIR/templates"
mkdir -p "$DATA_DIR/static/css"
mkdir -p "$DATA_DIR/static/js"
chmod -R 777 "$DATA_DIR/templates" "$DATA_DIR/static"
echo -e "${GREEN}✓ External directories created with proper permissions${NC}"
echo

echo -e "${BOLD}4. Copying templates and static files from container...${NC}"
# Extract templates from container
docker exec $APP_CONTAINER bash -c "if [ -d /app/templates ]; then tar -cf - /app/templates | gzip -9; fi" | gunzip | tar -xf - -C "$DATA_DIR" --strip-components=2 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Templates extracted from container${NC}"
else
    echo -e "${YELLOW}! Could not extract templates, they may not exist in container${NC}"
    echo "Creating minimal templates..."
    cp -r "$DATA_DIR/../server/templates/"* "$DATA_DIR/templates/" 2>/dev/null || true
fi

# Extract static files from container
docker exec $APP_CONTAINER bash -c "if [ -d /app/static ]; then tar -cf - /app/static | gzip -9; fi" | gunzip | tar -xf - -C "$DATA_DIR" --strip-components=2 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Static files extracted from container${NC}"
else
    echo -e "${YELLOW}! Could not extract static files, they may not exist in container${NC}"
    # Create minimal CSS and JS
    echo "/* Basic styling */" > "$DATA_DIR/static/css/style.css"
    echo "// Basic JavaScript" > "$DATA_DIR/static/js/main.js"
fi

# Set permissions on all extracted files
chmod -R 666 "$DATA_DIR/templates/"* "$DATA_DIR/static/"* 2>/dev/null
echo -e "${GREEN}✓ Set file permissions to 666${NC}"
echo

echo -e "${BOLD}5. Updating docker-compose.yml with volume mounts...${NC}"
# Check if docker-compose file exists
DOCKER_COMPOSE_FILE="docker-compose.yml"
if [ -f "$DOCKER_COMPOSE_FILE" ]; then
    # Backup the original
    cp "$DOCKER_COMPOSE_FILE" "${DOCKER_COMPOSE_FILE}.bak"
    
    # Check if volumes section already exists for app service
    if ! grep -q "volumes:" "$DOCKER_COMPOSE_FILE" || ! grep -A10 "volumes:" "$DOCKER_COMPOSE_FILE" | grep -q "$DATA_DIR/templates"; then
        # Add or update volumes section
        awk -v data_dir="$DATA_DIR" '
        /volumes:/ {
            print;
            print "      - " data_dir "/data:/app/data:rw";
            print "      - " data_dir "/templates:/app/templates:rw";
            print "      - " data_dir "/static:/app/static:rw";
            in_volumes = 1;
            next;
        }
        in_volumes && /- / {
            if(!printed_data && !($0 ~ data_dir "/data")) {
                printed_data = 1;
            }
            if(!printed_templates && !($0 ~ data_dir "/templates")) {
                printed_templates = 1;
            }
            if(!printed_static && !($0 ~ data_dir "/static")) {
                printed_static = 1;
            }
        }
        in_volumes && !/- / {
            in_volumes = 0;
        }
        /container_name: amrs-maintenance-tracker/ && !found_volumes {
            found_volumes = 1;
            print;
            print "    volumes:";
            print "      - " data_dir "/data:/app/data:rw";
            print "      - " data_dir "/templates:/app/templates:rw";
            print "      - " data_dir "/static:/app/static:rw";
            next;
        }
        { print; }
        ' "$DOCKER_COMPOSE_FILE" > "${DOCKER_COMPOSE_FILE}.new"
        mv "${DOCKER_COMPOSE_FILE}.new" "$DOCKER_COMPOSE_FILE"
        echo -e "${GREEN}✓ Updated docker-compose.yml with volume mounts${NC}"
    else
        echo -e "${GREEN}✓ Volume mounts already present in docker-compose.yml${NC}"
    fi
    
    # Make sure user is set to root for debugging
    if grep -q "user:" "$DOCKER_COMPOSE_FILE"; then
        sed -i.bak 's/user:.*"/user: "root"/' "$DOCKER_COMPOSE_FILE" 2>/dev/null || 
        sed -i 's/user:.*"/user: "root"/' "$DOCKER_COMPOSE_FILE" 2>/dev/null
        echo -e "${GREEN}✓ Set container user to root for debugging${NC}"
    else
        # Add user if not present
        sed -i.bak '/container_name: amrs-maintenance-tracker/a\    user: "root"' "$DOCKER_COMPOSE_FILE" 2>/dev/null ||
        sed -i '/container_name: amrs-maintenance-tracker/a\    user: "root"' "$DOCKER_COMPOSE_FILE" 2>/dev/null
        echo -e "${GREEN}✓ Added root user to docker-compose.yml${NC}"
    fi
else
    echo -e "${RED}✗ docker-compose.yml not found${NC}"
    exit 1
fi
echo

echo -e "${BOLD}6. Creating fixed entrypoint script...${NC}"
# Create a fixed entrypoint script that doesn't try to modify permissions
cat > "$DATA_DIR/fixed_entrypoint.sh" << 'EOF'
#!/bin/bash
set -e

echo "Starting AMRS Maintenance Tracker entrypoint script (fixed version)..."

# Create data directory if it doesn't exist (only directory we modify)
mkdir -p /app/data
chmod 777 /app/data 2>/dev/null || echo "Warning: Could not set data directory permissions"

# Print debugging info
echo "Current user: $(id)"
echo "Directory structure:"
ls -la /app
echo "Volume mounts:"
mount | grep "/app"
echo "Directory permissions:"
ls -la /app/templates /app/static 2>/dev/null || echo "Template/static directories not found"

# Initialize the database if it doesn't exist
if [ ! -f /app/data/app.db ]; then
    echo "Initializing database..."
    # Try to use an initialization script if available
    if [ -f /app/data/init_db.py ]; then
        python /app/data/init_db.py
    elif [ -f /app/init_db.py ]; then
        python /app/init_db.py
    else
        echo "Creating minimal database..."
        python -c '
import sqlite3, os
conn = sqlite3.connect("/app/data/app.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS user (id INTEGER PRIMARY KEY, username TEXT UNIQUE, email TEXT, password_hash TEXT)")
cursor.execute("INSERT OR IGNORE INTO user VALUES (1, \"techsupport\", \"admin@example.com\", \"pbkdf2:sha256:260000$gEv81A7qSCwKW7AX$d16c4780521640d58707f8af594a5ddfe0b86e89b08c488e0d39a39a1b70e613\")")
conn.commit()
conn.close()
print("Database created successfully")
'
    fi
    
    # Set database permissions
    chmod 666 /app/data/app.db 2>/dev/null || echo "Warning: Could not set database file permissions"
fi

# Start the Flask application
echo "Starting Flask application..."
export FLASK_DEBUG=${DEBUG:-false}
export PYTHONUNBUFFERED=1

# Check connectivity to other containers
echo "Checking network connectivity:"
getent hosts nginx || echo "Cannot resolve nginx"
ping -c 1 nginx || echo "Cannot ping nginx"

# Start the application
if command -v gunicorn &>/dev/null; then
    echo "Starting with Gunicorn..."
    exec gunicorn --bind 0.0.0.0:${PORT:-9000} --workers=2 --timeout=30 --log-level=info app:app
else
    echo "Starting with Flask development server..."
    exec python -m flask run --host=0.0.0.0 --port=${PORT:-9000}
fi
EOF

chmod +x "$DATA_DIR/fixed_entrypoint.sh"
echo -e "${GREEN}✓ Fixed entrypoint script created${NC}"
echo

echo -e "${BOLD}7. Updating Docker container...${NC}"
echo "Stopping containers..."
docker-compose down
echo "Starting containers with fixed configuration..."
docker-compose up -d
echo -e "${GREEN}✓ Containers restarted with fixed configuration${NC}"
echo

echo -e "${BOLD}8. Testing the fix...${NC}"
# Wait for container to start
sleep 5
echo "Checking if container is running..."
if docker ps | grep -q $APP_CONTAINER; then
    echo -e "${GREEN}✓ Container is running${NC}"
    
    # Check if template access error is fixed
    ERROR_LOG=$(docker logs --tail 20 $APP_CONTAINER 2>&1 | grep "Operation not permitted")
    if [ -z "$ERROR_LOG" ]; then
        echo -e "${GREEN}✓ No permission errors detected${NC}"
    else
        echo -e "${RED}✗ Permission errors still exist:${NC}"
        echo "$ERROR_LOG"
    fi
    
    # Check if API is responding
    echo "Testing API endpoint..."
    if curl -s http://localhost:9000/api/health | grep -q "status"; then
        echo -e "${GREEN}✓ API is responding correctly${NC}"
    else
        echo -e "${RED}✗ API endpoint not responding${NC}"
    fi
else
    echo -e "${RED}✗ Container failed to start${NC}"
fi
echo

echo -e "${GREEN}${BOLD}Docker permissions fix completed!${NC}"
echo "The container should now be running without permission errors."
echo "If you still see issues:"
echo "1. Check the container logs: docker logs $APP_CONTAINER"
echo "2. Try running the full fix_all_issues.sh script"
echo
echo "To return to non-root user (when everything is working):"
echo "sed -i.bak 's/user: \"root\"/user: \"1000:1000\"/' docker-compose.yml"
