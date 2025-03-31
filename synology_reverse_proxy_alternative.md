# Using Synology's Built-in Reverse Proxy

Instead of running Nginx in a container, you can use Synology's built-in reverse proxy:

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

This approach leverages Synology's existing web server that's already listening on ports 80/443.
