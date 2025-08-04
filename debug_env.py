#!/usr/bin/env python3
"""
Debug script to check environment variables for AMRS sync
"""
import os
from dotenv import load_dotenv

# Load .env file first (same way app.py does it)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
dotenv_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path)
print(f"Loaded .env from: {dotenv_path}")
print(f".env file exists: {os.path.exists(dotenv_path)}")
print()

from timezone_utils import is_online_server

print("=== AMRS Environment Debug ===")
print(f"AMRS_ONLINE_URL: {repr(os.environ.get('AMRS_ONLINE_URL'))}")
print(f"AMRS_ADMIN_USERNAME: {repr(os.environ.get('AMRS_ADMIN_USERNAME'))}")
print(f"AMRS_ADMIN_PASSWORD: {'***' if os.environ.get('AMRS_ADMIN_PASSWORD') else None}")
print()
print(f"RENDER: {repr(os.environ.get('RENDER'))}")
print(f"HEROKU: {repr(os.environ.get('HEROKU'))}")
print(f"RAILWAY: {repr(os.environ.get('RAILWAY'))}")
print(f"RENDER_EXTERNAL_URL: {repr(os.environ.get('RENDER_EXTERNAL_URL'))}")
print(f"IS_ONLINE_SERVER: {repr(os.environ.get('IS_ONLINE_SERVER'))}")
print()
print(f"is_online_server() returns: {is_online_server()}")
print()
if is_online_server():
    print("❌ PROBLEM: This system thinks it's the online server!")
    print("📝 SOLUTION: Set AMRS_ONLINE_URL environment variable")
else:
    print("✅ GOOD: This system correctly identifies as offline client")
    if not os.environ.get('AMRS_ONLINE_URL'):
        print("⚠️  WARNING: AMRS_ONLINE_URL not set - sync will be skipped")
        print("📝 SOLUTION: Check your .env file has AMRS_ONLINE_URL=https://your-render-url.onrender.com")
