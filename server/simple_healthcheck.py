#!/usr/bin/env python3
"""
Simple health check script for AMRS Maintenance Tracker

This script checks basic system health without requiring external dependencies.
It's used during the setup process to verify the application is functioning correctly.
"""
import os
import sys
import sqlite3
import http.client
import json
from datetime import datetime

def check_database():
    """Check database connection and basic structure"""
    print("Checking database connection...")
    db_path = '/app/data/app.db'
    
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        return False
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if we can execute a query
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        if result[0] == 1:
            print("Database connection successful")
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        print(f"Found tables: {', '.join(table_names)}")
        
        # Check if user table has admin user
        if 'user' in table_names:
            cursor.execute("SELECT COUNT(*) FROM user WHERE role='admin'")
            admin_count = cursor.fetchone()[0]
            print(f"Admin users found: {admin_count}")
            
            if admin_count == 0:
                print("Warning: No admin users found in the database")
                
        conn.close()
        return True
    except Exception as e:
        print(f"Database error: {str(e)}")
        return False

def check_api_health():
    """Check if API is responsive"""
    print("Checking API health...")
    try:
        conn = http.client.HTTPConnection("localhost", 9000)
        conn.request("GET", "/api/health")
        response = conn.getresponse()
        
        if response.status == 200:
            data = response.read()
            try:
                result = json.loads(data.decode())
                print(f"API health check: {result.get('status', 'unknown')}")
                return True
            except:
                print("API returned non-JSON response")
                return False
        else:
            print(f"API health check failed with status: {response.status}")
            return False
    except Exception as e:
        print(f"API connection error: {str(e)}")
        return False

def main():
    """Run all health checks"""
    print(f"Starting health check at {datetime.now()}")
    print("=" * 50)
    
    db_status = check_database()
    api_status = check_api_health()
    
    print("=" * 50)
    print("Health Check Results:")
    print(f"Database: {'PASS' if db_status else 'FAIL'}")
    print(f"API: {'PASS' if api_status else 'FAIL'}")
    
    # Return overall status
    return db_status and api_status

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
