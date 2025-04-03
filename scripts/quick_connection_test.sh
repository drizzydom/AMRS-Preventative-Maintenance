#!/bin/bash
# Simple script to test connectivity to the application endpoints

# Get ports from arguments or use defaults
APP_PORT=${1:-9000}
HTTP_PORT=${2:-8080}
HTTPS_PORT=${3:-8443}

echo "AMRS Quick Connection Test"
echo "========================="
echo

# Test Flask API directly
echo "Testing direct Flask API connection (http://localhost:$APP_PORT/api/health)..."
curl -v http://localhost:$APP_PORT/api/health
echo -e "\n"

# Test Nginx HTTP proxy
echo "Testing Nginx HTTP connection (http://localhost:$HTTP_PORT/api/health)..."
curl -v http://localhost:$HTTP_PORT/api/health
echo -e "\n"

# Test Nginx HTTPS proxy (ignore SSL errors)
echo "Testing Nginx HTTPS connection (https://localhost:$HTTPS_PORT/api/health)..."
curl -v -k https://localhost:$HTTPS_PORT/api/health
echo -e "\n"

# Check container status
echo "Container status:"
docker ps | grep -E "amrs|nginx"
echo -e "\n"

# Check if ports are listening
echo "Listening ports:"
netstat -tuln 2>/dev/null | grep -E "$APP_PORT|$HTTP_PORT|$HTTPS_PORT" || \
ss -tuln 2>/dev/null | grep -E "$APP_PORT|$HTTP_PORT|$HTTPS_PORT" || \
echo "Could not check listening ports (netstat/ss not available)"
