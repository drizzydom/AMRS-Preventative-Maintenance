# Using Synology's Built-in Reverse Proxy (Recommended)

Since port 443 is reserved for system use on Synology, the best approach is to use Synology's built-in reverse proxy:

## Option 1: Direct Reverse Proxy to App Container

1. Go to **DSM Control Panel** → **Login Portal** → **Advanced** → **Reverse Proxy**
2. Click **Create** and set up:
   - **Source:**
     - Protocol: HTTPS
     - Hostname: your-ddns-hostname.synology.me
     - Port: 443 (default HTTPS port)
   - **Destination:**
     - Protocol: HTTP
     - Hostname: localhost
     - Port: 9000 (your Flask app port)
   
3. Click **OK** to save.

With this configuration, you can:
- Remove the nginx container from your docker-compose.yml
- Keep only the app container running on port 9000

## Option 2: Reverse Proxy to Nginx Container

If you want to keep your Nginx container:

1. Configure Synology reverse proxy:
   - **Source:**
     - Protocol: HTTPS
     - Hostname: your-ddns-hostname.synology.me
     - Port: 443
   - **Destination:**
     - Protocol: HTTP
     - Hostname: localhost
     - Port: 8080 (mapped to Nginx port 80)

2. Keep the modified port mappings in docker-compose.yml:
   ```yaml
   nginx:
     ports:
       - "8080:80"
       - "8443:443"
   ```

## Option 3: Use Different Ports for Your Application

If you prefer to access your application on non-standard ports:

1. Keep the docker-compose.yml with modified port mappings
2. Access your application at:
   - HTTP: http://your-synology-ip:8080
   - HTTPS: https://your-synology-ip:8443

3. Update port forwarding on your router:
   - Forward external port 80 to internal port 8080
   - Forward external port 443 to internal port 8443

**Note:** For SSL certificates with Let's Encrypt, option 1 or 2 is recommended as Let's Encrypt validates on standard ports.
