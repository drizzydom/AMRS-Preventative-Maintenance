#!/bin/bash

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

DATA_DIR=${1:-"/volume1/docker/amrs-data"}
echo -e "${BOLD}Fixing database access issues...${NC}"
echo "Using data directory: $DATA_DIR"

# Step 1: Ensure data directories exist with proper permissions
echo -e "\n${BOLD}Creating necessary directories with proper permissions...${NC}"
mkdir -p "$DATA_DIR"
mkdir -p "$DATA_DIR/instance"
chmod -R 777 "$DATA_DIR"  # Temporarily make fully accessible for debugging
echo -e "${GREEN}✓ Directories created and permissions set${NC}"

# Step 2: Create empty database file to ensure file exists
echo -e "\n${BOLD}Creating initial database file...${NC}"
touch "$DATA_DIR/app.db"
chmod 666 "$DATA_DIR/app.db"
echo -e "${GREEN}✓ Empty database file created${NC}"

# Step 3: Update docker-compose.yml to explicitly create instance directory
echo -e "\n${BOLD}Updating Docker Compose configuration...${NC}"
sed -i.bak 's|- DATABASE_URL=sqlite:///data/app.db|- DATABASE_URL=sqlite:////app/data/app.db|g' docker-compose.yml
echo "Updated DATABASE_URL in docker-compose.yml to use absolute path"

# Step 4: Create a test script to check database access from within the container
cat > "$DATA_DIR/test_db_access.py" << EOL
#!/usr/bin/env python3
import os
import sqlite3
import sys

print("Testing database access...")
print(f"Current directory: {os.getcwd()}")
print(f"Directory contents: {os.listdir('.')}")
print(f"Data directory contents: {os.listdir('/app/data')}")

# Try to open database with relative path
try:
    conn = sqlite3.connect('data/app.db')
    print("✓ Successfully connected to database with relative path")
    conn.close()
except Exception as e:
    print(f"✗ Failed to connect with relative path: {e}")

# Try with absolute path
try:
    conn = sqlite3.connect('/app/data/app.db')
    print("✓ Successfully connected to database with absolute path")
    conn.close()
except Exception as e:
    print(f"✗ Failed to connect with absolute path: {e}")

sys.exit(0)
EOL
chmod +x "$DATA_DIR/test_db_access.py"
echo -e "${GREEN}✓ Database test script created${NC}"

# Step 5: Restart containers
echo -e "\n${BOLD}Restarting Docker containers...${NC}"
docker-compose down
docker-compose up -d
echo -e "${GREEN}✓ Containers restarted${NC}"

# Step 6: Execute test script in container to verify database access
echo -e "\n${BOLD}Testing database access from container...${NC}"
sleep 5  # Give container time to start
docker exec amrs-maintenance-tracker python /app/data/test_db_access.py

echo -e "\n${BOLD}Fix completed!${NC}"
echo "If issues persist, check the logs with: docker logs amrs-maintenance-tracker"
