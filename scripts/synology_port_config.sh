#!/bin/bash
# =============================================================================
# AMRS Synology Port Forwarding Guide
# This script provides guidance for setting up port forwarding on Synology
# =============================================================================

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BOLD}AMRS Synology Port Forwarding Guide${NC}"
echo "===================================="
echo

# Get current external IP address
EXTERNAL_IP=$(curl -s https://api.ipify.org || curl -s https://ifconfig.me || echo "Unknown")

# Check if DSM 7 or DSM 6
DSM_VERSION=""
if [ -f "/etc/synoinfo.conf" ]; then
    MAJOR_VERSION=$(grep "^majorversion" /etc/synoinfo.conf | cut -d'"' -f2)
    MINOR_VERSION=$(grep "^minorversion" /etc/synoinfo.conf | cut -d'"' -f2)
    DSM_VERSION="${MAJOR_VERSION}.${MINOR_VERSION}"
fi

# Get HTTP and HTTPS ports
HTTP_PORT=${1:-8080}
HTTPS_PORT=${2:-8443}

echo -e "${BOLD}1. Current System Information${NC}"
echo -e "External IP Address: ${GREEN}$EXTERNAL_IP${NC}"
if [ -n "$DSM_VERSION" ]; then
    echo -e "DSM Version: ${GREEN}$DSM_VERSION${NC}"
else
    echo -e "DSM Version: ${YELLOW}Unknown (Not running on Synology?)${NC}"
fi
echo -e "HTTP Port: ${GREEN}$HTTP_PORT${NC}"
echo -e "HTTPS Port: ${GREEN}$HTTPS_PORT${NC}"
echo

echo -e "${BOLD}2. Port Forwarding Instructions${NC}"
echo -e "${BLUE}To access your AMRS system from outside your network:${NC}"
echo "1. Log in to your Synology DSM web interface"
echo "2. Open the Control Panel"

# Different instructions based on DSM version
if [[ "$DSM_VERSION" == 7* ]]; then
    echo -e "${BOLD}For DSM 7:${NC}"
    echo "3. Go to 'Network' > 'Router Configuration'"
    echo "4. Click 'Create' > 'Custom Port Forwarding Rules'"
    echo "5. Create the following rules:"
    echo -e "   a. ${GREEN}Name: AMRS HTTP${NC}"
    echo -e "      External Port: ${BOLD}80${NC} (or choose another port)"
    echo -e "      Internal Port: ${BOLD}$HTTP_PORT${NC}"
    echo -e "      Local IP: ${BOLD}Your Synology IP${NC}"
    echo -e "      Protocol: ${BOLD}TCP${NC}"
    echo
    echo -e "   b. ${GREEN}Name: AMRS HTTPS${NC}"
    echo -e "      External Port: ${BOLD}443${NC} (or choose another port)"
    echo -e "      Internal Port: ${BOLD}$HTTPS_PORT${NC}"
    echo -e "      Local IP: ${BOLD}Your Synology IP${NC}"
    echo -e "      Protocol: ${BOLD}TCP${NC}"
elif [[ "$DSM_VERSION" == 6* ]]; then
    echo -e "${BOLD}For DSM 6:${NC}"
    echo "3. Go to 'External Access' > 'Router Configuration'"
    echo "4. Click 'Create' > 'Router Configuration'"
    echo "5. Create the following rules:"
    echo -e "   a. ${GREEN}Name: AMRS HTTP${NC}"
    echo -e "      External Port: ${BOLD}80${NC} (or choose another port)"
    echo -e "      Internal Port: ${BOLD}$HTTP_PORT${NC}"
    echo -e "      Local IP: ${BOLD}Your Synology IP${NC}"
    echo -e "      Protocol: ${BOLD}TCP${NC}"
    echo
    echo -e "   b. ${GREEN}Name: AMRS HTTPS${NC}"
    echo -e "      External Port: ${BOLD}443${NC} (or choose another port)"
    echo -e "      Internal Port: ${BOLD}$HTTPS_PORT${NC}"
    echo -e "      Local IP: ${BOLD}Your Synology IP${NC}"
    echo -e "      Protocol: ${BOLD}TCP${NC}"
else
    echo -e "${BOLD}General instructions:${NC}"
    echo "3. Find port forwarding settings in your Synology Control Panel"
    echo "   (Location may vary depending on DSM version)"
    echo "4. Create two port forwarding rules:"
    echo -e "   a. ${GREEN}Forward external port 80 to internal port $HTTP_PORT${NC}"
    echo -e "   b. ${GREEN}Forward external port 443 to internal port $HTTPS_PORT${NC}"
fi
echo

echo -e "${BOLD}3. Alternative: Manual Router Configuration${NC}"
echo "If the Synology router configuration doesn't work, you can configure port forwarding directly on your router:"
echo "1. Access your router's administration interface (typically http://192.168.1.1 or similar)"
echo "2. Find the port forwarding section (may be called 'Virtual Server', 'NAT', or 'Port Forwarding')"
echo "3. Create two port forwarding rules:"
echo -e "   a. ${GREEN}Forward external port 80 to $EXTERNAL_IP:$HTTP_PORT${NC}"
echo -e "   b. ${GREEN}Forward external port 443 to $EXTERNAL_IP:$HTTPS_PORT${NC}"
echo

echo -e "${BOLD}4. Testing External Access${NC}"
echo "After setting up port forwarding, you can test external access:"
echo -e "1. From a device outside your network (like a mobile phone on cellular data),"
echo -e "   try accessing: ${GREEN}http://$EXTERNAL_IP${NC} and ${GREEN}https://$EXTERNAL_IP${NC}"
echo "2. If you have a domain name pointed to your IP address, you can also try:"
echo -e "   ${GREEN}http://yourdomain.com${NC} and ${GREEN}https://yourdomain.com${NC}"
echo

echo -e "${BOLD}5. Security Considerations${NC}"
echo -e "${YELLOW}Important:${NC} When exposing services to the internet, please be aware of security implications:"
echo "1. Always use strong passwords for your admin accounts"
echo "2. Keep your Synology DSM and AMRS system updated"
echo "3. Consider setting up a Synology Reverse Proxy with HTTPS only"
echo "4. Use a proper SSL certificate (Let's Encrypt) for production use"
echo

echo -e "${GREEN}${BOLD}Port Forwarding Guide Complete${NC}"
echo "Follow the instructions above to make your AMRS system accessible from the internet."
echo "If you have any issues, please refer to your Synology documentation or contact support."
