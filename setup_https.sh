#!/bin/bash

# Install Certbot (on Ubuntu/Debian)
sudo apt update
sudo apt install certbot

# Get certificate (replace with your domain)
sudo certbot certonly --standalone -d your-domain.com

# Update docker-compose.yml to mount certificates
echo "
Add these lines to your docker-compose.yml:

volumes:
  - /etc/letsencrypt/live/your-domain.com/fullchain.pem:/app/certs/fullchain.pem:ro
  - /etc/letsencrypt/live/your-domain.com/privkey.pem:/app/certs/privkey.pem:ro
"
