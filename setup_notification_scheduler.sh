#!/bin/bash

# Script to set up cron jobs for notification scheduling

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PYTHON_PATH=$(which python3)

# Check if crontab exists and create it if not
if ! command -v crontab &> /dev/null; then
    echo "Error: crontab is not installed."
    exit 1
fi

# Create temporary file with existing cron jobs
crontab -l > /tmp/current_cron 2>/dev/null || echo "" > /tmp/current_cron

# Check if the jobs are already in the crontab
if ! grep -q "notification_scheduler.py daily" /tmp/current_cron; then
    # Add daily digest job (runs at 8:00 AM every day)
    echo "0 8 * * * cd ${DIR} && ${PYTHON_PATH} notification_scheduler.py daily" >> /tmp/current_cron
    echo "Daily notification job added."
else
    echo "Daily notification job already exists."
fi

if ! grep -q "notification_scheduler.py weekly" /tmp/current_cron; then
    # Add weekly digest job (runs at 9:00 AM every Monday)
    echo "0 9 * * 1 cd ${DIR} && ${PYTHON_PATH} notification_scheduler.py weekly" >> /tmp/current_cron
    echo "Weekly notification job added."
else
    echo "Weekly notification job already exists."
fi

# Install new crontab
crontab /tmp/current_cron
rm /tmp/current_cron

echo "Notification scheduler set up successfully."
echo "Daily digests will run at 8:00 AM every day."
echo "Weekly digests will run at 9:00 AM every Monday."
