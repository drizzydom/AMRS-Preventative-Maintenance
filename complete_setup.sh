#!/bin/bash

# Set your DDNS hostname here
DDNS_HOSTNAME="amrs-maintenance.dscloud.me"
SYNOLOGY_IP="192.168.1.169"  # Replace with your NAS IP

echo "Complete AMRS Maintenance Tracker Setup"
echo "====================================="
echo
echo "DDNS Hostname: $DDNS_HOSTNAME"
echo "Synology IP: $SYNOLOGY_IP"
echo

# 1. Update docker-compose.yml SERVER_NAME
echo "Updating docker-compose.yml with DDNS hostname..."
sed -i "s/SERVER_NAME=.*/SERVER_NAME=$DDNS_HOSTNAME/" docker-compose.yml
sed -i "s/your-ddns-hostname\.synology\.me/$DDNS_HOSTNAME/g" docker-compose.yml

# 2. Update Nginx configuration
echo "Creating Nginx configuration..."
mkdir -p nginx/conf.d
cat > nginx/conf.d/default.conf << EOL
server {
    listen 80;
    server_name $DDNS_HOSTNAME;
    
    # Redirect HTTP to HTTPS
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl;
    server_name $DDNS_HOSTNAME;
    
    # SSL certificates
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    
    # SSL optimizations
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;
    
    # Modern TLS configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    
    # HSTS (comment out if testing)
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    
    # Other security headers
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Proxy the requests to the Flask app
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
echo "Configuration complete!"
echo
echo "Next steps:"
echo
echo "1. Ensure DDNS is configured in Synology DSM:"
echo "   - Control Panel > External Access > DDNS"
echo
echo "2. Setup SSL certificates using Let's Encrypt in Synology DSM:"
echo "   - Control Panel > Security > Certificate"
echo
echo "3. Configure port forwarding in your router:"
echo "   - Forward ports 80 and 443 to your Synology NAS ($SYNOLOGY_IP)"
echo
echo "4. Deploy the application:"
echo "   docker-compose down"
echo "   docker-compose build --no-cache"
echo "   docker-compose up -d"
echo
echo "5. Visit your application at:"
echo "   https://$DDNS_HOSTNAME"
echo
echo "6. Generate a Windows client with your DDNS server URL:"
echo "   cd windows_client"
echo "   python build.py --server-url https://$DDNS_HOSTNAME"
echo
