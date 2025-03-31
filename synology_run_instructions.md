# Running the setup script directly on Synology

1. Copy the entire AMRS-Preventative-Maintenance folder to your Synology NAS
   For example, to: /volume1/docker/AMRS-Preventative-Maintenance

2. SSH into your Synology:
   ssh admin@your-synology-ip

3. Navigate to the directory:
   cd /volume1/docker/AMRS-Preventative-Maintenance

4. Make the script executable:
   chmod +x master_setup.sh

5. Run the script:
   ./master_setup.sh

6. Follow the prompts to configure your installation
