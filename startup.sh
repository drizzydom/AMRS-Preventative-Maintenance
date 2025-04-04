#!/bin/bash
# Startup script for ensuring database is ready before starting the app

# Create data directory if it doesn't exist
mkdir -p /var/data

# Set proper permissions
chmod -R 755 /var/data

# Log startup information
echo "Starting application..."
echo "Data directory: $(ls -la /var/data)"

# Start the application
exec gunicorn app:app
