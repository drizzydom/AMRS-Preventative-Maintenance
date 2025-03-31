# Running the setup script from your local computer

1. Make the script executable:
   chmod +x master_setup.sh

2. Run the script:
   ./master_setup.sh

3. When prompted, provide:
   - Your Synology NAS IP address
   - SSH username (typically "admin")
   - DDNS hostname and other configuration options

The script will automatically:
- Connect to your Synology via SSH
- Copy necessary files
- Set up directories
- Configure DDNS and certificates
- Create and start Docker containers
