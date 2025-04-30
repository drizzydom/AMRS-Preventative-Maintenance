#!/usr/bin/env python
"""
Fix for audit history not showing audit actions.
This file is imported during app startup to patch the admin_audit_history function.
"""
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def patch_admin_audit_history():
    """
    Patch the admin_audit_history function to properly show audit actions.
    This fixes issues with query that might not be showing completed audit tasks.
    """
    try:
        # Import the app and required models after this module is imported
        from app import app, db
        from models import AuditTaskCompletion, AuditTask, Machine, User
        from flask import render_template, flash, redirect, url_for
        from flask_login import current_user
        
        # Define our improved version of the admin_audit_history function
        def fixed_admin_audit_history():
            if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard'))
                
            # Get all completions that are marked as completed
            # Order by completed_at if available, otherwise fall back to date
            completions = AuditTaskCompletion.query.filter_by(completed=True).order_by(
                AuditTaskCompletion.completed_at.desc()
            ).all()
            
            # Fix any records that have completed=True but no completed_at timestamp
            try:
                records_to_fix = AuditTaskCompletion.query.filter(
                    AuditTaskCompletion.completed == True,
                    AuditTaskCompletion.completed_at == None
                ).all()
                
                if records_to_fix:
                    logger.info(f"Fixing {len(records_to_fix)} audit records with missing timestamps")
                    for record in records_to_fix:
                        record.completed_at = record.created_at
                    db.session.commit()
            except Exception as e:
                logger.error(f"Error fixing audit records: {e}")
                
            # Get related data for the template
            audit_tasks = {t.id: t for t in AuditTask.query.all()}
            machines = {m.id: m for m in Machine.query.all()}
            users = {u.id: u for u in User.query.all()}
            
            return render_template('admin/audit_history.html', 
                                  completions=completions, 
                                  audit_tasks=audit_tasks, 
                                  machines=machines,
                                  users=users)
        
        # Replace the original function with our fixed version
        from app import admin_audit_history as original_function
        
        # Apply our patched function
        app.view_functions['admin_audit_history'] = fixed_admin_audit_history
        
        logger.info("Successfully patched admin_audit_history function")
        return True
        
    except ImportError as e:
        logger.error(f"Failed to import necessary modules: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to patch admin_audit_history: {e}")
        return False

# The patch will be applied when this module is imported
patch_successful = patch_admin_audit_history()