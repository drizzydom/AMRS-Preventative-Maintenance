#!/bin/bash
# Script to debug and fix the offline browser testing database

# Set colors for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}====================================================${NC}"
echo -e "${BLUE}  AMRS Preventative Maintenance - Database Fix Tool  ${NC}"
echo -e "${BLUE}====================================================${NC}"

# Check if a database file was specified
if [ -n "$1" ]; then
  DB_FILE="$1"
  echo -e "${YELLOW}Using specified database: ${DB_FILE}${NC}"
else
  DB_FILE="maintenance_test.db"
  echo -e "${YELLOW}Using default database: ${DB_FILE}${NC}"
fi

# Export the DB_FILE environment variable for the Python script
export DB_FILE

# Option 1: Run the debug script
echo -e "\n${GREEN}Option 1: Debug and fix database issues${NC}"
read -p "Run the database diagnostic tool? (y/n): " run_debug
if [[ $run_debug == "y" || $run_debug == "Y" ]]; then
  python "$(dirname "$0")/debug_offline_browser.py" "$DB_FILE"
fi

# Option 2: Recreate the database
echo -e "\n${GREEN}Option 2: Recreate the database from scratch${NC}"
read -p "Recreate the database? (y/n): " recreate_db
if [[ $recreate_db == "y" || $recreate_db == "Y" ]]; then
  echo -e "${YELLOW}Recreating database...${NC}"
  export RECREATE_DB=true
  python "$(dirname "$0")/run_offline_app_test.py" --initialize-only
  echo -e "${GREEN}Database recreated successfully.${NC}"
fi

# Option 3: Run the test app
echo -e "\n${GREEN}Option 3: Start the offline test app${NC}"
read -p "Start the offline test app? (y/n): " start_app
if [[ $start_app == "y" || $start_app == "Y" ]]; then
  read -p "Enter port number (default: 8080): " port
  if [ -z "$port" ]; then
    port=8080
  fi
  echo -e "${YELLOW}Starting offline app on port ${port}...${NC}"
  "$(dirname "$0")/test_offline_browser.sh" "$port"
fi

echo -e "\n${GREEN}Done!${NC}"
