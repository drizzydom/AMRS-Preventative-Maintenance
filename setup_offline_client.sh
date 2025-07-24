#!/bin/bash
# Example sync configuration for offline client testing
# Copy this to a file like 'setup_offline_client.sh' and modify the URLs/credentials

# Set these environment variables for offline client mode:
export AMRS_ONLINE_URL="https://your-render-app.onrender.com"
export AMRS_ADMIN_USERNAME="your_admin_username"
export AMRS_ADMIN_PASSWORD="your_admin_password"

# Optionally set a different database path for testing
export DATABASE_URL="sqlite:///offline_client_test.db"

echo "Environment configured for offline client mode"
echo "AMRS_ONLINE_URL: $AMRS_ONLINE_URL"
echo "AMRS_ADMIN_USERNAME: $AMRS_ADMIN_USERNAME" 
echo "DATABASE_URL: $DATABASE_URL"

# Now run the app:
# python3 app.py
