#!/usr/bin/env python3
"""
Simplified healthcheck script that doesn't require external dependencies
"""
import os
import sys
import http.client
import json
import time
from sqlalchemy import create_engine, text
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models import encrypt_value

# Use DATABASE_URL from environment
DATABASE_URL = os.environ.get('DATABASE_URL')

def check_database():
    """Check if database has the required tables and admin account (PostgreSQL/SQLAlchemy version)"""
    print("Checking database (SQLAlchemy/PostgreSQL)...")
    if not DATABASE_URL:
        print("DATABASE_URL not set!")
        return False
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            # Check tables
            tables = [row[0] for row in conn.execute(text("""
                SELECT table_name FROM information_schema.tables WHERE table_schema='public'
            """))]
            required_tables = ['users', 'sites', 'machines', 'parts', 'maintenance_records']
            missing_tables = [t for t in required_tables if t not in tables]
            if missing_tables:
                print(f"Warning: Missing tables: {', '.join(missing_tables)}")
                return False
                
            # Check for admin account using environment variable or fallback
            admin_username = os.environ.get('DEFAULT_ADMIN_USERNAME')
            if admin_username:
                encrypted_username = encrypt_value(admin_username)
                result = conn.execute(text("SELECT id, username FROM users WHERE username = :username"), {"username": encrypted_username})
                admin = result.fetchone()
                if not admin:
                    print(f"Warning: Admin account '{admin_username}' not found!")
                    # Check if any admin account exists at all
                    result = conn.execute(text("SELECT COUNT(*) FROM users WHERE role_id = (SELECT id FROM roles WHERE name = 'admin')"))
                    count = result.scalar()
                    if count == 0:
                        print("No admin account found in the database!")
                        return False
                    else:
                        print(f"Found {count} admin account(s) with different username.")
                else:
                    print(f"Database check passed! Admin account ID: {admin[0]}")
            else:
                # If no admin username provided in env vars, check if any admin role exists
                result = conn.execute(text("SELECT COUNT(*) FROM users WHERE role_id = (SELECT id FROM roles WHERE name = 'admin')"))
                count = result.scalar()
                if count == 0:
                    print("No admin account found in the database!")
                    return False
                else:
                    print(f"Database check passed! Found {count} admin account(s).")
            
            return True
    except Exception as e:
        print(f"Database check failed: {str(e)}")
        return False
    
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
