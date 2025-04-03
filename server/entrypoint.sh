#!/bin/bash
set -e

echo "Starting AMRS Maintenance Tracker entrypoint script..."

# Create data directory and set permissions (only this directory should be modified)
mkdir -p /app/data
chmod 777 /app/data 2>/dev/null || echo "Warning: Cannot set permissions on data directory"

# Print debugging information
echo "Environment variables:"
env | grep -v PASSWORD
echo "Current user: $(whoami) ($(id -u):$(id -g))"
echo "Directory permissions:"
ls -la /app/
echo "Network connectivity check:"
getent hosts app || echo "Cannot resolve 'app'"
getent hosts nginx || echo "Cannot resolve 'nginx'"

# Initialize the database if it doesn't exist
if [ ! -f /app/data/app.db ]; then
    echo "Initializing database..."
    # Try using the init script from data directory if exists
    if [ -f /app/data/init_db.py ]; then
        echo "Using init_db.py from data directory..."
        python /app/data/init_db.py
    # Otherwise try the included one
    elif [ -f /app/init_db.py ]; then
        echo "Using built-in init_db.py..."
        python /app/init_db.py
    # Last resort, create a minimal database
    else
        echo "Creating minimal database..."
        python -c '
import sqlite3, os
db_path = "/app/data/app.db"
os.makedirs(os.path.dirname(db_path), exist_ok=True)
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS user (id INTEGER PRIMARY KEY, username TEXT UNIQUE, email TEXT, password_hash TEXT, role TEXT)")
cursor.execute("INSERT OR IGNORE INTO user VALUES (1, \"techsupport\", \"admin@example.com\", \"pbkdf2:sha256:260000$gEv81A7qSCwKW7AX$d16c4780521640d58707f8af594a5ddfe0b86e89b08c488e0d39a39a1b70e613\", \"admin\")")
conn.commit()
conn.close()
print("Minimal database created successfully")
'
    fi
    
    # Set database permissions
    chmod 666 /app/data/app.db 2>/dev/null || echo "Warning: Could not set permissions on database file"
fi

# Start the Flask application
echo "Starting Flask application..."
export FLASK_DEBUG=${DEBUG:-0}

# Check for gunicorn vs regular flask
if command -v gunicorn &>/dev/null; then
    echo "Starting with gunicorn..."
    # Explicitly bind to all interfaces (0.0.0.0)
    exec gunicorn --bind 0.0.0.0:$PORT --workers=2 --timeout=30 --log-level=info app:app
else
    echo "Starting with Flask development server..."
    # Explicitly bind to all interfaces (0.0.0.0)
    exec python -m flask run --host=0.0.0.0 --port=$PORT
fi
