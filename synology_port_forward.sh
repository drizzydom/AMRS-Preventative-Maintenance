#!/bin/bash

echo "Updated Port Forwarding Configuration Instructions"
echo "================================================="
echo
echo "1. Access your Synology Router management interface"
echo "2. Navigate to Network Center > Port Forwarding"
echo "3. Create two rules:"
echo
echo "   Rule 1: HTTP"
echo "   - Name: HTTP-App"
echo "   - External Port: 80"  # Keep this as 80 for external access
echo "   - Internal IP: [Your Synology NAS IP]" 
echo "   - Internal Port: 8080"  # Updated to use port 8080
echo "   - Protocol: TCP"
echo
echo "   Rule 2: HTTPS" 
echo "   - Name: HTTPS-App"
echo "   - External Port: 443"  # Keep this as 443 for external access
echo "   - Internal IP: [Your Synology NAS IP]"
echo "   - Internal Port: 8443"  # Updated to use port 8443
echo "   - Protocol: TCP"
echo
echo "4. Apply the rules"
