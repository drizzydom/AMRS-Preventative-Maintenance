# Verifying Synology Network Configuration

If you're experiencing network errors with Synology DSM's reverse proxy, check these network settings:

1. **Control Panel** → **Network** → **Network Interface**
   - Verify that your primary network interface shows "Connected"
   - Check if your Synology has a proper IP address

2. **Control Panel** → **Network** → **General**
   - Verify the Gateway and DNS Server settings

3. **Control Panel** → **Security** → **Firewall**
   - Ensure that ports 80 and 443 are allowed

4. **Control Panel** → **Application Portal** → **Advanced Settings**
   - Verify that the portal is configured to use the correct network interface

5. **Connection Limits**: Check if your Synology has reached connection limits
   - SSH into your Synology: `ssh admin@your-synology-ip`
   - Run: `netstat -an | grep ESTABLISHED | wc -l`

6. **Test DDNS Resolution**:
   - From your Synology, run: `ping your-hostname.dscloud.me`
   - If it doesn't resolve, there may be DNS issues
