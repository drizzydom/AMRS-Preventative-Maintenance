#!/bin/bash

# Example of updating a DDNS record (adapt to your provider)
echo "Setting up DDNS for your Docker container..."

# For Synology built-in DDNS
echo "On your Synology NAS:"
echo "1. Go to Control Panel → External Access → DDNS"
echo "2. Click Add and enter your previous DDNS provider details"
echo "3. Enter your hostname, username and password"
echo "4. Enable automatic updates"

# For custom DDNS update client
echo "Alternatively, you can set up a cron job to update your DDNS:"
echo "*/15 * * * * curl -s 'https://your-ddns-provider.com/update?hostname=your-domain.com&password=your-password' > /dev/null 2>&1"
