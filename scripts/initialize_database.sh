#!/bin/bash
# =============================================================================
# AMRS Database Initialization Script
# This script initializes the SQLite database with required tables and sample data
# =============================================================================

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BOLD}AMRS Database Initialization${NC}"
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

# Create data directory if it doesn't exist
mkdir -p "$DATA_DIR/data"

# Create Python script for database initialization
echo -e "${BOLD}1. Creating database initialization script...${NC}"
DB_INIT_SCRIPT="$DATA_DIR/init_db.py"

cat > "$DB_INIT_SCRIPT" << 'EOL'
#!/usr/bin/env python3
"""
Database initialization script for AMRS Maintenance Tracker
"""
import os
import sys
import sqlite3
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('db_init')

try:
    from werkzeug.security import generate_password_hash
except ImportError:
    # Simple fallback if werkzeug is not available
    def generate_password_hash(password):
        return f"hash_{password}"

# Get database path from environment or use default
DB_PATH = os.environ.get('DATABASE_PATH', '/app/data/app.db')

def init_db():
    """Initialize the database with required tables and admin user"""
    logger.info(f"Initializing database at {DB_PATH}")
    
    # Get the directory path
    db_dir = os.path.dirname(DB_PATH)
    
    # Ensure database directory exists with proper permissions
    try:
        os.makedirs(db_dir, exist_ok=True)
        
        # Output directory permissions for debugging
        dir_stat = os.stat(db_dir)
        logger.info(f"Database directory exists, permissions: {oct(dir_stat.st_mode)}")
        
        # Try to make the directory writable if needed
        if not os.access(db_dir, os.W_OK):
            try:
                os.chmod(db_dir, 0o777)
                logger.info("Updated directory permissions to 777")
            except Exception as e:
                logger.warning(f"Failed to update directory permissions: {e}")
    except Exception as e:
        logger.critical(f"Failed to create database directory: {e}")
        return False
    
    # Try to touch the database file to check if we can write
    try:
        with open(DB_PATH, 'a'):
            pass
        logger.info("Verified database file is writable")
    except Exception as e:
        logger.error(f"Cannot write to database file: {e}")
        try:
            # Last resort: try parent directory
            alt_path = os.path.join(os.path.dirname(db_dir), 'app.db')
            logger.warning(f"Trying alternative path: {alt_path}")
            with open(alt_path, 'a'):
                pass
            DB_PATH = alt_path
        except Exception as e2:
            logger.critical(f"Cannot write to alternative path either: {e2}")
            return False
    
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
        logger.info("Tables created successfully")
        
        # Add admin user if it doesn't exist
        cursor.execute("SELECT id FROM user WHERE username = ?", ("techsupport",))
        if not cursor.fetchone():
            logger.info("Creating techsupport admin account...")
            cursor.execute(
                "INSERT INTO user (username, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
                ("techsupport", "techsupport@amrs-maintenance.com", generate_password_hash("Sm@rty123"), "admin", datetime.now())
            )
            conn.commit()
            logger.info("Admin user created")
        else:
            logger.info("Admin user already exists")
        
        # Create sample data if database is empty
        cursor.execute("SELECT COUNT(*) FROM site")
        if cursor.fetchone()[0] == 0:
            logger.info("Adding sample data...")
            
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
            logger.info("Sample data added")
        
        # Set proper permissions
        try:
            os.chmod(DB_PATH, 0o666)  # rw-rw-rw- permissions
            logger.info("Database file permissions set to 666")
        except Exception as e:
            logger.warning(f"Warning: Could not set database file permissions: {e}")
        
        conn.close()
        logger.info("Database initialization completed successfully")
        return True
        
    except Exception as e:
        logger.critical(f"Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_db()
    sys.exit(0 if success else 1)
EOL

chmod +x "$DB_INIT_SCRIPT"
echo -e "${GREEN}✓ Database initialization script created${NC}"

# Create simple Python script to test database setup without Docker
echo -e "${BOLD}2. Creating local database setup script...${NC}"
LOCAL_DB_SCRIPT="$DATA_DIR/setup_local_db.py"

cat > "$LOCAL_DB_SCRIPT" << 'EOL'
#!/usr/bin/env python3
"""
Local database setup script (no Docker needed)
"""
import os
import sys
import sqlite3
from datetime import datetime

def generate_password_hash(password):
    """Simple password hashing when werkzeug is not available"""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def setup_local_db():
    """Create a local database file with all tables and sample data"""
    # Current directory database path
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
    print(f"Creating local database at {db_path}")
    
    try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create all tables
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
        
        # Add admin user with known password
        cursor.execute("SELECT id FROM user WHERE username = ?", ("techsupport",))
        if not cursor.fetchone():
            print("Creating admin account...")
            cursor.execute(
                "INSERT INTO user (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
                ("techsupport", "techsupport@amrs-maintenance.com", 
                generate_password_hash("Sm@rty123"), "admin")
            )
        
        # Add some sample data
        # Site
        cursor.execute("INSERT INTO site (name, location) VALUES (?, ?)", 
                    ("Main Factory", "123 Industrial Ave"))
        site_id = cursor.lastrowid
        
        # Machines
        cursor.execute("INSERT INTO machine (name, site_id, model) VALUES (?, ?, ?)",
                    ("Pump System A", site_id, "PS-2000"))
        machine_id_1 = cursor.lastrowid
        
        cursor.execute("INSERT INTO machine (name, site_id, model) VALUES (?, ?, ?)",
                    ("Conveyor Belt B", site_id, "CB-1000"))
        machine_id_2 = cursor.lastrowid
        
        # Parts
        cursor.execute("INSERT INTO part (name, machine_id, maintenance_interval) VALUES (?, ?, ?)",
                    ("Motor", machine_id_1, 30))
        part_id_1 = cursor.lastrowid
        
        cursor.execute("INSERT INTO part (name, machine_id, maintenance_interval) VALUES (?, ?, ?)",
                    ("Pump", machine_id_1, 60))
        part_id_2 = cursor.lastrowid
        
        cursor.execute("INSERT INTO part (name, machine_id, maintenance_interval) VALUES (?, ?, ?)",
                    ("Belt", machine_id_2, 45))
        part_id_3 = cursor.lastrowid
        
        # Save changes
        conn.commit()
        conn.close()
        
        # Set file permissions
        try:
            os.chmod(db_path, 0o666)
        except:
            print("Warning: Could not set database file permissions")
        
        print(f"Database created successfully at {db_path}")
        print("Login credentials: techsupport / Sm@rty123")
        return True
        
    except Exception as e:
        print(f"Error setting up database: {e}")
        return False

if __name__ == "__main__":
    if setup_local_db():
        print("Local database setup completed successfully")
        sys.exit(0)
    else:
        print("Local database setup failed")
        sys.exit(1)
EOL

chmod +x "$LOCAL_DB_SCRIPT"
echo -e "${GREEN}✓ Local database setup script created${NC}"

echo -e "${BOLD}3. Setting up initial database...${NC}"
if command -v python3 &>/dev/null; then
    echo "Attempting to create database locally..."
    python3 "$LOCAL_DB_SCRIPT"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Database created locally${NC}"
    else
        echo -e "${YELLOW}! Failed to create database locally${NC}"
        echo "Database will be created when container starts"
    fi
else
    echo -e "${YELLOW}! Python3 not found, database will be created when container starts${NC}"
fi

echo
echo -e "${GREEN}${BOLD}Database initialization setup complete!${NC}"
echo "Database will be created when the container starts"
echo "Default admin login: techsupport / Sm@rty123"
