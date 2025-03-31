#!/bin/bash

echo "Let's Encrypt on Synology Configuration"
echo "======================================"
echo
echo "1. Open Control Panel in DSM"
echo "2. Go to Security > Certificate"
echo "3. Click 'Add' and select 'Add a new certificate'"
echo "4. Choose 'Get a certificate from Let's Encrypt'"
echo "5. Enter these details:"
echo "   - Domain name: your-ddns-hostname.synology.me"
echo "   - Email: your-email@example.com"
echo "6. Select your domain from the dropdown"
echo "7. Complete the setup and wait for validation"
echo
echo "After certificate is issued:"
echo "8. Note the location of certificate files:"
echo "   - Certificate: /etc/letsencrypt/live/your-ddns-hostname.synology.me/fullchain.pem"
echo "   - Private key: /etc/letsencrypt/live/your-ddns-hostname.synology.me/privkey.pem"
