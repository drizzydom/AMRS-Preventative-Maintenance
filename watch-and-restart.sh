#!/bin/bash

# Install inotify-tools if needed
# apt-get update && apt-get install -y inotify-tools

echo "Watching for changes in application files..."

# Function to restart Docker container
restart_container() {
    echo "Changes detected, rebuilding and restarting container..."
    docker-compose down
    docker-compose build
    docker-compose up -d
    echo "Container restarted at $(date)"
}

# Watch directory for changes in Python files
inotifywait -m -r -e modify,create,delete --exclude "instance|backups|__pycache__|.*\.pyc" . |
while read -r directory events filename; do
    if [[ "$filename" =~ \.py$ ]] || [[ "$filename" =~ \.html$ ]] || [[ "$filename" =~ \.js$ ]] || [[ "$filename" =~ \.css$ ]] || [[ "$filename" =~ Dockerfile$ ]] || [[ "$filename" =~ docker-compose.yml$ ]]; then
        echo "File $directory$filename was $events"
        restart_container
    fi
done
