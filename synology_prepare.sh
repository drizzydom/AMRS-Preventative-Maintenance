#!/bin/bash

# Replace with your actual Synology login details
NAS_IP="your-synology-ip"
NAS_USER="your-username"

# Create required directory structure for volume mounting
echo "Creating required directories on your Synology NAS..."
ssh ${NAS_USER}@${NAS_IP} "mkdir -p /volume1/amrs-maintenance/app/server/instance"

echo "Directory structure created successfully!"
