#!/bin/bash

# Complete rebuild with no caching and forced recreation
docker-compose down
docker system prune -f --volumes
docker-compose build --no-cache
docker-compose up --force-recreate
