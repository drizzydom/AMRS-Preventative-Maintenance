#!/bin/bash

# Set your variables
DDNS_HOSTNAME="your-ddns-hostname.synology.me"

echo "=== AMRS Maintenance Simplified Deployment ==="
echo "Using recommended approach with Synology reverse proxy"
echo

# Update the docker-compose file to use only the app container
cat > docker-compose.simple.yml << EOL
version: '3'

services:
  app:
    build: ./server
    ports:
      - "9000:9000"
    environment:
      - DATABASE_URL=sqlite:///data/app.db
      - SECRET_KEY=secure_key_here
      - DEBUG=False
      - PYTHONUNBUFFERED=1
      - HOST=0.0.0.0
      - SERVER_NAME=$DDNS_HOSTNAME
      - PREFERRED_URL_SCHEME=https
    volumes:
      - /volume1/docker/data:/app/data
    restart: "unless-stopped"
    container_name: amrs-maintenance-tracker
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
EOL

echo "Created simplified docker-compose file: docker-compose.simple.yml"
echo 
echo "Next steps:"
echo "1. Configure Synology DSM reverse proxy to forward HTTPS (443) to port 9000"
echo "2. Deploy container with: docker-compose -f docker-compose.simple.yml up -d"
echo "3. Set up DDNS in Control Panel → External Access → DDNS"
echo "4. Set up Let's Encrypt certificate in Control Panel → Security → Certificate"
echo
echo "Your application will be accessible at: https://$DDNS_HOSTNAME"
