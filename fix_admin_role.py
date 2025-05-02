#!/usr/bin/env python
"""
Script to fix admin role permissions in AMRS Preventative Maintenance

This script ensures that:
1. The 'admin' role exists and has the 'admin.full' permission
2. All users with username 'admin' or with is_admin=True have the admin role

Run this script from the command line:
python fix_admin_role.py
"""

import os
import sys
from flask import Flask
from models import db, User, Role
from werkzeug.security import generate_password_hash

def fix_admin_role():
    """Find or create admin role and ensure it has admin.full permission"""
    print("\n--- Fixing Admin Role Permissions ---")
    
    # Find existing admin role or create a new one
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        print(f"Creating new admin role")
        admin_role = Role(name='admin', description='Administrator', permissions='admin.full')
        db.session.add(admin_role)
        db.session.commit()
        print(f"Created admin role with ID {admin_role.id} and permissions: admin.full")
    else:
        # Ensure the admin role has admin.full permission
        current_permissions = admin_role.permissions.split(',') if admin_role.permissions else []
        if 'admin.full' not in current_permissions:
            current_permissions.append('admin.full')
            admin_role.permissions = ','.join(current_permissions)
            db.session.commit()
            print(f"Updated admin role (ID: {admin_role.id}) to include admin.full permission")
            print(f"Current permissions: {admin_role.permissions}")
        else:
            print(f"Admin role (ID: {admin_role.id}) already has admin.full permission")
    
    return admin_role

def fix_admin_users(admin_role):
    """Ensure all admin users have the admin role"""
    print("\n--- Fixing Admin Users ---")
    
    # Find users who should have admin role (username=admin OR is_admin=True)
    admin_username_users = User.query.filter(User.username_hash == User.query.filter_by(_username='admin').first().username_hash if User.query.filter_by(_username='admin').first() else '').all()
    admin_flag_users = User.query.filter_by(is_admin=True).all()
    
    # Combine the lists without duplicates
    admin_users = list(set(admin_username_users + admin_flag_users))
    
    if not admin_users:
        print("No admin users found in the database")
        return
    
    updated_count = 0
    for user in admin_users:
        if not user.role or user.role.id != admin_role.id:
            user.role = admin_role
            updated_count += 1
            print(f"Updated user '{user.username}' (ID: {user.id}) to have admin role")
    
    if updated_count > 0:
        db.session.commit()
        print(f"Updated {updated_count} user(s) to have admin role")
    else:
        print("All admin users already have the correct role")

def create_admin_user(admin_role):
    """Create a default admin user if none exists"""
    print("\n--- Checking for Default Admin User ---")
    
    # Check if we have any admin users
    admin_users = User.query.filter(
        (User.role_id == admin_role.id) | 
        (User.is_admin == True) | 
        (User.username_hash == User.query.filter_by(_username='admin').first().username_hash if User.query.filter_by(_username='admin').first() else '')
    ).all()
    
    if admin_users:
        print(f"Found {len(admin_users)} existing admin user(s)")
        return
    
    # Get credentials from environment variables
    admin_username = os.environ.get('DEFAULT_ADMIN_USERNAME') or 'admin'
    admin_email = os.environ.get('DEFAULT_ADMIN_EMAIL') or 'admin@example.com'
    admin_password = os.environ.get('DEFAULT_ADMIN_PASSWORD') or 'adminpassword'
    
    # Create new admin user
    print(f"Creating default admin user with username: {admin_username}")
    admin_user = User(
        username=admin_username,
        email=admin_email,
        password_hash=generate_password_hash(admin_password),
        is_admin=True,
        role=admin_role
    )
    
    db.session.add(admin_user)
    db.session.commit()
    print(f"Created default admin user with ID: {admin_user.id}")

def main():
    """Main function to run the script"""
    # Create a minimal Flask app to establish database connection
    app = Flask(__name__)
    
    # Load the configuration
    if os.path.exists('config.py'):
        app.config.from_object('config.Config')
    else:
        print("Error: config.py not found")
        sys.exit(1)
    
    # Initialize the database with the app
    db.init_app(app)
    
    # Run the fixes within the app context
    with app.app_context():
        admin_role = fix_admin_role()
        fix_admin_users(admin_role)
        create_admin_user(admin_role)
    
    print("\nAdmin role and user fixes completed successfully!")

if __name__ == "__main__":
    main()