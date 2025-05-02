#!/usr/bin/env python
"""
Script to fix the admin_audit_history route in app.py
This script modifies the query in the admin_audit_history function to ensure 
audit completions are properly displayed.
"""

import os
import sys
import re

def fix_admin_audit_history_route():
    """Fix the admin_audit_history route in app.py"""
    app_py_path = os.path.join(os.path.dirname(__file__), 'app.py')
    
    # Read the current app.py file
    with open(app_py_path, 'r') as file:
        content = file.read()
    
    # Define the pattern to look for and the replacement
    old_query = r"completions = AuditTaskCompletion\.query\.order_by\(AuditTaskCompletion\.completed_at\.desc\(\)\)\.all\(\)"
    new_query = "completions = AuditTaskCompletion.query.filter_by(completed=True).order_by(AuditTaskCompletion.completed_at.desc() if AuditTaskCompletion.completed_at is not None else AuditTaskCompletion.date.desc()).all()"
    
    # Check if the pattern exists
    if re.search(old_query, content):
        # Replace the query
        updated_content = re.sub(old_query, new_query, content)
        
        # Create a backup of the original file
        backup_path = app_py_path + '.bak'
        print(f"Creating backup of app.py at {backup_path}")
        with open(backup_path, 'w') as file:
            file.write(content)
        
        # Write the updated content back to app.py
        print(f"Updating admin_audit_history route in {app_py_path}")
        with open(app_py_path, 'w') as file:
            file.write(updated_content)
        
        print("Successfully updated the admin_audit_history route.")
        print("Now the route will:")
        print("1. Only show records marked as completed")
        print("2. Sort by completed_at timestamp or fall back to date if timestamp is missing")
        
        return True
    else:
        print("Could not find the expected query pattern in app.py.")
        print("The route may have been modified already or the pattern has changed.")
        return False

if __name__ == "__main__":
    fix_admin_audit_history_route()