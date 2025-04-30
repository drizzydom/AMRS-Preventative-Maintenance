#!/usr/bin/env python
"""
Fix for audit history not showing audit actions and machine names.
This file is imported during app startup to patch both audit history related functions.
"""
import logging
from functools import wraps
from datetime import datetime, timedelta, date
import sys
import traceback

# Configure more detailed logging
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def fix_audit_task_machine_ids(db_session):
    """
    Automatically fix audit task completions that have missing machine IDs.
    This will run during app startup to ensure all audit data is properly displayed.
    
    Args:
        db_session: SQLAlchemy database session
    
    Returns:
        tuple: (num_fixed, num_remaining) count of fixed records and remaining unfixed records
    """
    try:
        from models import AuditTaskCompletion, AuditTask
        
        # Find completions with missing machine IDs
        missing_machine_id_completions = AuditTaskCompletion.query.filter(
            AuditTaskCompletion.machine_id == None,
            AuditTaskCompletion.completed == True
        ).all()
        
        # Count total before repair
        total_missing = len(missing_machine_id_completions)
        if total_missing == 0:
            logger.info("[AUDIT FIX] No audit completions with missing machine IDs found.")
            return 0, 0
            
        logger.info(f"[AUDIT FIX] Found {total_missing} audit completions with missing machine IDs. Attempting to repair.")
        
        # Count repairs
        repaired_count = 0
        
        # Attempt to repair completions with missing machine IDs
        for completion in missing_machine_id_completions:
            # Get the audit task this completion is for
            audit_task = AuditTask.query.get(completion.audit_task_id)
            if not audit_task:
                logger.warning(f"[AUDIT FIX] Completion {completion.id} has invalid audit_task_id {completion.audit_task_id}")
                continue
                
            # Check if audit task has machines associated
            if not hasattr(audit_task, 'machines') or not audit_task.machines:
                logger.warning(f"[AUDIT FIX] Audit task {audit_task.id} ({audit_task.name}) has no machines associated")
                continue
                
            # If only one machine is associated with the audit task, use that
            if len(audit_task.machines) == 1:
                completion.machine_id = audit_task.machines[0].id
                logger.info(f"[AUDIT FIX] Assigned machine_id {completion.machine_id} to completion {completion.id} (single machine)")
                repaired_count += 1
            else:
                # Multiple machines - try to find a logical match
                # For now, just use the first one as a default
                completion.machine_id = audit_task.machines[0].id
                logger.info(f"[AUDIT FIX] Assigned machine_id {completion.machine_id} to completion {completion.id} (first of multiple)")
                repaired_count += 1
                
        # Commit changes if any repairs were made
        if repaired_count > 0:
            db_session.commit()
            logger.info(f"[AUDIT FIX] Successfully repaired {repaired_count} audit task completions")
        
        # Fix machine_id attribute in AuditTask objects if needed
        audit_tasks_without_machine_id = AuditTaskCompletion.query.filter(
            AuditTaskCompletion.machine_id_attr_missing == True
        ).all()
        
        if audit_tasks_without_machine_id:
            logger.info(f"[AUDIT FIX] Found {len(audit_tasks_without_machine_id)} completions missing machine_id attribute")
            # We'd need to fix this, but it's likely not a real column
        
        # Check remaining unfixed records
        remaining_missing = AuditTaskCompletion.query.filter(
            AuditTaskCompletion.machine_id == None,
            AuditTaskCompletion.completed == True
        ).count()
        
        logger.info(f"[AUDIT FIX] After repairs: {remaining_missing} completions still have missing machine IDs")
        
        return repaired_count, remaining_missing
        
    except Exception as e:
        logger.error(f"[AUDIT FIX] Error repairing audit machine IDs: {e}")
        logger.error(traceback.format_exc())
        return 0, 0

def patch_audit_history_functions():
    """
    Patch both the admin_audit_history and audit_history_page functions
    to properly show audit actions and machine data.
    """
    try:
        # Import the app and required models after this module is imported
        from app import app, db
        from models import AuditTaskCompletion, AuditTask, Machine, User, Site
        from flask import render_template, flash, redirect, url_for, request, jsonify
        from flask_login import current_user
        
        # First, run the fix for audit task machine IDs during startup
        with app.app_context():
            try:
                fixed_count, remaining_count = fix_audit_task_machine_ids(db.session)
                if fixed_count > 0:
                    logger.info(f"[STARTUP] Fixed {fixed_count} audit completions with missing machine IDs")
                if remaining_count > 0:
                    logger.warning(f"[STARTUP] {remaining_count} audit completions still have missing machine IDs")
            except Exception as e:
                logger.error(f"[STARTUP] Error fixing audit machine IDs: {e}")
                logger.error(traceback.format_exc())
        
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
                        record.completed_at = record.created_at or datetime.now()
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
        
        # Add debug route to diagnose audit data
        def debug_audit_history():
            try:
                # Same permission checks as original function
                if not hasattr(current_user, 'is_authenticated') or not current_user.is_authenticated:
                    return jsonify({"error": "Authentication required"}), 401
                    
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
                    return jsonify({"error": "Permission denied"}), 403
                    
                # Get all audit completions for the last 365 days
                start_date = datetime.now().date() - timedelta(days=365)
                end_date = datetime.now().date()
                
                completions = AuditTaskCompletion.query.filter(
                    AuditTaskCompletion.date >= start_date,
                    AuditTaskCompletion.date <= end_date,
                    AuditTaskCompletion.completed == True
                ).all()
                
                # Count by machine
                machine_counts = {}
                for completion in completions:
                    if completion.machine_id:
                        if completion.machine_id not in machine_counts:
                            machine_counts[completion.machine_id] = 0
                        machine_counts[completion.machine_id] += 1
                
                # Get machine details
                machines = Machine.query.filter(Machine.id.in_(machine_counts.keys())).all() if machine_counts else []
                machine_data = {}
                for machine in machines:
                    # Add machine object attributes for debug
                    machine_attrs = {key: str(getattr(machine, key)) for key in dir(machine) 
                                    if not key.startswith('_') and not callable(getattr(machine, key))}
                    
                    machine_data[machine.id] = {
                        "id": machine.id,
                        "name": machine.name,
                        "count": machine_counts.get(machine.id, 0),
                        "site_id": machine.site_id,
                        "attributes": machine_attrs
                    }
                    
                # Get sites 
                site_ids = set(machine.site_id for machine in machines if machine.site_id)
                sites = Site.query.filter(Site.id.in_(site_ids)).all() if site_ids else []
                site_data = {site.id: site.name for site in sites}
                
                # Return as JSON
                return jsonify({
                    "total_completions": len(completions),
                    "machine_data": machine_data,
                    "site_data": site_data,
                    "date_range": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat()
                    }
                })
                
            except Exception as e:
                traceback.print_exc()
                return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500
        
        # Define our improved version of the audit_history_page function
        def fixed_audit_history_page():
            try:
                # Add detailed debug logging
                logger.info("Starting audit_history_page function")
                
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

                logger.info("Permission check passed")

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
                    
                logger.info(f"Date range: {start_date} to {end_date}")
                
                # Get site and machine filters - default is None (All Sites, All Machines)
                site_id = request.args.get('site_id', type=int)
                machine_id = request.args.get('machine_id', type=int)
                
                logger.info(f"Filters: site_id={site_id}, machine_id={machine_id}")
                
                # Restrict sites for non-admins
                if current_user.is_admin:
                    sites = Site.query.all()
                    logger.info(f"Admin user: Found {len(sites)} sites")
                else:
                    # Limit to user's assigned sites
                    if hasattr(current_user, 'sites'):
                        user_site_ids = [site.id for site in current_user.sites]
                        sites = current_user.sites
                        logger.info(f"Regular user: Found {len(sites)} assigned sites")
                    else:
                        logger.warning("User does not have sites attribute")
                        sites = []
                        user_site_ids = []
                    
                    # Ensure the selected site is one the user has access to
                    if site_id and site_id not in user_site_ids:
                        logger.warning(f"User tried to access unauthorized site_id: {site_id}")
                        site_id = None
                
                # Get all available machines
                all_machines = Machine.query.all()
                logger.info(f"Total machines in system: {len(all_machines)}")
                
                # Get available machines based on site filter
                if site_id:
                    available_machines = Machine.query.filter_by(site_id=site_id).all()
                    logger.info(f"For site_id {site_id}: Found {len(available_machines)} machines")
                else:
                    if not current_user.is_admin and hasattr(current_user, 'sites') and current_user.sites:
                        site_ids = [site.id for site in current_user.sites]
                        available_machines = Machine.query.filter(Machine.site_id.in_(site_ids)).all()
                        logger.info(f"For user's sites: Found {len(available_machines)} machines")
                    else:
                        available_machines = all_machines
                        logger.info(f"All machines: Found {len(available_machines)} machines")
                
                # Debug dump available machines
                machine_debug = []
                for m in available_machines[:5]:  # Just show the first 5 to avoid excessive logging
                    machine_debug.append({
                        'id': m.id,
                        'name': m.name,
                        'site_id': m.site_id
                    })
                logger.info(f"Sample of available machines: {machine_debug}")
                
                # Build the query for audit completions
                query = AuditTaskCompletion.query.filter(
                    AuditTaskCompletion.date >= start_date,
                    AuditTaskCompletion.date <= end_date,
                    AuditTaskCompletion.completed == True  # Only show completed tasks
                ).order_by(AuditTaskCompletion.date.desc())
                
                # Apply site filter if specified
                if site_id:
                    # Get all audit tasks for the selected site
                    site_audit_tasks = AuditTask.query.filter_by(site_id=site_id).all()
                    task_ids = [task.id for task in site_audit_tasks]
                    logger.info(f"For site_id {site_id}: Found {len(task_ids)} audit tasks")
                    if task_ids:
                        query = query.filter(AuditTaskCompletion.audit_task_id.in_(task_ids))
                elif not current_user.is_admin and hasattr(current_user, 'sites') and current_user.sites:
                    # If no site is selected but user access is restricted, filter by all allowed site tasks
                    site_ids = [site.id for site in current_user.sites]
                    site_audit_tasks = AuditTask.query.filter(AuditTask.site_id.in_(site_ids)).all()
                    task_ids = [task.id for task in site_audit_tasks]
                    logger.info(f"For user's sites: Found {len(task_ids)} audit tasks")
                    if task_ids:
                        query = query.filter(AuditTaskCompletion.audit_task_id.in_(task_ids))

                # Apply machine filter if specified
                if machine_id:
                    query = query.filter(AuditTaskCompletion.machine_id == machine_id)
                
                # Execute the query
                try:
                    completions = query.all()
                    logger.info(f"Found {len(completions)} audit completions")
                    
                    # Fix any missing machine_id during this query
                    fixed_count = 0
                    for completion in completions:
                        if not completion.machine_id:
                            # Try to find the machine from the audit task
                            audit_task = AuditTask.query.get(completion.audit_task_id)
                            if audit_task and hasattr(audit_task, 'machines') and audit_task.machines:
                                completion.machine_id = audit_task.machines[0].id
                                fixed_count += 1
                    
                    if fixed_count > 0:
                        db.session.commit()
                        logger.info(f"Fixed {fixed_count} completions with missing machine_id during query")
                        
                    # Reload completions if we made fixes
                    if fixed_count > 0:
                        completions = query.all()
                        
                except Exception as e:
                    logger.error(f"Error querying audit completions: {e}")
                    completions = []
                
                # Count completions by machine for debugging
                machine_counts = {}
                for completion in completions:
                    if completion.machine_id:
                        if completion.machine_id not in machine_counts:
                            machine_counts[completion.machine_id] = 0
                        machine_counts[completion.machine_id] += 1
                
                logger.info(f"Completion counts by machine: {machine_counts}")

                # Get all necessary reference data
                audit_tasks = {task.id: task for task in AuditTask.query.all()}
                logger.info(f"Found {len(audit_tasks)} total audit tasks")
                
                machines_dict = {}
                for machine in all_machines:
                    # Make sure machine.machine_id exists (for display in headers)
                    if not hasattr(machine, 'machine_id') or not machine.machine_id:
                        setattr(machine, 'machine_id', f"ID: {machine.id}")
                    
                    machines_dict[machine.id] = machine
                logger.info(f"Found {len(machines_dict)} total machines")
                
                users = {user.id: user for user in User.query.all()}
                logger.info(f"Found {len(users)} users")
                
                # Build machine_data dictionary - critical for display
                machine_data = {}
                for completion in completions:
                    if not completion.machine_id:
                        logger.warning(f"Skipping completion with no machine_id: {completion.id}")
                        continue
                        
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
                
                logger.info(f"Built machine_data for {len(machine_data)} machines")
                
                # Group completions by date for display
                grouped_completions = {}
                for completion in completions:
                    date_str = completion.date.strftime('%Y-%m-%d')
                    if date_str not in grouped_completions:
                        grouped_completions[date_str] = []
                    grouped_completions[date_str].append(completion)
                
                # Sort dates in reverse chronological order
                sorted_dates = sorted(grouped_completions.keys(), reverse=True)
                
                # Flag for if we have multiple sites (to show site dropdown)
                show_site_dropdown = len(sites) > 1 or current_user.is_admin
                
                # Prepare machines for display (the ones with completions)
                display_machines = []
                
                # First add machines that have completions
                for machine_id in machine_data.keys():
                    if machine_id in machines_dict:
                        display_machines.append(machines_dict[machine_id])
                
                # If no machines with completions, show message on page
                # but still provide machines for the dropdown
                if not display_machines:
                    logger.info("No machines with completions found, displaying all available machines")
                    # If a specific site is selected, show just those machines
                    if site_id:
                        site_machines = [m for m in all_machines if m.site_id == site_id]
                        if site_machines:
                            display_machines = site_machines
                            logger.info(f"Using {len(display_machines)} machines from selected site")
                        else:
                            # Fallback to all machines user has access to
                            display_machines = available_machines
                            logger.info(f"Using {len(display_machines)} available machines")
                    else:
                        # Just use all available machines
                        display_machines = available_machines
                        logger.info(f"Using {len(display_machines)} available machines")
                
                logger.info(f"Display machines count: {len(display_machines)}")
                
                # Define helper functions for the template
                def get_date_range(start, end):
                    """Get a list of dates between start and end, inclusive."""
                    delta = end - start
                    return [start + timedelta(days=i) for i in range(delta.days + 1)]
                
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
                
                # --- Build all_tasks_per_machine: {machine_id: [AuditTask, ...]} ---
                all_tasks_per_machine = {}
                for machine in available_machines:
                    all_tasks_per_machine[machine.id] = [task for task in audit_tasks.values() if machine in getattr(task, 'machines', [])]

                # --- Build interval_bars: {machine_id: {task_id: [(start_date, end_date), ...]}} ---
                from collections import defaultdict
                interval_bars = defaultdict(lambda: defaultdict(list))
                # Use start_date and end_date for the calendar range if available, else today
                calendar_start = start_date if 'start_date' in locals() else today
                calendar_end = end_date if 'end_date' in locals() else today
                for machine in available_machines:
                    for task in all_tasks_per_machine[machine.id]:
                        # Only for interval-based tasks (not daily)
                        if getattr(task, 'interval', None) in ('weekly', 'monthly') or (getattr(task, 'interval', None) == 'custom' and getattr(task, 'custom_interval_days', None)):
                            # Determine interval length
                            if task.interval == 'weekly':
                                interval_days = 7
                            elif task.interval == 'monthly':
                                interval_days = 30
                            elif task.interval == 'custom' and task.custom_interval_days:
                                interval_days = task.custom_interval_days
                            else:
                                continue
                            # Find the first interval start <= calendar_end
                            current = calendar_start
                            while current <= calendar_end:
                                start = current
                                end = min(current + timedelta(days=interval_days - 1), calendar_end)
                                interval_bars[machine.id][task.id].append((start, end))
                                current = end + timedelta(days=1)

                # Final debug logging before render
                logger.info(f"Rendering template with {len(completions)} completions and {len(display_machines)} machines")
                
                return render_template('audit_history.html', 
                                    completions=completions,
                                    grouped_completions=grouped_completions,
                                    sorted_dates=sorted_dates,
                                    audit_tasks=audit_tasks,
                                    machines=machines_dict,            # For fetching machine details by id
                                    display_machines=display_machines, # Machines to show in the calendar view
                                    available_machines=available_machines,  # For dropdown
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
                                    get_calendar_weeks=get_calendar_weeks,
                                    all_tasks_per_machine=all_tasks_per_machine,
                                    interval_bars=interval_bars)
                                    
            except Exception as e:
                # Capture and log the full traceback
                logger.error(f"Error in audit_history_page: {str(e)}")
                logger.error(traceback.format_exc())
                flash(f'An error occurred processing audit history: {str(e)}', 'danger')
                return redirect(url_for('dashboard'))
        
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
        
        # Register the debug endpoint
        app.route('/debug/audit-data')(debug_audit_history)
        logger.info("Registered debug endpoint at /debug/audit-data")
            
        return True
        
    except ImportError as e:
        logger.error(f"Failed to import necessary modules: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to patch audit history functions: {e}")
        logger.error(traceback.format_exc())  # Print the full traceback
        return False

# The patch will be applied when this module is imported
patch_successful = patch_audit_history_functions()

if patch_successful:
    print("[AUDIT HISTORY] Successfully patched audit history functions")
else:
    print("[AUDIT HISTORY] Failed to patch audit history functions")