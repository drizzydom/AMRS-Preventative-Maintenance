#!/usr/bin/env python3
"""
Keep-alive script for Render deployment.
This script sends periodic HTTP requests to the application to prevent it from sleeping.
Run this as a separate service or via scheduled tasks.
"""

import requests
import time
import os
import sys
import datetime
import logging
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("keep_alive")

# Configuration
APP_URL = os.environ.get('APP_URL', 'https://maintenance-tracker.onrender.com')
HEALTH_ENDPOINT = '/health'
PING_INTERVAL = 60 * 14  # 14 minutes (Render free tier sleep after 15 min)
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

def ping_app():
    """Send a request to the health check endpoint."""
    url = urljoin(APP_URL, HEALTH_ENDPOINT)
    
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Pinging {url}")
            start_time = time.time()
            response = requests.get(url, timeout=10)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                logger.info(f"Health check successful ({elapsed:.2f}s) - Response: {response.json()}")
                return True
            else:
                logger.warning(f"Health check failed with status {response.status_code} ({elapsed:.2f}s)")
        except Exception as e:
            logger.error(f"Error during health check (attempt {attempt+1}/{MAX_RETRIES}): {str(e)}")
        
        if attempt < MAX_RETRIES - 1:
            logger.info(f"Retrying in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)
    
    logger.error(f"Health check failed after {MAX_RETRIES} attempts")
    return False

def main():
    """Main function to periodically ping the application."""
    logger.info(f"Starting keep-alive service for {APP_URL}")
    logger.info(f"Will ping every {PING_INTERVAL} seconds")
    
    while True:
        ping_app()
        logger.info(f"Next ping in {PING_INTERVAL} seconds")
        time.sleep(PING_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Keep-alive service stopped by user")
