#!/bin/bash

echo "Completely rebuilding Docker containers..."
docker-compose down
docker system prune -f -a --volumes
docker-compose build --no-cache
docker-compose up
