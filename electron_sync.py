"""
Database Synchronization for Electron App

This module handles synchronization between local SQLite database (offline mode)
and the PostgreSQL database (online mode) when internet connectivity is restored.
"""

import os
import sys
import logging
import time
import json
import uuid
from datetime import datetime, timedelta
import threading
import queue
import traceback
import requests
from sqlalchemy import create_engine, text, inspect, or_
from sqlalchemy.orm import sessionmaker
from flask import Flask
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import from our own modules
from models import db, User, Role, Site, Machine, Part, MaintenanceRecord, AuditTask, AuditTaskCompletion

# Global vars
sync_queue = queue.Queue()
sync_thread = None
sync_running = False
app = None  # Flask app instance
sqlite_engine = None  # SQLite connection
pg_engine = None  # PostgreSQL connection
last_sync_time = None
sync_error = None

def init_sync(flask_app):
    """Initialize the synchronization module with the Flask app"""
    global app, sync_running, sync_thread
    app = flask_app
    
    # Start sync thread if not already running
    if not sync_running and not sync_thread:
        sync_thread = threading.Thread(target=sync_worker, daemon=True)
        sync_running = True
        sync_thread.start()
        logger.info("Database sync thread started")
    
    return True

def get_sync_status():
    """Get the current synchronization status"""
    global last_sync_time, sync_error
    
    return {
        'running': sync_running,
        'last_sync': last_sync_time,
        'error': sync_error,
        'queue_size': sync_queue.qsize()
    }

def queue_sync_task(task_type, data=None):
    """Add a synchronization task to the queue"""
    sync_queue.put({
        'type': task_type,
        'data': data,
        'timestamp': datetime.utcnow().isoformat()
    })
    logger.info(f"Queued sync task: {task_type}")

def sync_worker():
    """Worker thread for processing synchronization tasks"""
    global sync_running, last_sync_time, sync_error
    
    logger.info("Sync worker thread started")
    
    while sync_running:
        try:
            # Wait for a sync task (with timeout to allow thread to exit)
            try:
                task = sync_queue.get(timeout=5)
            except queue.Empty:
                continue
                
            # Process the task
            if task['type'] == 'full_sync':
                error = perform_full_sync()
                if error:
                    sync_error = error
                else:
                    last_sync_time = datetime.utcnow()
                    sync_error = None
            
            elif task['type'] == 'push_changes':
                error = push_local_changes(task['data'])
                if error:
                    sync_error = error
                else:
                    sync_error = None
            
            # Mark task as done
            sync_queue.task_done()
            
        except Exception as e:
            sync_error = f"Sync error: {str(e)}"
            logger.error(f"Error in sync worker: {e}")
            logger.error(traceback.format_exc())
            time.sleep(5)  # Wait before retrying after error
    
    logger.info("Sync worker thread stopped")

def check_connectivity():
    """Check if we can connect to the PostgreSQL database"""
    # Get PostgreSQL URI from environment
    pg_uri = os.environ.get('DATABASE_URL')
    if not pg_uri:
        return False, "No PostgreSQL URI configured"
    
    try:
        # Create a temporary engine for the test
        engine = create_engine(pg_uri, pool_pre_ping=True)
        
        # Try to connect
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            conn.close()
        
        # If we get here, connection succeeded
        return True, None
    except Exception as e:
        return False, str(e)

def get_sqlite_engine():
    """Get or create SQLite engine"""
    global sqlite_engine
    
    if sqlite_engine is None:
        # Import configuration function
        from electron_config import get_database_uri
        
        # Get SQLite URI
        sqlite_uri = get_database_uri()
        
        # Create engine
        sqlite_engine = create_engine(
            sqlite_uri,
            connect_args={'timeout': 30},
            pool_pre_ping=True
        )
    
    return sqlite_engine

def get_pg_engine():
    """Get or create PostgreSQL engine"""
    global pg_engine
    
    if pg_engine is None:
        # Get PostgreSQL URI from environment
        pg_uri = os.environ.get('DATABASE_URL')
        
        if not pg_uri:
            raise ValueError("PostgreSQL URI not configured")
        
        # Create engine
        pg_engine = create_engine(
            pg_uri,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True
        )
    
    return pg_engine

def perform_full_sync():
    """Perform a full synchronization between SQLite and PostgreSQL"""
    try:
        # Check if we have connectivity
        connected, error = check_connectivity()
        if not connected:
            return f"Cannot connect to PostgreSQL database: {error}"
        
        # Get engines
        sqlite_engine = get_sqlite_engine()
        pg_engine = get_pg_engine()
        
        # Create sessions
        SQLiteSession = sessionmaker(bind=sqlite_engine)
        PGSession = sessionmaker(bind=pg_engine)
        
        sqlite_session = SQLiteSession()
        pg_session = PGSession()
        
        try:
            # Sync from PostgreSQL to SQLite (pull changes)
            # 1. Users and Roles (basic data only)
            sync_reference_data(pg_session, sqlite_session)
            
            # 2. Sites, Machines, Parts (configuration data)
            sync_configuration_data(pg_session, sqlite_session)
            
            # Sync from SQLite to PostgreSQL (push local changes)
            # 3. Maintenance Records
            sync_maintenance_records(sqlite_session, pg_session)
            
            # 4. Audit Task Completions
            sync_audit_task_completions(sqlite_session, pg_session)
            
            # Commit changes
            sqlite_session.commit()
            pg_session.commit()
            
            logger.info("Full synchronization completed successfully")
            return None
            
        except Exception as e:
            sqlite_session.rollback()
            pg_session.rollback()
            logger.error(f"Error during full sync: {e}")
            logger.error(traceback.format_exc())
            return f"Sync error: {str(e)}"
            
        finally:
            sqlite_session.close()
            pg_session.close()
            
    except Exception as e:
        logger.error(f"Error setting up sync: {e}")
        logger.error(traceback.format_exc())
        return f"Sync setup error: {str(e)}"

def sync_reference_data(source_session, target_session):
    """Sync reference data (users, roles) from source to target"""
    # Sync roles first (they're referenced by users)
    source_roles = source_session.query(Role).all()
    
    for role in source_roles:
        # Check if role exists in target
        target_role = target_session.query(Role).filter_by(name=role.name).first()
        
        if target_role:
            # Update existing role
            target_role.description = role.description
            target_role.permissions = role.permissions
        else:
            # Create new role
            new_role = Role(
                name=role.name,
                description=role.description,
                permissions=role.permissions
            )
            target_session.add(new_role)
    
    # Commit to get role IDs
    target_session.commit()
    
    # Now sync users (basic data only, no passwords)
    source_users = source_session.query(User).all()
    
    for user in source_users:
        # Check if user exists in target by username hash
        target_user = target_session.query(User).filter_by(username_hash=user.username_hash).first()
        
        if not target_user:
            # Create basic user record
            role = target_session.query(Role).filter_by(name=user.role.name).first() if user.role else None
            
            new_user = User()
            new_user.username = user.username  # This will encrypt and hash
            new_user.email = user.email  # This will encrypt and hash
            new_user.full_name = user.full_name
            # Don't copy password hash
            new_user.is_admin = user.is_admin
            new_user.role = role
            
            target_session.add(new_user)
    
    # Commit user changes
    target_session.commit()

def sync_configuration_data(source_session, target_session):
    """Sync configuration data (sites, machines, parts) from source to target"""
    # Sync sites
    source_sites = source_session.query(Site).all()
    
    for site in source_sites:
        # Check if site exists in target
        target_site = target_session.query(Site).filter_by(name=site.name).first()
        
        if target_site:
            # Update existing site
            target_site.location = site.location
            target_site.contact_email = site.contact_email
            target_site.enable_notifications = site.enable_notifications
            target_site.notification_threshold = site.notification_threshold
        else:
            # Create new site
            new_site = Site(
                name=site.name,
                location=site.location,
                contact_email=site.contact_email,
                enable_notifications=site.enable_notifications,
                notification_threshold=site.notification_threshold
            )
            target_session.add(new_site)
            target_session.flush()  # Get ID for new site
            target_site = new_site
        
        # Now sync machines for this site
        for machine in site.machines:
            target_machine = target_session.query(Machine).filter_by(
                site_id=target_site.id,
                machine_number=machine.machine_number
            ).first()
            
            if target_machine:
                # Update existing machine
                target_machine.name = machine.name
                target_machine.model = machine.model
                target_machine.serial_number = machine.serial_number
            else:
                # Create new machine
                new_machine = Machine(
                    name=machine.name,
                    model=machine.model,
                    machine_number=machine.machine_number,
                    serial_number=machine.serial_number,
                    site=target_site
                )
                target_session.add(new_machine)
                target_session.flush()  # Get ID for new machine
                target_machine = new_machine
            
            # Now sync parts for this machine
            for part in machine.parts:
                target_part = target_session.query(Part).filter_by(
                    machine_id=target_machine.id,
                    name=part.name
                ).first()
                
                if target_part:
                    # Update existing part
                    target_part.description = part.description
                    target_part.maintenance_frequency = part.maintenance_frequency
                    target_part.maintenance_unit = part.maintenance_unit
                    target_part.maintenance_days = part.maintenance_days
                    target_part.last_maintenance = part.last_maintenance
                    target_part.next_maintenance = part.next_maintenance
                else:
                    # Create new part
                    new_part = Part(
                        name=part.name,
                        description=part.description,
                        maintenance_frequency=part.maintenance_frequency,
                        maintenance_unit=part.maintenance_unit,
                        maintenance_days=part.maintenance_days,
                        last_maintenance=part.last_maintenance,
                        next_maintenance=part.next_maintenance,
                        machine=target_machine
                    )
                    target_session.add(new_part)
    
    # Commit all changes
    target_session.commit()

def sync_maintenance_records(source_session, target_session):
    """Sync maintenance records from source to target (newer ones only)"""
    # Get all records from source that don't exist in target
    source_records = source_session.query(MaintenanceRecord).all()
    
    for record in source_records:
        # Check if record exists in target by client_id
        target_record = target_session.query(MaintenanceRecord).filter_by(client_id=record.client_id).first()
        
        if not target_record:
            # Find corresponding objects in target
            target_part = find_corresponding_part(record.part, target_session)
            target_user = find_corresponding_user(record.user, target_session)
            target_machine = find_corresponding_machine(record.machine, target_session)
            
            if target_part and target_user:
                # Create new record in target
                new_record = MaintenanceRecord(
                    part=target_part,
                    user=target_user,
                    machine=target_machine,
                    date=record.date,
                    comments=record.comments,
                    maintenance_type=record.maintenance_type,
                    description=record.description,
                    performed_by=record.performed_by,
                    status=record.status,
                    notes=record.notes,
                    client_id=record.client_id  # Preserve client ID for future sync
                )
                target_session.add(new_record)
    
    # Commit changes
    target_session.commit()

def sync_audit_task_completions(source_session, target_session):
    """Sync audit task completions from source to target (newer ones only)"""
    # Get all completions from source
    source_completions = source_session.query(AuditTaskCompletion).all()
    
    for completion in source_completions:
        # Check if already exists in target based on task, machine and date
        target_completion = target_session.query(AuditTaskCompletion).filter_by(
            audit_task_id=completion.audit_task_id,
            machine_id=completion.machine_id,
            date=completion.date
        ).first()
        
        if target_completion:
            # Update existing completion
            target_completion.completed = completion.completed
            target_completion.completed_by = completion.completed_by
            target_completion.completed_at = completion.completed_at
        else:
            # Find corresponding objects in target
            target_task = find_corresponding_audit_task(completion.audit_task, target_session)
            target_machine = find_corresponding_machine(completion.machine, target_session)
            target_user = target_session.query(User).get(completion.completed_by) if completion.completed_by else None
            
            if target_task and target_machine:
                # Create new completion
                new_completion = AuditTaskCompletion(
                    audit_task=target_task,
                    machine=target_machine,
                    date=completion.date,
                    completed=completion.completed,
                    completed_by=target_user.id if target_user else None,
                    completed_at=completion.completed_at
                )
                target_session.add(new_completion)
    
    # Commit changes
    target_session.commit()

def push_local_changes(record_type=None):
    """Push local changes to PostgreSQL (specific type or all)"""
    try:
        # Check if we have connectivity
        connected, error = check_connectivity()
        if not connected:
            return f"Cannot connect to PostgreSQL database: {error}"
        
        # Get engines
        sqlite_engine = get_sqlite_engine()
        pg_engine = get_pg_engine()
        
        # Create sessions
        SQLiteSession = sessionmaker(bind=sqlite_engine)
        PGSession = sessionmaker(bind=pg_engine)
        
        sqlite_session = SQLiteSession()
        pg_session = PGSession()
        
        try:
            if record_type is None or record_type == 'maintenance':
                sync_maintenance_records(sqlite_session, pg_session)
                
            if record_type is None or record_type == 'audit':
                sync_audit_task_completions(sqlite_session, pg_session)
            
            # Commit changes
            pg_session.commit()
            
            logger.info(f"Successfully pushed local changes to PostgreSQL: {record_type or 'all'}")
            return None
            
        except Exception as e:
            pg_session.rollback()
            logger.error(f"Error pushing changes: {e}")
            logger.error(traceback.format_exc())
            return f"Error pushing changes: {str(e)}"
            
        finally:
            sqlite_session.close()
            pg_session.close()
            
    except Exception as e:
        logger.error(f"Error setting up push: {e}")
        logger.error(traceback.format_exc())
        return f"Push setup error: {str(e)}"

# Helper functions to find corresponding objects between databases

def find_corresponding_part(source_part, target_session):
    """Find corresponding part in target database"""
    # Try to find by machine number and part name
    machine = source_part.machine
    if not machine:
        return None
        
    target_machine = target_session.query(Machine).filter_by(machine_number=machine.machine_number).first()
    if not target_machine:
        return None
        
    return target_session.query(Part).filter_by(
        machine_id=target_machine.id,
        name=source_part.name
    ).first()

def find_corresponding_user(source_user, target_session):
    """Find corresponding user in target database"""
    return target_session.query(User).filter_by(
        username_hash=source_user.username_hash
    ).first()

def find_corresponding_machine(source_machine, target_session):
    """Find corresponding machine in target database"""
    if not source_machine:
        return None
        
    return target_session.query(Machine).filter_by(
        machine_number=source_machine.machine_number
    ).first()

def find_corresponding_audit_task(source_task, target_session):
    """Find corresponding audit task in target database"""
    # Try to find by name and site
    site = source_task.site
    if not site:
        return None
        
    target_site = target_session.query(Site).filter_by(name=site.name).first()
    if not target_site:
        return None
        
    return target_session.query(AuditTask).filter_by(
        site_id=target_site.id,
        name=source_task.name
    ).first()

# API for Electron app to check sync status
def get_sync_info():
    """Get synchronization information for the UI"""
    status = get_sync_status()
    
    # Check current connectivity
    connected, error = check_connectivity()
    
    return {
        'online': connected,
        'last_sync': status['last_sync'].isoformat() if status['last_sync'] else None,
        'sync_error': status['error'],
        'pending_changes': status['queue_size'],
        'connection_error': error if not connected else None
    }

def trigger_sync():
    """Trigger a full synchronization"""
    queue_sync_task('full_sync')
    return True

# Initialize module when imported in app context
def init_sync_module(flask_app):
    """Initialize the sync module with a Flask app"""
    init_sync(flask_app)
    logger.info("Electron sync module initialized")

# If this module is run directly, test the sync functionality
if __name__ == '__main__':
    # Create a test Flask app
    test_app = Flask(__name__)
    
    # Configure database
    from electron_config import get_database_uri
    test_app.config['SQLALCHEMY_DATABASE_URI'] = get_database_uri()
    test_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(test_app)
    
    # Initialize sync
    with test_app.app_context():
        init_sync(test_app)
        trigger_sync()
    
    # Wait for completion
    time.sleep(10)
    print("Sync test complete")
