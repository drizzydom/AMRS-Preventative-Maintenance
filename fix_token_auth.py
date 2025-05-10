#!/usr/bin/env python3
"""
Fix token authentication issues in the AMRS Preventative Maintenance application.
This script checks and updates the token_manager.py file to ensure proper handling of user IDs.
"""

import os
import sys
import logging
import re
import shutil
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='[FIX_TOKEN_AUTH] %(levelname)s - %(message)s')
logger = logging.getLogger("fix_token_auth")

def backup_file(file_path):
    """Create a backup of the file before modification"""
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False
        
    backup_dir = os.path.join(os.path.dirname(file_path), 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = os.path.basename(file_path)
    backup_path = os.path.join(backup_dir, f"{filename}.{timestamp}.bak")
    
    try:
        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup at {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return False

def fix_token_manager(file_path):
    """Fix the token_manager.py file to ensure proper handling of user IDs"""
    try:
        # First create a backup
        if not backup_file(file_path):
            logger.error("Failed to create backup, aborting file modification")
            return False
            
        # Read the file contents
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Check if 'sub' claim is properly set as a string
        sub_pattern = r"['\"]sub['\"]\s*:\s*([^,\n]+)"
        sub_match = re.search(sub_pattern, content)
        
        if sub_match:
            current_value = sub_match.group(1).strip()
            logger.info(f"Found 'sub' claim implementation: {current_value}")
            
            if 'str(' not in current_value:
                # Need to fix: convert user_id to string
                logger.info("Fixing 'sub' claim: Adding str() conversion")
                modified_content = re.sub(
                    r"['\"](sub)['\"]\s*:\s*([^,\n]+)",
                    r"'\1': str(\2)",
                    content
                )
                
                # Write the modified content
                with open(file_path, 'w') as f:
                    f.write(modified_content)
                    
                logger.info("Updated token_manager.py: Added str() conversion for user_id in 'sub' claim")
            else:
                logger.info("'sub' claim already properly converts user_id to string")
        else:
            logger.error("Could not find 'sub' claim in the token_manager.py file")
            return False
            
        # Check if refresh_token method properly handles string user_ids
        refresh_pattern = r"def\s+refresh_token.*?payload\.get\(['\"](sub)['\"].*?\)"
        refresh_match = re.search(refresh_pattern, content, re.DOTALL)
        
        if refresh_match:
            refresh_section = refresh_match.group(0)
            logger.info("Found refresh_token method")
            
            # Check if conversion is already there
            conversion_pattern = r"user_id\s*=\s*payload\.get\(['\"](sub)['\"].*?\)(.*?if\s+isinstance\(user_id,\s*str\).*?user_id\s*=\s*int\(user_id\))"
            conversion_match = re.search(conversion_pattern, content, re.DOTALL)
            
            if not conversion_match:
                # Need to add conversion code
                logger.info("Fixing refresh_token method: Adding string to int conversion")
                
                # Pattern to find user_id extraction
                user_id_pattern = r"(user_id\s*=\s*payload\.get\(['\"](sub)['\"].*?\))"
                
                # Replacement with conversion code
                replacement = r"""\1
            # Convert user_id to int if it's stored as string
            if isinstance(user_id, str) and user_id.isdigit():
                user_id = int(user_id)"""
                
                # Apply the replacement
                modified_content = re.sub(user_id_pattern, replacement, content)
                
                # Write the modified content
                with open(file_path, 'w') as f:
                    f.write(modified_content)
                    
                logger.info("Updated token_manager.py: Added string to int conversion in refresh_token method")
            else:
                logger.info("refresh_token method already handles string user_ids properly")
                
            return True
        else:
            logger.error("Could not find refresh_token method in the token_manager.py file")
            return False
            
    except Exception as e:
        logger.error(f"Error fixing token_manager.py: {e}")
        return False

def fix_enhanced_token_manager(file_path):
    """Fix the enhanced_token_manager.py file to ensure proper handling of user IDs"""
    try:
        # Similar approach as fix_token_manager, but for the enhanced version
        if not os.path.exists(file_path):
            logger.info("Enhanced token manager not found, skipping")
            return True
            
        # First create a backup
        if not backup_file(file_path):
            logger.error("Failed to create backup, aborting file modification")
            return False
            
        # Read the file contents
        with open(file_path, 'r') as f:
            content = f.read()
            
        # In the enhanced token manager, check for proper handling
        # This is a simplified check, might need more complex patterns
        needs_fixing = False
        
        # Check if there are references to 'sub' and if they properly handle strings
        if "'sub':" in content and "str(" not in content:
            needs_fixing = True
            
        if needs_fixing:
            logger.info("Enhanced token manager needs fixing, but automatic fix not implemented")
            logger.info("Please review enhanced_token_manager.py manually and ensure proper user_id handling")
            
        return True
            
    except Exception as e:
        logger.error(f"Error fixing enhanced_token_manager.py: {e}")
        return False

def reset_user_password(username, new_password):
    """Reset the password for a specified user"""
    try:
        # Import inside function to avoid issues if modules aren't available
        from werkzeug.security import generate_password_hash
        from db_controller import DatabaseController
        
        # Create a database controller
        db = DatabaseController(use_encryption=False)
        
        # Check if the user exists
        user = db.fetch_one(
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (username,)
        )
        
        if not user:
            logger.error(f"User '{username}' not found in database")
            return False
        
        # Generate password hash
        password_hash = generate_password_hash(new_password)
        
        # Update the user's password
        db.execute_query(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (password_hash, user['id'])
        )
        
        # Verify the update worked
        updated_user = db.fetch_one(
            "SELECT id, username FROM users WHERE id = ? AND password_hash = ?",
            (user['id'], password_hash)
        )
        
        if updated_user:
            logger.info(f"Successfully reset password for user: {username}")
            # Test authentication
            auth_result = db.authenticate_user(username, new_password)
            if auth_result:
                logger.info(f"Authentication with new password successful: {auth_result}")
            else:
                logger.warning(f"Authentication with new password failed")
            return True
        else:
            logger.error(f"Failed to verify password reset for user: {username}")
            return False
            
    except Exception as e:
        logger.error(f"Error resetting password: {e}")
        return False

def main():
    """Main function to check and fix token authentication issues"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    token_manager_path = os.path.join(base_dir, 'token_manager.py')
    enhanced_token_manager_path = os.path.join(base_dir, 'enhanced_token_manager.py')
    
    logger.info("Starting token authentication fix")
    
    # Fix token_manager.py
    if fix_token_manager(token_manager_path):
        logger.info("token_manager.py has been checked and fixed if needed")
    else:
        logger.error("Failed to fix token_manager.py")
        
    # Fix enhanced_token_manager.py
    if fix_enhanced_token_manager(enhanced_token_manager_path):
        logger.info("enhanced_token_manager.py has been checked")
    else:
        logger.error("Failed to check enhanced_token_manager.py")
    
    # Reset password for dmoriello user
    reset_password = input("Do you want to reset the password for user 'dmoriello'? (y/n): ").lower() == 'y'
    if reset_password:
        password = input("Enter new password (default: password123): ") or "password123"
        if reset_user_password('dmoriello', password):
            print(f"Password for 'dmoriello' has been reset to '{password}'")
        else:
            print("Failed to reset password for 'dmoriello'")
    
    print("\nToken authentication fix completed.")
    print("You can now try logging in with the user 'dmoriello'.")
    
if __name__ == "__main__":
    main()
