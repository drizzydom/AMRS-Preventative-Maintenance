#!/usr/bin/env python
"""
Enhanced fix for audit history page issues - v2
This script provides a more comprehensive fix for audit history functionality
by completely replacing the problematic audit_history_page route handler.
"""
import os
import sys
import traceback
import logging
from datetime import datetime, timedelta, date
from calendar import monthrange

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("fix_audit_history_v2")

def safe_get_attribute(obj, attr, default=None):
    """Safely get an attribute from an object, return default if not found."""
    if obj is None:
        return default
    try:
        return getattr(obj, attr, default)
    except Exception:
        return default

def fix_audit_task_machine_ids(session):
    """
    Fix audit task completions with missing machine IDs by finding them
    from their parent audit task relationships.
    
    Returns:
        tuple: (fixed_count, remaining_count)
    """
    from models import AuditTaskCompletion, AuditTask

    try:
        # Find completions with missing machine_id but valid audit_task_id
        missing_machine_id_completions = session.query(AuditTaskCompletion).filter(
            AuditTaskCompletion.machine_id.is_(None),
            AuditTaskCompletion.audit_task_id.isnot(None)
        ).all()
        
        if not missing_machine_id_completions:
            logger.info("No audit completions with missing machine IDs found")
            return 0, 0
        
        # Get relevant audit tasks
        task_ids = [c.audit_task_id for c in missing_machine_id_completions if c.audit_task_id]
        task_ids = list(set(task_ids))  # deduplicate
        tasks_dict = {}
        
        # Map task_id to first machine in the task's machines relationship
        for task_id in task_ids:
            task = session.query(AuditTask).get(task_id)
            if task and task.machines and len(task.machines) > 0:
                # Use the first machine in the relationship
                tasks_dict[task.id] = task.machines[0].id
        
        # Fix completions with missing machine_id
        fixed_count = 0
        for completion in missing_machine_id_completions:
            if completion.audit_task_id in tasks_dict:
                completion.machine_id = tasks_dict[completion.audit_task_id]
                fixed_count += 1
        
        # Commit changes if any fixes were made
        if fixed_count > 0:
            session.commit()
        
        # Count remaining issues
        remaining_count = len(missing_machine_id_completions) - fixed_count
        return fixed_count, remaining_count
        
    except Exception as e:
        logger.error(f"Error fixing machine IDs: {e}")
        logger.error(traceback.format_exc())
        session.rollback()
        return 0, 0

def setup_enhanced_audit_history():
    """
    Replace the audit_history_page route handler with an improved version.
    """
    try:
        # Import at function level to avoid import errors
        from app import app, db
        from models import AuditTaskCompletion, AuditTask, Machine, User, Site, Role
        from flask import render_template, flash, redirect, url_for, request, jsonify, abort, current_app
        from flask_login import current_user, login_required
        from sqlalchemy import func, or_
    
        logger.info("Applying enhanced audit history fixes")
        
        # First, fix any audit completions with missing machine IDs
        with app.app_context():
            try:
                fixed_count, remaining_count = fix_audit_task_machine_ids(db.session)
                if fixed_count > 0:
                    logger.info(f"Fixed {fixed_count} audit completions with missing machine IDs")
                if remaining_count > 0:
                    logger.warning(f"{remaining_count} audit completions still have missing machine IDs")
            except Exception as e:
                logger.error(f"Error fixing audit machine IDs: {e}")
                logger.error(traceback.format_exc())
                
        # Define enhanced audit history page function
        @login_required
        def enhanced_audit_history_page():
            try:
                # Detailed debug logging
                logger.info("Starting enhanced_audit_history_page function")
                request_args = ', '.join([f"{k}={v}" for k, v in request.args.items()])
                logger.info(f"Request args: {request_args}")
                
                # --- Permission check ---
                if current_user.is_admin:
                    can_access = True
                else:
                    if hasattr(current_user, 'role') and current_user.role:
                        logger.debug(f"User role type: {type(current_user.role)}")
                        if hasattr(current_user.role, 'name'):
                            # Role is an object
                            role_name = current_user.role.name
                            permissions = (current_user.role.permissions or '').replace(' ', '').split(',')
                            logger.debug(f"User role name: {role_name}, permissions: {permissions}")
                        else:
                            # Role is a string
                            role_name = str(current_user.role)
                            user_role = Role.query.filter_by(name=role_name).first()
                            if user_role:
                                permissions = (user_role.permissions or '').replace(' ', '').split(',')
                            else:
                                permissions = []
                            logger.debug(f"String role: {role_name}, found: {user_role is not None}, permissions: {permissions}")
                    else:
                        permissions = []
                        logger.debug("No role assigned to user")
                    
                    can_access = 'audits.access' in permissions
                
                if not can_access:
                    logger.warning(f"User {current_user.username} denied access to audit history")
                    flash('You do not have permission to access audit history.', 'danger')
                    return redirect(url_for('dashboard'))

                logger.info("Permission check passed")
                
                # --- Date handling ---
                today = datetime.now().date()
                month_year = request.args.get('month_year', '')
                
                if month_year:
                    try:
                        year, month = map(int, month_year.split('-'))
                        logger.debug(f"Parsed year={year}, month={month} from month_year={month_year}")
                    except Exception as e:
                        logger.warning(f"Error parsing month_year parameter: {e}")
                        month = today.month
                        year = today.year
                else:
                    month = today.month
                    year = today.year
                
                first_day = date(year, month, 1)
                last_day = date(year, month, monthrange(year, month)[1])
                logger.info(f"Date range: {first_day} to {last_day}")
                
                # --- Site and machine filters ---
                site_id = request.args.get('site_id', type=int)
                machine_id_param = request.args.get('machine_id', '')
                logger.debug(f"Raw machine_id param: {machine_id_param}")
                
                # Handle machine_id conversion safely
                try:
                    machine_id = int(machine_id_param) if machine_id_param.strip() else None
                except (ValueError, AttributeError):
                    machine_id = None
                    
                logger.info(f"Filters: site_id={site_id}, machine_id={machine_id}")
                
                # --- Site access restrictions ---
                if current_user.is_admin:
                    sites = Site.query.all()
                    logger.info(f"Admin user: Found {len(sites)} sites")
                    show_site_dropdown = len(sites) > 1
                else:
                    if hasattr(current_user, 'sites'):
                        user_site_ids = [site.id for site in current_user.sites]
                        sites = current_user.sites
                        logger.info(f"Standard user: Found {len(sites)} assigned sites")
                        # For non-admins, verify site_id is in their allowed sites
                        if site_id and site_id not in user_site_ids:
                            site_id = user_site_ids[0] if user_site_ids else None
                            logger.warning(f"User tried to access unauthorized site, defaulting to {site_id}")
                    else:
                        logger.warning("User has no sites attribute, defaulting to empty list")
                        sites = []
                    
                    show_site_dropdown = len(sites) > 1
                
                # If only one site and no site selected, use that site
                if len(sites) == 1 and not site_id:
                    site_id = sites[0].id
                    logger.debug(f"Only one site available, automatically selecting site_id={site_id}")
                
                # --- Available machines for selected site ---
                logger.info("Getting available machines based on site filter")
                if site_id:
                    available_machines = Machine.query.filter_by(site_id=site_id).all()
                    logger.debug(f"Found {len(available_machines)} machines for site_id={site_id}")
                else:
                    if not current_user.is_admin and sites:
                        site_ids = [site.id for site in sites]
                        available_machines = Machine.query.filter(Machine.site_id.in_(site_ids)).all()
                        logger.debug(f"Found {len(available_machines)} machines across {len(site_ids)} user sites")
                    else:
                        available_machines = Machine.query.all()
                        logger.debug(f"Admin user or no sites filter: Found {len(available_machines)} total machines")
                
                # --- Query completions with proper filters ---
                logger.info("Building audit task completion query")
                query = AuditTaskCompletion.query.filter(
                    AuditTaskCompletion.date >= first_day,
                    AuditTaskCompletion.date <= last_day,
                    AuditTaskCompletion.completed == True  # Only show completed tasks
                )
                
                # Apply site filter via task relationship if site_id provided
                if site_id:
                    logger.debug(f"Adding site_id={site_id} filter")
                    site_audit_tasks = AuditTask.query.filter_by(site_id=site_id).all()
                    task_ids = [task.id for task in site_audit_tasks]
                    
                    if task_ids:
                        logger.debug(f"Found {len(task_ids)} audit tasks for site_id={site_id}")
                        query = query.filter(AuditTaskCompletion.audit_task_id.in_(task_ids))
                    else:
                        logger.warning(f"No audit tasks found for site_id={site_id}")
                        return render_template('audit_history.html',
                            completions=[],
                            month=month,
                            year=year,
                            month_weeks=[],
                            machine_data={},
                            audit_tasks={},
                            unique_tasks=[],
                            machines={},
                            users={},
                            sites=sites,
                            selected_site=site_id,
                            selected_machine=machine_id,
                            current_month=month,
                            current_year=year,
                            display_month=f"{datetime(year, month, 1).strftime('%B %Y')}",
                            available_machines=available_machines,
                            available_months=[],
                            selected_month=f"{year:04d}-{month:02d}",
                            today=today,
                            display_machines=[],
                            show_site_dropdown=show_site_dropdown
                        )
                # For non-admin users, restrict to their assigned sites
                elif not current_user.is_admin and sites:
                    logger.debug("Adding site restriction for non-admin user")
                    site_ids = [site.id for site in sites]
                    site_audit_tasks = AuditTask.query.filter(AuditTask.site_id.in_(site_ids)).all()
                    task_ids = [task.id for task in site_audit_tasks]
                    
                    if task_ids:
                        logger.debug(f"Found {len(task_ids)} audit tasks for user's sites")
                        query = query.filter(AuditTaskCompletion.audit_task_id.in_(task_ids))
                    else:
                        logger.warning("No audit tasks found for user's sites")
                        return render_template('audit_history.html',
                            completions=[],
                            month=month,
                            year=year,
                            month_weeks=[],
                            machine_data={},
                            audit_tasks={},
                            unique_tasks=[],
                            machines={},
                            users={},
                            sites=sites,
                            selected_site=site_id,
                            selected_machine=machine_id,
                            current_month=month,
                            current_year=year,
                            display_month=f"{datetime(year, month, 1).strftime('%B %Y')}",
                            available_machines=available_machines,
                            available_months=[],
                            selected_month=f"{year:04d}-{month:02d}",
                            today=today,
                            display_machines=[],
                            show_site_dropdown=show_site_dropdown
                        )
                
                # Apply machine filter if machine_id provided
                if machine_id:
                    logger.debug(f"Adding machine_id={machine_id} filter")
                    query = query.filter(AuditTaskCompletion.machine_id == machine_id)
                
                # Execute query and handle empty results
                try:
                    completions = query.all()
                    logger.info(f"Found {len(completions)} audit completions matching criteria")
                except Exception as e:
                    logger.error(f"Error executing audit completions query: {e}")
                    logger.error(traceback.format_exc())
                    completions = []
                
                # --- Build calendar data ---
                import calendar
                cal = calendar.Calendar(firstweekday=6)  # Sunday start
                month_weeks = list(cal.monthdayscalendar(year, month))
                logger.debug(f"Generated {len(month_weeks)} weeks for calendar")
                
                # --- Build machine_data structure ---
                logger.info("Building machine_data structure for template")
                machine_data = {}
                for completion in completions:
                    # Skip completions with missing machine_id
                    if completion.machine_id is None:
                        logger.warning(f"Skipping completion id={completion.id} with missing machine_id")
                        continue
                        
                    try:
                        m_id = completion.machine_id
                        d = completion.date
                        day_str = f"{d.year:04d}-{d.month:02d}-{d.day:02d}"
                        
                        if m_id not in machine_data:
                            machine_data[m_id] = {}
                        if day_str not in machine_data[m_id]:
                            machine_data[m_id][day_str] = []
                            
                        machine_data[m_id][day_str].append(completion)
                    except Exception as e:
                        logger.error(f"Error processing completion {completion.id}: {e}")
                
                # --- Generate auxiliary data for template ---
                logger.debug("Preparing auxiliary data for template")
                audit_tasks = {task.id: task for task in AuditTask.query.all()}
                
                # Get unique tasks for the legend
                unique_task_ids = set()
                for completion in completions:
                    if completion.audit_task_id in audit_tasks:
                        unique_task_ids.add(completion.audit_task_id)
                unique_tasks = [audit_tasks[task_id] for task_id in unique_task_ids]
                
                # Get machine data for display
                try:
                    machines_dict = {machine.id: machine for machine in Machine.query.all()}
                    users = {user.id: user for user in User.query.all()}
                    
                    # Prepare the list of machines to display
                    display_machines = []
                    # First add machines that have completions
                    for machine_id in machine_data.keys():
                        if machine_id in machines_dict:
                            display_machines.append(machines_dict[machine_id])
                            
                    # If specific machine selected but not in display_machines, add it
                    if machine_id and machine_id not in [m.id for m in display_machines]:
                        machine = Machine.query.get(machine_id)
                        if machine:
                            display_machines.append(machine)
                            
                    # If no machines with completions, show machines for dropdown
                    if not display_machines:
                        logger.info("No machines with completions found")
                        # If specific site selected, show machines for that site
                        if site_id:
                            site_machines = [m for m in available_machines if m.site_id == site_id]
                            if site_machines:
                                display_machines = site_machines
                        else:
                            # Just use all available machines
                            display_machines = available_machines
                except Exception as e:
                    logger.error(f"Error preparing machine data: {e}")
                    logger.error(traceback.format_exc())
                    display_machines = []
                    machines_dict = {}
                    users = {}
                
                # --- Generate available months for dropdown ---
                logger.debug("Generating available months for dropdown")
                # Start from April 2025 (to ensure we only include months with data)
                start_month, start_year = 4, 2025
                available_months = []

                # Get current date for comparison
                curr_date = datetime.now().date()

                # Generate months from start date through current month/year plus a few future months
                current_year, current_month = curr_date.year, curr_date.month

                # Add a few months into the future for planning purposes
                future_months = 3
                end_date = curr_date.replace(day=1)
                if current_month + future_months > 12:
                    future_year = current_year + ((current_month + future_months) // 12)
                    future_month = (current_month + future_months) % 12
                    if future_month == 0:
                        future_month = 12
                else:
                    future_year = current_year
                    future_month = current_month + future_months
                end_date = date(future_year, future_month, 1)

                # Generate the dropdown options
                temp_date = date(start_year, start_month, 1)

                # Loop through months until we reach end date
                while temp_date <= end_date:
                    m = temp_date.month
                    y = temp_date.year
                    value = f"{y:04d}-{m:02d}"
                    display = f"{calendar.month_name[m]} {y}"
                    available_months.append({'value': value, 'display': display})
                    
                    # Move to next month
                    if m == 12:
                        temp_date = date(y + 1, 1, 1)
                    else:
                        temp_date = date(y, m + 1, 1)

                # Debug output
                logger.info(f"Generated {len(available_months)} months for dropdown")
                for month in available_months:
                    logger.debug(f"Available month: {month['display']} ({month['value']})")

                # Sort in reverse chronological order (newest first)
                available_months = sorted(available_months, key=lambda x: x['value'], reverse=True)
                
                # Safety check - if somehow we have no months, add current month as fallback
                if not available_months:
                    logger.warning("No months were generated - adding current month as fallback")
                    available_months.append({
                        'value': f"{current_year:04d}-{current_month:02d}",
                        'display': f"{calendar.month_name[current_month]} {current_year}"
                    })

                # Ensure the selected month exists in available months
                selected_month = f"{year:04d}-{month:02d}"
                month_exists = any(m['value'] == selected_month for m in available_months)

                if not month_exists:
                    # If selected month isn't in our list, add it
                    logger.warning(f"Selected month {selected_month} not in available months - adding it")
                    available_months.append({
                        'value': selected_month,
                        'display': f"{calendar.month_name[month]} {year}"
                    })
                    # Re-sort after adding
                    available_months = sorted(available_months, key=lambda x: x['value'], reverse=True)
                
                selected_month = f"{year:04d}-{month:02d}"
                
                # Format for display in template
                display_month = datetime(year, month, 1).strftime('%B %Y')
                
                # --- Render template with all data ---
                logger.info("Rendering audit_history template")
                return render_template('audit_history.html',
                    completions=completions,
                    month=month,
                    year=year,
                    month_weeks=month_weeks,
                    machine_data=machine_data,
                    audit_tasks=audit_tasks,
                    unique_tasks=unique_tasks,
                    machines=machines_dict,
                    users=users,
                    sites=sites,
                    selected_site=site_id,
                    selected_machine=machine_id,
                    current_month=month,
                    current_year=year,
                    display_month=display_month,
                    available_machines=available_machines,
                    available_months=available_months,
                    selected_month=selected_month,
                    today=today,
                    display_machines=display_machines,
                    show_site_dropdown=show_site_dropdown
                )
                
            except Exception as e:
                logger.error(f"Error in enhanced_audit_history_page: {e}")
                logger.error(traceback.format_exc())
                flash(f'An error occurred processing audit history: {str(e)}', 'danger')
                return redirect(url_for('dashboard'))
        
        # Replace the existing function with our enhanced version
        app.view_functions['audit_history_page'] = enhanced_audit_history_page
        logger.info("Successfully installed enhanced audit_history_page function")
        
        # Add a debug endpoint to help diagnose issues
        @app.route('/debug/audit-history-data')
        @login_required
        def debug_audit_history_data():
            if not current_user.is_admin:
                return jsonify({"error": "Admin access required"}), 403
                
            try:
                # Get basic stats about audit data
                completion_count = db.session.query(func.count(AuditTaskCompletion.id)).scalar()
                missing_machine_count = db.session.query(func.count(AuditTaskCompletion.id))\
                    .filter(AuditTaskCompletion.machine_id.is_(None)).scalar()
                
                # Sample some recent completions
                recent = AuditTaskCompletion.query.order_by(AuditTaskCompletion.id.desc()).limit(5).all()
                recent_data = []
                for r in recent:
                    recent_data.append({
                        "id": r.id,
                        "date": str(r.date),
                        "audit_task_id": r.audit_task_id,
                        "machine_id": r.machine_id,
                        "completed": r.completed,
                        "completed_by": r.completed_by,
                        "completed_at": str(r.completed_at) if r.completed_at else None
                    })
                    
                # Get machine counts
                machine_count = db.session.query(func.count(Machine.id)).scalar()
                
                return jsonify({
                    "audit_completion_count": completion_count,
                    "missing_machine_id_count": missing_machine_count,
                    "machine_count": machine_count,
                    "recent_completions": recent_data
                })
                
            except Exception as e:
                logger.error(f"Error in debug endpoint: {str(e)}")
                return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500
                
        # Register the debug endpoint
        app.route('/debug/audit-history-data')(debug_audit_history_data)
        logger.info("Registered debug endpoint at /debug/audit-history-data")
        
        # Add a specific endpoint to debug the month dropdown issue
        @app.route('/debug/audit-history-months')
        @login_required
        def debug_audit_history_months():
            if not current_user.is_admin:
                return jsonify({"error": "Admin access required"}), 403
                
            try:
                import calendar
                from datetime import datetime, date
                
                # Debug info about dates
                curr_date = datetime.now().date()
                
                # Use April 2025 as starting point (first month with data)
                start_month, start_year = 4, 2025
                available_months = []
                
                # Add a few months into the future for planning purposes
                future_months = 3
                current_month, current_year = curr_date.month, curr_date.year
                
                if current_month + future_months > 12:
                    future_year = current_year + ((current_month + future_months) // 12)
                    future_month = (current_month + future_months) % 12
                    if future_month == 0:
                        future_month = 12
                else:
                    future_year = current_year
                    future_month = current_month + future_months
                end_date = date(future_year, future_month, 1)
                
                # Generate the dropdown options
                temp_date = date(start_year, start_month, 1)
                
                # Store all generated month information for debugging
                month_generation = []
                
                # Loop through months until we reach end date
                while temp_date <= end_date:
                    m = temp_date.month
                    y = temp_date.year
                    value = f"{y:04d}-{m:02d}"
                    display = f"{calendar.month_name[m]} {y}"
                    
                    available_months.append({'value': value, 'display': display})
                    month_generation.append({
                        'month': m,
                        'year': y,
                        'value': value,
                        'display': display,
                        'date': str(temp_date)
                    })
                    
                    # Move to next month
                    if m == 12:
                        temp_date = date(y + 1, 1, 1)
                    else:
                        temp_date = date(y, m + 1, 1)
                
                # Sort in reverse chronological order (newest first)
                available_months = sorted(available_months, key=lambda x: x['value'], reverse=True)
                
                # Check for any recent audit completions to verify data exists
                recent_months = db.session.query(
                    func.extract('year', AuditTaskCompletion.date).label('year'),
                    func.extract('month', AuditTaskCompletion.date).label('month'),
                    func.count().label('count')
                ).group_by(
                    func.extract('year', AuditTaskCompletion.date),
                    func.extract('month', AuditTaskCompletion.date)
                ).order_by(
                    func.extract('year', AuditTaskCompletion.date).desc(),
                    func.extract('month', AuditTaskCompletion.date).desc()
                ).limit(5).all()
                
                recent_month_data = [{'year': int(r.year), 'month': int(r.month), 'count': r.count} for r in recent_months]
                
                return jsonify({
                    "current_date": str(curr_date),
                    "start_date": f"{start_year}-{start_month:02d}-01",
                    "end_date": str(end_date),
                    "month_generation_steps": month_generation,
                    "final_available_months": [f"{m['display']} ({m['value']})" for m in available_months],
                    "recent_audit_completions_by_month": recent_month_data
                })
                
            except Exception as e:
                logger.error(f"Error in debug months endpoint: {str(e)}")
                return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500
                
        # Register the months debug endpoint
        app.route('/debug/audit-history-months')(debug_audit_history_months)
        logger.info("Registered months debug endpoint at /debug/audit-history-months")
        
        return True
        
    except ImportError as e:
        logger.error(f"Failed to import necessary modules: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to set up enhanced audit history: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("Running enhanced audit history fix...")
    success = setup_enhanced_audit_history()
    print("Fix applied successfully!" if success else "Failed to apply fix!")
    sys.exit(0 if success else 1)