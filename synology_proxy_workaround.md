# Synology Reverse Proxy Workaround

If you're experiencing network errors when saving the reverse proxy configuration, try this alternative approach:

## Method 1: Use IP Address Instead of Hostname

1. Go to **DSM Control Panel** → **Login Portal** → **Advanced** → **Reverse Proxy**
2. Create a new rule using your Synology's **IP address** instead of hostname:
   - **Source:**
     - Protocol: HTTPS
     - Hostname: (leave empty)
     - Port: 443
   - **Destination:**
     - Protocol: HTTP
     - Hostname: localhost
     - Port: 9000

3. Save this configuration first
4. After successfully creating this rule, try adding another one with your hostname

## Method 2: Command Line Configuration

SSH into your Synology and create the configuration file directly:

```bash
# SSH into your Synology
ssh admin@your-synology-ip

# Create Nginx configuration file
sudo mkdir -p /usr/local/etc/nginx/conf.d/
sudo bash -c 'cat > /usr/local/etc/nginx/conf.d/amrs-maintenance.conf << EOL
server {
    listen 443 ssl;
    server_name your-hostname.dscloud.me;
    
    ssl_certificate /etc/ssl/certs/your-certificate.crt;
    ssl_certificate_key /etc/ssl/private/your-key.key;
    
    location / {
        proxy_pass http://localhost:9000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOL'

# Reload Nginx configuration
sudo nginx -s reload
```

## Method 3: Use Docker Container Direct Access

Simplify by removing Nginx and exposing your app container directly:

```yaml
# In your docker-compose.yml
services:
  app:
    ports:
      - "443:9000"  # Map external port 443 directly to container port 9000
    volumes:
      - /path/to/ssl/certs:/app/certs  # Mount SSL certificates
    environment:
      - USE_HTTPS=true                 # Configure app to use HTTPS
```
