#!/bin/bash

# Replace with your Synology NAS IP address and username
NAS_IP="192.168.1.x"
NAS_USER="admin"
PROJECT_DIR="/volume1/docker/AMRS-Preventative-Maintenance"

# Create the directory on Synology if it doesn't exist
ssh ${NAS_USER}@${NAS_IP} "mkdir -p ${PROJECT_DIR}"

# Copy the entire project folder to Synology
scp -r ../* ${NAS_USER}@${NAS_IP}:${PROJECT_DIR}/

echo "Files transferred successfully to ${PROJECT_DIR} on your Synology NAS"
