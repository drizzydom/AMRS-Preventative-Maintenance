# Synology Reverse Proxy Configuration

1. **Open DSM Control Panel**
2. Go to **Login Portal** → **Advanced** → **Reverse Proxy**
3. Click **Create** and set up:
   - **Source:**
     - Protocol: HTTPS
     - Hostname: your-ddns-domain.com (your previous domain)
     - Port: 443
   - **Destination:**
     - Protocol: HTTP
     - Hostname: localhost
     - Port: 9000
4. Enable **HSTS** for better security
5. Click **OK** to save the configuration
