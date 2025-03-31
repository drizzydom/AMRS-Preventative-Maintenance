# Synology Certificate Setup for AMRS Maintenance

There are two ways to set up certificates for your application:

## Option 1: Copy Let's Encrypt Certificates from Synology

After obtaining certificates through Synology DSM:

1. SSH into your Synology:
   ```bash
   ssh admin@your-synology-ip
   ```

2. Find your certificate files (adjust paths as needed):
   ```bash
   sudo find /etc/letsencrypt/live/ -name "*.pem"
   ```

3. Copy the certificate files to your project:
   ```bash
   # Create destination directory
   mkdir -p /volume1/docker/AMRS-Preventative-Maintenance/nginx/ssl
   
   # Copy the certificates (adjust paths as needed)
   sudo cp /etc/letsencrypt/live/amrs-maintenance.dscloud.me/fullchain.pem \
           /volume1/docker/AMRS-Preventative-Maintenance/nginx/ssl/
   sudo cp /etc/letsencrypt/live/amrs-maintenance.dscloud.me/privkey.pem \
           /volume1/docker/AMRS-Preventative-Maintenance/nginx/ssl/
   
   # Fix permissions
   sudo chown -R admin:users /volume1/docker/AMRS-Preventative-Maintenance/nginx/ssl
   ```

4. Restart your Docker containers:
   ```bash
   cd /volume1/docker/AMRS-Preventative-Maintenance
   docker-compose restart nginx
   ```

## Option 2: Use Synology Reverse Proxy (Recommended)

Instead of managing certificates in your container:

1. Go to **DSM Control Panel** → **Login Portal** → **Advanced** → **Reverse Proxy**
2. Click **Create** and set up:
   - **Source:**
     - Protocol: HTTPS
     - Hostname: amrs-maintenance.dscloud.me
     - Port: 443
   - **Destination:**
     - Protocol: HTTP
     - Hostname: localhost
     - Port: 9000 (your app container port)
3. In this case, modify your `docker-compose.yml` to expose only port 9000
   and remove the nginx service.
