#!/bin/bash
# Script to run the offline app for testing in a web browser

# Set default port if not provided
PORT=${1:-8080}

# Check for debug flag
if [ "$1" == "--debug" ]; then
  echo "Running database diagnostics first..."
  python3 "$(dirname "$0")/debug_offline_browser.py"
  
  # Use second argument as port or default to 8080
  PORT=${2:-8080}
fi

# Print information
echo "Starting AMRS Preventative Maintenance offline test on port $PORT"
echo "Access the application at: http://localhost:$PORT"
echo ""

# Run the offline app test script
python3 "$(dirname "$0")/run_offline_app_test.py" $PORT
