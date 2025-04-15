#!/bin/bash

# This script creates a symbolic link to make app_render.py accessible as app.py
# for Render.com's default gunicorn command

echo "Creating symbolic link for Render.com deployment..."

# Check if running on Render
if [ "$RENDER" = "true" ]; then
    echo "Running on Render, creating app.py symlink..."
    # Create symlink if it doesn't exist
    if [ ! -L app.py ] && [ -f app_render.py ]; then
        ln -sf app_render.py app.py
        echo "Created symbolic link: app_render.py -> app.py"
    else
        echo "Symlink already exists or app_render.py not found"
    fi
    
    # Check if gunicorn is installed
    if ! command -v gunicorn &> /dev/null; then
        echo "Installing gunicorn..."
        pip install gunicorn==21.2.0
    fi
else
    echo "Not running on Render, skipping symlink creation"
fi

echo "Setup complete"
