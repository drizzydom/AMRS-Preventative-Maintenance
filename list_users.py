#!/usr/bin/env python3
"""
Quick script to list all users in the database
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Set up database configuration
os.environ['DATABASE_URL'] = 'sqlite:////Users/dominicmoriello/Library/Application Support/AMRS_PM/maintenance_secure.db'

from models import User
from db_utils import db

def list_users():
    """List all users in the database"""
    print("\n" + "="*60)
    print("USERS IN DATABASE")
    print("="*60)
    
    try:
        users = User.query.all()
        
        if not users:
            print("\nNo users found in database!")
            return
        
        print(f"\nFound {len(users)} users:\n")
        
        for user in users:
            status = "✓ ACTIVE" if user.is_active else "✗ INACTIVE"
            role = user.role.name if user.role else "No Role"
            print(f"  {status:12} | Username: {user.username:20} | Email: {user.email:30} | Role: {role}")
        
        print("\n" + "="*60)
        print(f"\nTo login, use one of the usernames above with its password.")
        print("If you don't know the password, you may need to reset it.")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error listing users: {e}")
        print(f"   Make sure the database exists at:")
        print(f"   {os.environ['DATABASE_URL']}\n")

if __name__ == '__main__':
    list_users()
