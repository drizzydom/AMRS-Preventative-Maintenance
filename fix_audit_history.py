#!/usr/bin/env python
"""
Fix for audit history not showing audit actions and machine names.
This file is imported during app startup to patch both audit history related functions.
"""
import logging
from functools import wraps
from datetime import datetime, timedelta, date

logger = logging.getLogger(__name__)

def patch_audit_history_functions():
    """
    Patch both the admin_audit_history and audit_history_page functions
    to properly show audit actions and machine data.
    """
    try:
        # Import the app and required models after this module is imported
        from app import app, db
        from models import AuditTaskCompletion, AuditTask, Machine, User, Site
        from flask import render_template, flash, redirect, url_for, request
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
        
        # Define our improved version of the audit_history_page function
        def fixed_audit_history_page():
            # Same permission checks as original function
            if current_user.is_admin:
                can_access = True
            else:
                if hasattr(current_user, 'role') and current_user.role:
                    if hasattr(current_user.role, 'name'):
                        # Role is an object, use its permissions directly
                        permissions = (current_user.role.permissions or '').replace(' ', '').split(',') 
                        can_access = 'audits.access' in permissions
                    else:
                        # Role is a string, query for the role
                        from models import Role
                        user_role = Role.query.filter_by(name=current_user.role).first()
                        permissions = (user_role.permissions or '').replace(' ', '').split(',') if user_role and user_role.permissions else []
                        can_access = 'audits.access' in permissions
                else:
                    can_access = False
            
            if not can_access:
                flash('You do not have permission to access audit history.', 'danger')
                return redirect(url_for('dashboard'))

            # Get date range for filtering
            start_date_str = request.args.get('start_date')
            end_date_str = request.args.get('end_date')
            
            today = datetime.now().date()
            
            # Default to last 365 days if no dates provided
            if not start_date_str:
                start_date = today - timedelta(days=365)
            else:
                try:
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                except ValueError:
                    start_date = today - timedelta(days=365)
                    flash("Invalid start date format. Using default of 365 days ago.", "warning")
            
            if not end_date_str:
                end_date = today
            else:
                try:
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                except ValueError:
                    end_date = today
                    flash("Invalid end date format. Using today's date.", "warning")
            
            # Ensure start date is before end date
            if start_date > end_date:
                start_date, end_date = end_date, start_date
            
            # Get site and machine filters
            site_id = request.args.get('site_id', type=int)
            machine_id = request.args.get('machine_id', type=int)
            
            # Restrict sites for non-admins
            if current_user.is_admin:
                sites = Site.query.all()
            else:
                # Limit to user's assigned sites
                user_site_ids = [site.id for site in current_user.sites]
                sites = current_user.sites
                # Ensure the selected site is one the user has access to
                if site_id and site_id not in user_site_ids:
                    if sites:
                        site_id = sites[0].id
                    else:
                        site_id = None
            
            # If only one site is available, automatically select it
            if len(sites) == 1 and not site_id:
                site_id = sites[0].id

            # Get available machines based on selected site
            if site_id:
                machines = Machine.query.filter_by(site_id=site_id).all()
            else:
                if not current_user.is_admin and sites:
                    site_ids = [site.id for site in sites]
                    machines = Machine.query.filter(Machine.site_id.in_(site_ids)).all()
                else:
                    machines = Machine.query.all()

            # Query completions within the date range
            query = AuditTaskCompletion.query.filter(
                AuditTaskCompletion.date >= start_date,
                AuditTaskCompletion.date <= end_date
            ).order_by(AuditTaskCompletion.date.desc())
            
            # Apply site filter if specified
            if site_id:
                # Get all audit tasks for the selected site
                site_audit_tasks = AuditTask.query.filter_by(site_id=site_id).all()
                task_ids = [task.id for task in site_audit_tasks]
                if task_ids:
                    query = query.filter(AuditTaskCompletion.audit_task_id.in_(task_ids))
                else:
                    # No tasks for this site, return empty result
                    completions = []
                    machine_data = {}
                    show_site_dropdown = len(sites) > 1 or current_user.is_admin
                    return render_template('audit_history.html', 
                                        completions=completions,
                                        grouped_completions={},
                                        sorted_dates=[],
                                        audit_tasks={},
                                        machines={},
                                        available_machines=machines,
                                        users={},
                                        sites=sites,
                                        selected_site=site_id,
                                        selected_machine=machine_id,
                                        start_date=start_date,
                                        end_date=end_date,
                                        today=today,
                                        show_site_dropdown=show_site_dropdown,
                                        machine_data=machine_data)
            else:
                # If no site is selected but we have restricted sites
                if not current_user.is_admin and sites:
                    # Get all audit tasks for the user's sites
                    site_ids = [site.id for site in sites]
                    site_audit_tasks = AuditTask.query.filter(AuditTask.site_id.in_(site_ids)).all()
                    task_ids = [task.id for task in site_audit_tasks]
                    if task_ids:
                        query = query.filter(AuditTaskCompletion.audit_task_id.in_(task_ids))
                    else:
                        # No tasks for user's sites, return empty result
                        completions = []
                        machine_data = {}
                        show_site_dropdown = len(sites) > 1 or current_user.is_admin
                        return render_template('audit_history.html', 
                                            completions=completions,
                                            grouped_completions={},
                                            sorted_dates=[],
                                            audit_tasks={},
                                            machines={},
                                            available_machines=machines,
                                            users={},
                                            sites=sites,
                                            selected_site=site_id,
                                            selected_machine=machine_id,
                                            start_date=start_date,
                                            end_date=end_date,
                                            today=today,
                                            show_site_dropdown=show_site_dropdown,
                                            machine_data=machine_data)

            # Apply machine filter if specified
            if machine_id:
                query = query.filter(AuditTaskCompletion.machine_id == machine_id)
            
            # Execute the query
            try:
                completions = query.all()
            except Exception as e:
                logger.error(f"Error querying audit completions: {e}")
                completions = []

            # --- Ensure all machines with completions are included in the list ---
            machine_ids_with_completions = set(c.machine_id for c in completions)
            machine_ids_in_list = set(m.id for m in machines)
            missing_machine_ids = machine_ids_with_completions - machine_ids_in_list
            if missing_machine_ids:
                # Only add machines the user is allowed to see
                allowed_machine_ids = set(m.id for m in Machine.query.filter(Machine.id.in_(missing_machine_ids)).all())
                # If user is admin, allow all; otherwise, restrict to user's sites
                if not current_user.is_admin and sites:
                    allowed_site_ids = set(site.id for site in sites)
                    allowed_machine_ids = set(m.id for m in Machine.query.filter(
                        Machine.id.in_(missing_machine_ids), 
                        Machine.site_id.in_(allowed_site_ids)).all())
                # Add missing machines
                if allowed_machine_ids:
                    machines += Machine.query.filter(Machine.id.in_(allowed_machine_ids)).all()

            # Get related data for display
            audit_tasks = {task.id: task for task in AuditTask.query.all()}
            machines_dict = {machine.id: machine for machine in Machine.query.all()}
            users = {user.id: user for user in User.query.all()}
            
            # Group completions by date for better display
            grouped_completions = {}
            for completion in completions:
                date_str = completion.date.strftime('%Y-%m-%d')
                if date_str not in grouped_completions:
                    grouped_completions[date_str] = []
                grouped_completions[date_str].append(completion)
            
            # Build machine_data dictionary with proper structure
            machine_data = {}
            for completion in completions:
                machine_id = completion.machine_id
                date_str = completion.date.strftime('%Y-%m-%d')
                
                # Ensure machine_id exists in machine_data
                if machine_id not in machine_data:
                    machine_data[machine_id] = {}
                    
                # Ensure date_str exists in machine_data[machine_id]
                if date_str not in machine_data[machine_id]:
                    machine_data[machine_id][date_str] = []
                
                # Add completion to the machine_data dictionary
                machine_data[machine_id][date_str].append(completion)
            
            # Sort dates in reverse chronological order
            sorted_dates = sorted(grouped_completions.keys(), reverse=True)
            
            # Flag for if we only have a single site (to hide site dropdown)
            show_site_dropdown = len(sites) > 1 or current_user.is_admin
            
            # Define helper function for template
            def get_date_range(start, end):
                """Get a list of dates between start and end, inclusive."""
                delta = end - start
                return [start + timedelta(days=i) for i in range(delta.days + 1)]
            
            # Define helper function for template
            def get_calendar_weeks(start, end):
                """Get calendar weeks for the date range."""
                # Find the first Sunday before or on the start date
                first_day = start - timedelta(days=start.weekday() + 1)
                if first_day.weekday() != 6:  # If not Sunday
                    first_day = start - timedelta(days=(start.weekday() + 1) % 7)
                
                # Find the last Saturday after or on the end date
                last_day = end + timedelta(days=(5 - end.weekday()) % 7)
                
                # Generate weeks
                weeks = []
                current = first_day
                while current <= last_day:
                    week = []
                    for _ in range(7):
                        week.append(current if current >= start and current <= end else None)
                        current = current + timedelta(days=1)
                    weeks.append(week)
                
                return weeks
            
            return render_template('audit_history.html', 
                                completions=completions,
                                grouped_completions=grouped_completions,
                                sorted_dates=sorted_dates,
                                audit_tasks=audit_tasks,
                                machines=machines_dict,
                                available_machines=machines,
                                users=users,
                                sites=sites,
                                selected_site=site_id,
                                selected_machine=machine_id,
                                start_date=start_date,
                                end_date=end_date,
                                today=today,
                                show_site_dropdown=show_site_dropdown,
                                machine_data=machine_data,
                                get_date_range=get_date_range,
                                get_calendar_weeks=get_calendar_weeks)
        
        # Replace the original functions with our fixed versions
        try:
            from app import admin_audit_history
            app.view_functions['admin_audit_history'] = fixed_admin_audit_history
            logger.info("Successfully patched admin_audit_history function")
        except (ImportError, AttributeError) as e:
            logger.warning(f"Could not patch admin_audit_history: {e}")
            
        try:
            from app import audit_history_page
            app.view_functions['audit_history_page'] = fixed_audit_history_page
            logger.info("Successfully patched audit_history_page function")
        except (ImportError, AttributeError) as e:
            logger.warning(f"Could not patch audit_history_page: {e}")
            
        return True
        
    except ImportError as e:
        logger.error(f"Failed to import necessary modules: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to patch audit history functions: {e}")
        return False

# The patch will be applied when this module is imported
patch_successful = patch_audit_history_functions()

if patch_successful:
    print("[AUDIT HISTORY] Successfully patched audit history functions")
else:
    print("[AUDIT HISTORY] Failed to patch audit history functions")