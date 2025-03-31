#!/bin/bash

# Set your DDNS hostname here
DDNS_HOSTNAME="your-ddns-hostname.synology.me"

echo "Setting up DDNS integration for Docker container"
echo "================================================"
echo
echo "DDNS Hostname: $DDNS_HOSTNAME"
echo

# 1. Update docker-compose.yml SERVER_NAME
echo "Updating docker-compose.yml with DDNS hostname..."
sed -i "s/SERVER_NAME=.*/SERVER_NAME=$DDNS_HOSTNAME/" docker-compose.yml

# 2. Update nginx configuration
echo "Updating Nginx configuration..."
mkdir -p nginx/conf.d
cat > nginx/conf.d/default.conf << EOL
server {
    listen 80;
    server_name $DDNS_HOSTNAME;
    
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl;
    server_name $DDNS_HOSTNAME;
    
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    location / {
        proxy_pass http://app:9000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOL

echo
echo "Configuration files updated successfully!"
echo
echo "Next steps:"
echo "1. Make sure DDNS is enabled in your Synology DSM:"
echo "   Control Panel → External Access → DDNS"
echo
echo "2. Set up port forwarding in your router:"
echo "   - Forward ports 80 and 443 to your Synology NAS"
echo
echo "3. Set up SSL certificates:"
echo "   - Either use Synology's built-in Let's Encrypt integration"
echo "   - Or manually place certificates in nginx/certs/ directory"
echo
echo "4. Restart your containers with:"
echo "   docker-compose down && docker-compose up -d"
echo
echo "Once completed, your app should be accessible at: https://$DDNS_HOSTNAME"
