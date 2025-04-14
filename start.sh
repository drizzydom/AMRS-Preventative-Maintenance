#!/bin/bash
# Simple startup script for Render

# Set up directories
echo "Setting up directory structure..."
mkdir -p /var/data/db
mkdir -p /var/data/backups
mkdir -p /var/data/uploads
chmod -R 755 /var/data

# Find gunicorn in various possible locations
GUNICORN_CMD=""
for path in $(which -a gunicorn 2>/dev/null) ~/.local/bin/gunicorn /usr/local/bin/gunicorn /usr/bin/gunicorn; do
  if [ -x "$path" ]; then
    GUNICORN_CMD="$path"
    break
  fi
done

# If gunicorn command not found, try to install it
if [ -z "$GUNICORN_CMD" ]; then
  echo "Gunicorn not found, attempting to install..."
  pip install gunicorn
  GUNICORN_CMD=$(which gunicorn 2>/dev/null || echo "")
fi

# Start the application
if [ -n "$GUNICORN_CMD" ]; then
  echo "Starting application with $GUNICORN_CMD wsgi:app"
  exec $GUNICORN_CMD wsgi:app
else
  echo "ERROR: Could not find or install gunicorn"
  echo "Attempting fallback with python -m gunicorn"
  exec python -m gunicorn wsgi:app
fi
