#!/bin/bash
# Startup script for ensuring database is ready before starting the app

echo "[STARTUP] Starting application setup..."

# Create data directory if it doesn't exist
if [ ! -d "/var/data" ]; then
    echo "[STARTUP] Creating /var/data directory..."
    mkdir -p /var/data || echo "[ERROR] Failed to create /var/data directory"
fi

# Set proper permissions
echo "[STARTUP] Setting permissions on data directory..."
chmod -R 755 /var/data || echo "[ERROR] Failed to set permissions on /var/data"

# Create backups directory if it doesn't exist
echo "[STARTUP] Creating backups directory..."
mkdir -p /var/data/backups || echo "[ERROR] Failed to create backups directory"
chmod -R 755 /var/data/backups || echo "[ERROR] Failed to set permissions on backups directory"

# Ensure the templates/errors directory exists and is writable
echo "[STARTUP] Ensuring error templates directory exists..."
mkdir -p templates/errors
chmod -R 755 templates/ || echo "[ERROR] Failed to set permissions on templates directory"

# Check if the error templates exist
if [ -f "templates/errors/404.html" ]; then
    echo "[STARTUP] Error templates verified."
else
    echo "[ERROR] Error templates missing. Using fallback error handlers."
fi

# List contents of data directory
echo "[STARTUP] Data directory contents:"
ls -la /var/data || echo "[ERROR] Failed to list /var/data contents"

# Print environment diagnostics
echo "[STARTUP] Environment diagnostics:"
echo "  FLASK_APP: $FLASK_APP"
echo "  SERVER_NAME: $SERVER_NAME"
echo "  APPLICATION_ROOT: $APPLICATION_ROOT"
echo "  PYTHONPATH: $PYTHONPATH"
echo "  Working directory: $(pwd)"
echo "  Directory structure:"
find . -type d -maxdepth 2 | sort

echo "[STARTUP] Starting application server..."
# Start the application with more verbose logging and log access
exec gunicorn app:app --log-level debug --access-logfile - --error-logfile - --capture-output --bind 0.0.0.0:$PORT
