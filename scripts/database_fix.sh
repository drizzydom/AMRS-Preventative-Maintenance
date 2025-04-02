#!/bin/bash
# =============================================================================
# AMRS Database Fix Script
# This script fixes SQLite database access issues
# =============================================================================

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BOLD}AMRS Database Fix Script${NC}"
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

echo -e "${BOLD}1. Stopping containers to release any database locks...${NC}"
docker-compose down 2>/dev/null || docker stop $(docker ps -f name=amrs -q) 2>/dev/null
echo -e "${GREEN}✓ Containers stopped (if running)${NC}"
echo

echo -e "${BOLD}2. Creating a backup of existing database...${NC}"
DB_PATH="$DATA_DIR/data/app.db"
ALT_DB_PATH="$DATA_DIR/app.db"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$DATA_DIR/backup"
mkdir -p "$BACKUP_DIR"

if [ -f "$DB_PATH" ]; then
    cp "$DB_PATH" "$BACKUP_DIR/app.db_backup_$TIMESTAMP"
    echo -e "${GREEN}✓ Database backup created at $BACKUP_DIR/app.db_backup_$TIMESTAMP${NC}"
elif [ -f "$ALT_DB_PATH" ]; then
    cp "$ALT_DB_PATH" "$BACKUP_DIR/app.db_backup_$TIMESTAMP"
    echo -e "${GREEN}✓ Database backup created at $BACKUP_DIR/app.db_backup_$TIMESTAMP${NC}"
else
    echo -e "${YELLOW}! No existing database found to backup${NC}"
fi
echo

echo -e "${BOLD}3. Fixing directory permissions...${NC}"
# Fix data directory permissions
mkdir -p "$DATA_DIR/data"
chmod -R 777 "$DATA_DIR"
chmod -R 777 "$DATA_DIR/data"
echo -e "${GREEN}✓ Set directory permissions to 777${NC}"
echo

echo -e "${BOLD}4. Recreating database files with proper permissions...${NC}"
# Create empty database files with proper permissions
touch "$DATA_DIR/data/app.db"
touch "$DATA_DIR/app.db"  # Alternative location
chmod 666 "$DATA_DIR/data/app.db" "$DATA_DIR/app.db"
echo -e "${GREEN}✓ Created database files with 666 permissions${NC}"
echo

echo -e "${BOLD}5. Re-initializing database...${NC}"
# Create a minimal database schema
cat > "$DATA_DIR/emergency_db_init.py" << 'EOL'
#!/usr/bin/env python3
"""Emergency database initialization"""
import sqlite3
import os
import sys

def init_db():
    """Create minimal database structure"""
    # Try both possible locations
    db_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'app.db'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
    ]
    
    success = False
    
    for db_path in db_paths:
        try:
            print(f"Trying to initialize database at {db_path}")
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            # Connect and create tables
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create minimal table structure
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user'
            )
            ''')
            
            # Add admin user
            cursor.execute("SELECT COUNT(*) FROM user WHERE username = 'techsupport'")
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO user (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
                    ("techsupport", "techsupport@amrs-maintenance.com", "password_hash_here", "admin")
                )
            
            conn.commit()
            conn.close()
            
            # Set permissions
            os.chmod(db_path, 0o666)
            print(f"Successfully created database at {db_path}")
            success = True
            
        except Exception as e:
            print(f"Failed to initialize at {db_path}: {e}")
    
    return success

if __name__ == "__main__":
    if init_db():
        print("Database initialization successful")
        sys.exit(0)
    else:
        print("Database initialization failed")
        sys.exit(1)
EOL

chmod +x "$DATA_DIR/emergency_db_init.py"

# Try to run the script
if command -v python3 &>/dev/null; then
    python3 "$DATA_DIR/emergency_db_init.py"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Database initialized successfully${NC}"
    else
        echo -e "${RED}✗ Python database initialization failed${NC}"
        # Try with SQLite directly
        echo "Attempting direct SQLite initialization..."
        if command -v sqlite3 &>/dev/null; then
            sqlite3 "$DATA_DIR/data/app.db" "CREATE TABLE IF NOT EXISTS user (id INTEGER PRIMARY KEY, username TEXT, email TEXT, password_hash TEXT); INSERT OR IGNORE INTO user VALUES (1, 'techsupport', 'admin@example.com', 'password_hash_here');"
            echo -e "${GREEN}✓ SQLite initialization done${NC}"
        else
            echo -e "${RED}✗ SQLite not found, cannot initialize database${NC}"
        fi
    fi
else
    echo -e "${YELLOW}! Python3 not found, using direct Docker method${NC}"
    # Try using Docker to initialize the database
    docker run --rm -v "$DATA_DIR:/data" python:3.9-slim python3 -c "
import sqlite3
import os
conn = sqlite3.connect('/data/data/app.db')
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS user (id INTEGER PRIMARY KEY, username TEXT, email TEXT, password_hash TEXT)')
cursor.execute('INSERT OR IGNORE INTO user VALUES (1, \"techsupport\", \"admin@example.com\", \"password_hash_here\")')
conn.commit()
conn.close()
print('Database initialized inside Docker')
"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Docker-based initialization successful${NC}"
    else
        echo -e "${RED}✗ Docker-based initialization failed${NC}"
    fi
fi
echo

echo -e "${BOLD}6. Setting ownership...${NC}"
# Try to set correct ownership (requires sudo)
if command -v sudo &>/dev/null; then
    echo "Attempting to set proper ownership (may prompt for sudo password)"
    sudo chown -R 1000:1000 "$DATA_DIR" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Ownership set to 1000:1000${NC}"
    else
        echo -e "${YELLOW}! Could not set ownership (sudo failed)${NC}"
    fi
else
    echo -e "${YELLOW}! Sudo not available, skipping ownership fix${NC}"
fi
echo

echo -e "${BOLD}7. Restarting containers...${NC}"
# Restart containers
cd $(dirname "$DATA_DIR") && docker-compose up -d
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Containers restarted${NC}"
else
    echo -e "${RED}✗ Failed to restart containers${NC}"
fi
echo

echo -e "${GREEN}${BOLD}Database fix completed!${NC}"
echo "If problems persist, try manually accessing the database file:"
echo "1. Connect to the container: docker exec -it amrs-maintenance-tracker bash"
echo "2. Test the database: sqlite3 /app/data/app.db .tables"
