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

# List contents of data directory
echo "[STARTUP] Data directory contents:"
ls -la /var/data || echo "[ERROR] Failed to list /var/data contents"

# Set proper environment variables if not already set
if [ -z "$FLASK_APP" ]; then
    echo "[STARTUP] Setting FLASK_APP environment variable..."
    export FLASK_APP=app.py
fi

# Check if the database file exists
if [ -f "/var/data/maintenance.db" ]; then
    echo "[STARTUP] Database file exists: $(ls -la /var/data/maintenance.db)"
else
    echo "[STARTUP] Database file does not exist yet - will be created on first run"
fi

echo "[STARTUP] Starting application server..."
# Start the application with more verbose logging
exec gunicorn app:app --log-level debug
