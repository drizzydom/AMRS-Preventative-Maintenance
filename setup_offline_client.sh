#!/bin/bash
# AMRS Offline Client Configuration
# Update the values below with your actual Render URL and admin credentials

# CRITICAL: Set these environment variables for offline client mode:
export AMRS_ONLINE_URL="https://your-render-app.onrender.com"  # REPLACE WITH YOUR ACTUAL RENDER URL
export AMRS_ADMIN_USERNAME="your_admin_username"              # REPLACE WITH YOUR ACTUAL ADMIN USERNAME  
export AMRS_ADMIN_PASSWORD="your_admin_password"              # REPLACE WITH YOUR ACTUAL ADMIN PASSWORD

# Ensure this is explicitly NOT the online server
unset RENDER
unset HEROKU  
unset RAILWAY
unset RENDER_EXTERNAL_URL
unset IS_ONLINE_SERVER

# Optionally set a different database path for testing
export DATABASE_URL="sqlite:///offline_client_test.db"

echo "🔧 Environment configured for OFFLINE CLIENT mode"
echo "🌐 Online server URL: $AMRS_ONLINE_URL"
echo "👤 Admin username: $AMRS_ADMIN_USERNAME" 
echo "💾 Database: $DATABASE_URL"
echo ""
echo "⚠️  IMPORTANT: Update the URL and credentials above before use!"
echo "🚀 Now run: python3 app.py"
