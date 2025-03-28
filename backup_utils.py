#!/usr/bin/env python3
"""
Utilities for backing up and restoring maintenance data.
"""

import os
import json
import shutil
from datetime import datetime
import time
from flask import current_app, send_from_directory

# Configure backup directory
BACKUP_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'backups')

def ensure_backup_dir():
    """Ensure the backup directory exists."""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        print(f"Created backup directory: {BACKUP_DIR}")

def serialize_datetime(obj):
    """JSON serializer for datetime objects."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def backup_database(backup_name=None, include_users=True):
    """
    Create a backup of the database.
    
    Args:
        include_users (bool): Whether to include user and role data
        backup_name (str): Optional custom name for the backup
    
    Returns:
        str: Path to the backup file
    """
    # Handle case where backup_name is not a string
    if not backup_name or not isinstance(backup_name, str):
        backup_name = datetime.now().strftime("%Y%m%d_%H%M%S")
    else:
        # Only clean up the name if it's actually a string
        backup_name = ''.join(c if c.isalnum() else '_' for c in backup_name)
    
    # Import here to avoid circular imports
    from app import app, db, Site, Machine, Part, MaintenanceLog, User, Role, user_site
    
    with app.app_context():
        ensure_backup_dir()
        
        # Generate backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{backup_name}.json"
        
        backup_path = os.path.join(BACKUP_DIR, filename)
        
        # Create backup data structure
        backup_data = {
            'metadata': {
                'timestamp': timestamp,
                'datetime': datetime.now().isoformat(),
                'include_users': include_users,
                'version': '1.0'
            },
            'sites': [],
            'machines': [],
            'parts': [],
            'maintenance_logs': []
        }
        
        if include_users:
            backup_data['users'] = []
            backup_data['roles'] = []
            backup_data['user_site_assignments'] = []
        
        # Collect data
        # 1. Sites
        sites = Site.query.all()
        for site in sites:
            site_data = {
                'id': site.id,
                'name': site.name,
                'location': site.location,
                'enable_notifications': site.enable_notifications,
                'contact_email': site.contact_email,
                'notification_threshold': site.notification_threshold
            }
            backup_data['sites'].append(site_data)
        
        # 2. Machines
        machines = Machine.query.all()
        for machine in machines:
            machine_data = {
                'id': machine.id,
                'name': machine.name,
                'model': machine.model,
                'site_id': machine.site_id,
                'machine_number': machine.machine_number,
                'serial_number': machine.serial_number
            }
            backup_data['machines'].append(machine_data)
        
        # 3. Parts
        parts = Part.query.all()
        for part in parts:
            part_data = {
                'id': part.id,
                'name': part.name,
                'description': part.description,
                'machine_id': part.machine_id,
                'maintenance_frequency': part.maintenance_frequency,
                'maintenance_unit': part.maintenance_unit,
                'last_maintenance': part.last_maintenance.isoformat(),
                'next_maintenance': part.next_maintenance.isoformat(),
                'notification_sent': part.notification_sent,
                'last_maintained_by': part.last_maintained_by,
                'invoice_number': part.invoice_number
            }
            backup_data['parts'].append(part_data)
        
        # 4. Maintenance Logs
        try:
            maintenance_logs = MaintenanceLog.query.all()
            for log in maintenance_logs:
                log_data = {
                    'id': log.id,
                    'machine_id': log.machine_id,
                    'part_id': log.part_id,
                    'performed_by': log.performed_by,
                    'invoice_number': log.invoice_number,
                    'maintenance_date': log.maintenance_date.isoformat(),
                    'notes': log.notes
                }
                backup_data['maintenance_logs'].append(log_data)
        except Exception as e:
            # If maintenance log table doesn't exist yet, just continue
            current_app.logger.warning(f"Could not backup maintenance logs: {str(e)}")
        
        # 5. Users and Roles (if requested)
        if include_users:
            users = User.query.all()
            for user in users:
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'password_hash': user.password_hash,
                    'is_admin': user.is_admin,
                    'role_id': user.role_id,
                    'email': user.email,
                    'full_name': user.full_name
                }
                backup_data['users'].append(user_data)
            
            roles = Role.query.all()
            for role in roles:
                role_data = {
                    'id': role.id,
                    'name': role.name,
                    'description': role.description,
                    'permissions': role.permissions
                }
                backup_data['roles'].append(role_data)
            
            # Get user-site assignments
            user_site_assignments = db.session.query(user_site).all()
            for user_id, site_id in user_site_assignments:
                assignment = {
                    'user_id': user_id,
                    'site_id': site_id
                }
                backup_data['user_site_assignments'].append(assignment)
        
        # Save to file
        with open(backup_path, 'w') as f:
            json.dump(backup_data, f, indent=2, default=serialize_datetime)
        
        print(f"Backup created: {backup_path}")
        return backup_path

def restore_database(backup_path, restore_users=True):
    """
    Restore database from a backup file.
    
    Args:
        backup_path (str): Path to the backup file
        restore_users (bool): Whether to restore user and role data
    
    Returns:
        dict: Statistics about the restoration
    """
    # Import here to avoid circular imports
    from app import app, db, Site, Machine, Part, MaintenanceLog, User, Role
    
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup file not found: {backup_path}")
    
    # Load backup data
    with open(backup_path, 'r') as f:
        backup_data = json.load(f)
    
    stats = {
        'sites_created': 0,
        'sites_updated': 0,
        'machines_created': 0,
        'machines_updated': 0,
        'parts_created': 0,
        'parts_updated': 0,
        'logs_restored': 0,
        'users_restored': 0,
        'roles_restored': 0,
        'assignments_restored': 0,
        'errors': []
    }
    
    with app.app_context():
        # First backup the current database as a precaution
        current_time = time.strftime("%Y%m%d_%H%M%S")
        auto_backup_path = backup_database(include_users=True, backup_name=f"pre_restore_{current_time}")
        
        try:
            # 1. Restore Sites
            for site_data in backup_data.get('sites', []):
                # Check if site exists
                site = Site.query.filter_by(name=site_data['name']).first()
                
                if site:
                    # Update existing site
                    site.location = site_data.get('location', site.location)
                    site.enable_notifications = site_data.get('enable_notifications', site.enable_notifications)
                    site.contact_email = site_data.get('contact_email', site.contact_email)
                    site.notification_threshold = site_data.get('notification_threshold', site.notification_threshold)
                    stats['sites_updated'] += 1
                else:
                    # Create new site
                    new_site = Site(
                        name=site_data['name'],
                        location=site_data.get('location', ''),
                        enable_notifications=site_data.get('enable_notifications', False),
                        contact_email=site_data.get('contact_email', ''),
                        notification_threshold=site_data.get('notification_threshold', 30)
                    )
                    db.session.add(new_site)
                    stats['sites_created'] += 1
            
            db.session.commit()  # Commit sites to get their IDs
            
            # Create mapping from backup site IDs to current site IDs
            backup_to_current_site_id = {}
            for site_data in backup_data.get('sites', []):
                site = Site.query.filter_by(name=site_data['name']).first()
                if site:
                    backup_to_current_site_id[site_data['id']] = site.id
            
            # 2. Restore Machines
            for machine_data in backup_data.get('machines', []):
                # Map the site ID
                current_site_id = backup_to_current_site_id.get(machine_data['site_id'])
                if not current_site_id:
                    stats['errors'].append(f"Could not find site for machine: {machine_data['name']}")
                    continue
                
                # Check if machine exists at this site
                machine = Machine.query.filter_by(
                    name=machine_data['name'],
                    site_id=current_site_id
                ).first()
                
                if machine:
                    # Update existing machine
                    machine.model = machine_data.get('model', machine.model)
                    machine.machine_number = machine_data.get('machine_number', machine.machine_number)
                    machine.serial_number = machine_data.get('serial_number', machine.serial_number)
                    stats['machines_updated'] += 1
                else:
                    # Create new machine
                    new_machine = Machine(
                        name=machine_data['name'],
                        model=machine_data.get('model', ''),
                        site_id=current_site_id,
                        machine_number=machine_data.get('machine_number', ''),
                        serial_number=machine_data.get('serial_number', '')
                    )
                    db.session.add(new_machine)
                    stats['machines_created'] += 1
            
            db.session.commit()  # Commit machines to get their IDs
            
            # Create mapping from backup machine IDs to current machine IDs
            backup_to_current_machine_id = {}
            for machine_data in backup_data.get('machines', []):
                current_site_id = backup_to_current_site_id.get(machine_data['site_id'])
                if current_site_id:
                    machine = Machine.query.filter_by(
                        name=machine_data['name'],
                        site_id=current_site_id
                    ).first()
                    if machine:
                        backup_to_current_machine_id[machine_data['id']] = machine.id
            
            # 3. Restore Parts
            for part_data in backup_data.get('parts', []):
                # Map the machine ID
                current_machine_id = backup_to_current_machine_id.get(part_data['machine_id'])
                if not current_machine_id:
                    stats['errors'].append(f"Could not find machine for part: {part_data['name']}")
                    continue
                
                # Check if part exists for this machine
                part = Part.query.filter_by(
                    name=part_data['name'],
                    machine_id=current_machine_id
                ).first()
                
                # Parse dates
                last_maintenance = datetime.fromisoformat(part_data['last_maintenance'])
                next_maintenance = datetime.fromisoformat(part_data['next_maintenance'])
                
                if part:
                    # Update existing part
                    part.description = part_data.get('description', part.description)
                    part.maintenance_frequency = part_data.get('maintenance_frequency', part.maintenance_frequency)
                    part.maintenance_unit = part_data.get('maintenance_unit', part.maintenance_unit)
                    part.last_maintenance = last_maintenance
                    part.next_maintenance = next_maintenance
                    part.notification_sent = part_data.get('notification_sent', part.notification_sent)
                    part.last_maintained_by = part_data.get('last_maintained_by', part.last_maintained_by)
                    part.invoice_number = part_data.get('invoice_number', part.invoice_number)
                    stats['parts_updated'] += 1
                else:
                    # Create new part
                    new_part = Part(
                        name=part_data['name'],
                        description=part_data.get('description', ''),
                        machine_id=current_machine_id,
                        maintenance_frequency=part_data.get('maintenance_frequency', 7),
                        maintenance_unit=part_data.get('maintenance_unit', 'day'),
                        last_maintenance=last_maintenance,
                        next_maintenance=next_maintenance,
                        notification_sent=part_data.get('notification_sent', False),
                        last_maintained_by=part_data.get('last_maintained_by', ''),
                        invoice_number=part_data.get('invoice_number', '')
                    )
                    db.session.add(new_part)
                    stats['parts_created'] += 1
            
            db.session.commit()  # Commit parts to get their IDs
            
            # Create mapping from backup part IDs to current part IDs
            backup_to_current_part_id = {}
            for part_data in backup_data.get('parts', []):
                current_machine_id = backup_to_current_machine_id.get(part_data['machine_id'])
                if current_machine_id:
                    part = Part.query.filter_by(
                        name=part_data['name'],
                        machine_id=current_machine_id
                    ).first()
                    if part:
                        backup_to_current_part_id[part_data['id']] = part.id
            
            # 4. Restore Maintenance Logs
            try:
                for log_data in backup_data.get('maintenance_logs', []):
                    # Map the machine and part IDs
                    current_machine_id = backup_to_current_machine_id.get(log_data['machine_id'])
                    current_part_id = backup_to_current_part_id.get(log_data['part_id'])
                    
                    if not current_machine_id or not current_part_id:
                        stats['errors'].append(f"Could not map machine or part for maintenance log")
                        continue
                    
                    # Parse date
                    maintenance_date = datetime.fromisoformat(log_data['maintenance_date'])
                    
                    # Check if a log with the same data already exists
                    existing_log = MaintenanceLog.query.filter_by(
                        machine_id=current_machine_id,
                        part_id=current_part_id,
                        maintenance_date=maintenance_date
                    ).first()
                    
                    if not existing_log:
                        # Create new log entry
                        new_log = MaintenanceLog(
                            machine_id=current_machine_id,
                            part_id=current_part_id,
                            performed_by=log_data.get('performed_by', 'Unknown'),
                            invoice_number=log_data.get('invoice_number', ''),
                            maintenance_date=maintenance_date,
                            notes=log_data.get('notes', '')
                        )
                        db.session.add(new_log)
                        stats['logs_restored'] += 1
            except Exception as e:
                stats['errors'].append(f"Error restoring maintenance logs: {str(e)}")
            
            # 5. Restore Users and Roles (if included and requested)
            if restore_users and 'users' in backup_data and 'roles' in backup_data:
                # First restore roles
                for role_data in backup_data.get('roles', []):
                    role = Role.query.filter_by(name=role_data['name']).first()
                    if not role:
                        # Create new role
                        new_role = Role(
                            name=role_data['name'],
                            description=role_data.get('description', ''),
                            permissions=role_data.get('permissions', '')
                        )
                        db.session.add(new_role)
                        stats['roles_restored'] += 1
                
                db.session.commit()  # Commit roles to get their IDs
                
                # Create mapping from backup role IDs to current role IDs
                backup_to_current_role_id = {}
                for role_data in backup_data.get('roles', []):
                    role = Role.query.filter_by(name=role_data['name']).first()
                    if role:
                        backup_to_current_role_id[role_data['id']] = role.id
                
                # Now restore users
                for user_data in backup_data.get('users', []):
                    user = User.query.filter_by(username=user_data['username']).first()
                    
                    # Map the role ID
                    current_role_id = backup_to_current_role_id.get(user_data.get('role_id'))
                    
                    if not user:
                        # Create new user
                        new_user = User(
                            username=user_data['username'],
                            password_hash=user_data['password_hash'],  # We're directly copying the hash
                            is_admin=user_data.get('is_admin', False),
                            role_id=current_role_id,
                            email=user_data.get('email', ''),
                            full_name=user_data.get('full_name', '')
                        )
                        db.session.add(new_user)
                        stats['users_restored'] += 1
                
                db.session.commit()  # Commit users to get their IDs
                
                # Create mapping from backup user IDs to current user IDs
                backup_to_current_user_id = {}
                for user_data in backup_data.get('users', []):
                    user = User.query.filter_by(username=user_data['username']).first()
                    if user:
                        backup_to_current_user_id[user_data['id']] = user.id
                
                # Finally restore user-site assignments
                for assignment in backup_data.get('user_site_assignments', []):
                    current_user_id = backup_to_current_user_id.get(assignment['user_id'])
                    current_site_id = backup_to_current_site_id.get(assignment['site_id'])
                    
                    if current_user_id and current_site_id:
                        # Check if assignment already exists
                        user = User.query.get(current_user_id)
                        site = Site.query.get(current_site_id)
                        
                        if user and site and site not in user.sites:
                            user.sites.append(site)
                            stats['assignments_restored'] += 1
            
            # Final commit
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            stats['errors'].append(f"Error during restore: {str(e)}")
            print(f"Error during restore: {str(e)}")
            print(f"A backup of the database before restore was created at: {auto_backup_path}")
        
        return stats

def list_backups():
    """
    List all available backups.
    
    Returns:
        list: List of dictionaries with backup info
    """
    ensure_backup_dir()
    
    backups = []
    for filename in os.listdir(BACKUP_DIR):
        if filename.endswith('.json'):
            file_path = os.path.join(BACKUP_DIR, filename)
            file_stat = os.stat(file_path)
            
            # Try to read metadata from the backup file
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    metadata = data.get('metadata', {})
            except:
                metadata = {}
                data = {'sites': [], 'machines': [], 'parts': []}
            
            backup_info = {
                'filename': filename,
                'path': file_path,
                'size': file_stat.st_size,
                'created': datetime.fromtimestamp(file_stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                'includes_users': metadata.get('include_users', False),
                'timestamp': metadata.get('timestamp', ''),
                'version': metadata.get('version', 'unknown'),
                'sites_count': len(data.get('sites', [])),
                'machines_count': len(data.get('machines', [])),
                'parts_count': len(data.get('parts', []))
            }
            backups.append(backup_info)
    
    # Sort by creation time (newest first)
    backups.sort(key=lambda x: x['created'], reverse=True)
    return backups

def delete_backup(filename):
    """Delete a backup file."""
    file_path = os.path.join(BACKUP_DIR, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False
