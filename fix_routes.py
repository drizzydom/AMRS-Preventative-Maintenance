#!/usr/bin/env python3
"""
Utility script to fix routing issues and create admin account
Run this script directly to perform diagnostics and fixes
"""

import os
import sys
import importlib
import inspect

def diagnose_app():
    """Diagnose Flask app routing issues"""
    print("\n===== ROUTE DIAGNOSTICS =====")
    
    try:
        # Try to import app
        print("Importing app...")
        from app import app, db, User
        
        # Print all registered routes
        print("\nRegistered Routes:")
        for rule in app.url_map.iter_rules():
            print(f"  {rule.endpoint}: {', '.join(rule.methods - {'HEAD', 'OPTIONS'})} {rule}")
        
        # Check for root route (/)
        root_endpoints = [rule.endpoint for rule in app.url_map.iter_rules() if rule.rule == '/']
        if root_endpoints:
            print(f"\nRoot route (/) is mapped to: {root_endpoints[0]}")
        else:
            print("\nWARNING: No root route (/) defined!")
            
        # Check if needed templates exist
        template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
        
        print("\nChecking critical templates:")
        for template in ['login.html', 'dashboard.html', 'base.html', 'errors/404.html']:
            path = os.path.join(template_dir, template)
            if os.path.exists(path):
                print(f"  ✓ {template} exists")
            else:
                print(f"  ✗ {template} is missing!")
                
        # Check database status
        print("\nChecking database:")
        with app.app_context():
            tables = db.engine.table_names()
            print(f"  Found {len(tables)} tables: {', '.join(tables)}")
            
            # Check if User model exists and has users
            if 'user' in tables:
                user_count = User.query.count()
                print(f"  Found {user_count} users")
                
                # Create admin user if none exist
                if user_count == 0:
                    print("\nCreating default admin user...")
                    create_admin()
            else:
                print("  User table not found")
        
    except ImportError as e:
        print(f"Error importing app: {e}")
    except Exception as e:
        print(f"Error during diagnosis: {e}")

def create_admin():
    """Create admin user directly"""
    try:
        # Import necessary modules
        from app import db, User, Role
        from werkzeug.security import generate_password_hash
        
        # Try to find or create admin role
        admin_role = Role.query.filter_by(name="Administrator").first()
        if not admin_role:
            admin_role = Role(
                name="Administrator",
                description="Full system access",
                permissions="admin.full"
            )
            db.session.add(admin_role)
            db.session.commit()
            
        # Create admin user
        admin = User(
            username="admin",
            email="admin@example.com",
            full_name="System Administrator",
            is_admin=True,
            role_id=admin_role.id
        )
        
        # Handle different password setting mechanisms
        if hasattr(admin, 'set_password'):
            admin.set_password("admin")
        else:
            admin.password_hash = generate_password_hash("admin")
            
        db.session.add(admin)
        db.session.commit()
        
        print("Successfully created admin user with username 'admin' and password 'admin'")
    except Exception as e:
        print(f"Error creating admin: {e}")
        
if __name__ == '__main__':
    diagnose_app()
