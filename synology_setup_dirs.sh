#!/bin/bash

# Directory to be created on the Synology NAS
DOCKER_DATA_DIR="/volume1/docker/data"
SERVER_INSTANCE_DIR="/volume1/docker/AMRS-Preventative-Maintenance/server/instance"

echo "Setting up directories on Synology NAS"
echo "====================================="

# Create the Docker data directory
echo "Creating data directory at: $DOCKER_DATA_DIR"
mkdir -p $DOCKER_DATA_DIR

# Create the server instance directory
echo "Creating server instance directory at: $SERVER_INSTANCE_DIR"
mkdir -p $SERVER_INSTANCE_DIR

echo "All required directories have been created successfully!"
echo "You can now run 'docker-compose up -d' to start the containers."
