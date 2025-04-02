#!/usr/bin/env python3
"""
Simplified healthcheck script that doesn't require external dependencies
"""
import os
import sys
import sqlite3
import http.client
import json
import time

DB_PATH = '/app/data/app.db'

def check_database():
    """Check if database has the required tables and admin account"""
    print("Checking database...")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        required_tables = ['user', 'site', 'machine', 'part', 'maintenance_record']
        
        missing_tables = [table for table in required_tables if table not in tables]
        if missing_tables:
            print(f"Warning: Missing tables: {', '.join(missing_tables)}")
            return False
        
        # Check for admin account
        cursor.execute("SELECT id, username FROM user WHERE username = ?", ("techsupport",))
        admin = cursor.fetchone()
        if not admin:
            print("Warning: Techsupport admin account not found!")
            return False
            
        print(f"Database check passed! Admin account ID: {admin[0]}")
        return True
        
    except Exception as e:
        print(f"Database check failed: {str(e)}")
        return False
    
    finally:
        if 'conn' in locals():
            conn.close()

def check_api():
    """Check if API endpoints are responding using standard library"""
    print("Checking API endpoints...")
    
    endpoints = [
        '/api/health'
    ]
    
    for endpoint in endpoints:
        try:
            # Create connection to localhost
            conn = http.client.HTTPConnection('localhost', 9000)
            conn.request('GET', endpoint)
            response = conn.getresponse()
            
            if response.status == 200:
                print(f"✓ Endpoint {endpoint} is working")
            else:
                print(f"✗ Endpoint {endpoint} returned status {response.status}")
                return False
            
        except Exception as e:
            print(f"✗ Failed to connect to {endpoint}: {str(e)}")
            return False
    
    return True

def main():
    """Run all checks and report results"""
    print("Starting system health check...")
    
    # Wait for app to be fully initialized
    time.sleep(2)
    
    db_check = check_database()
    api_check = check_api()
    
    if db_check and api_check:
        print("\n==== ALL CHECKS PASSED! System is ready. ====")
        return True
    else:
        print("\n==== SOME CHECKS FAILED! Please check the logs. ====")
        return False

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)
