"""
sync_db.py - Script to sync online AMRS database to local offline storage

Usage:
    python sync_db.py --url <ONLINE_URL> --username <ADMIN_USER> --password <ADMIN_PASS> [--outfile <FILENAME>]

This script authenticates as an admin, downloads all data from /api/sync/data,
and saves it as a JSON file (default: amrs_sync_data.json).
"""

import requests
import argparse
import getpass
import os
import sys
from sync_utils import import_json_to_sqlite

DEFAULT_OUTFILE = "amrs_sync_data.json"
DEFAULT_DB = "maintenance.db"

parser = argparse.ArgumentParser(description="Sync AMRS online database for offline use.")
parser.add_argument('--url', help='Base URL of the online AMRS server (e.g. https://your-app.onrender.com)')
parser.add_argument('--username', help='Admin username')
parser.add_argument('--password', help='Admin password (will prompt if not given)')
parser.add_argument('--outfile', default=DEFAULT_OUTFILE, help='Output JSON file')
parser.add_argument('--import', dest='import_file', help='Import JSON file into local SQLite DB')
parser.add_argument('--db', default=DEFAULT_DB, help='Path to local SQLite DB (default: maintenance.db)')
args = parser.parse_args()

if args.import_file:
    # Import mode: import JSON into SQLite DB
    import_json_to_sqlite(args.import_file, args.db)
    sys.exit(0)

if not (args.url and args.username):
    print("You must provide --url and --username for sync.")
    sys.exit(1)

session = requests.Session()

# Prompt for password if not provided
if not args.password:
    args.password = getpass.getpass(f"Password for {args.username}: ")

# Step 1: Log in to get session cookie
login_url = args.url.rstrip('/') + '/login'
sync_url = args.url.rstrip('/') + '/api/sync/data'

print(f"Logging in as {args.username}...")
login_resp = session.post(login_url, data={
    'username': args.username,
    'password': args.password
}, allow_redirects=True)

if login_resp.status_code != 200 or ('Set-Cookie' not in login_resp.headers and 'session' not in session.cookies):
    print("Login failed. Check credentials and try again.")
    sys.exit(1)

print("Login successful. Downloading sync data...")
sync_resp = session.get(sync_url)
if sync_resp.status_code != 200:
    print(f"Failed to fetch sync data: {sync_resp.status_code} {sync_resp.text}")
    sys.exit(1)

with open(args.outfile, 'w', encoding='utf-8') as f:
    f.write(sync_resp.text)

print(f"Sync data saved to {args.outfile}")
print(f"To import into local DB, run: python sync_db.py --import {args.outfile} --db {args.db}")
