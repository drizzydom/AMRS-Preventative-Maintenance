"""
Module for implementing a hybrid database access layer that works with both
SQLAlchemy in online mode and SQLite in offline mode.
"""
import os
import logging
from functools import wraps
from flask import g, current_app

logger = logging.getLogger(__name__)

# Flag to indicate if we're in offline mode
OFFLINE_MODE = os.environ.get('OFFLINE_MODE', 'false').lower() == 'true'

class HybridDAO:
    """
    Hybrid Data Access Object that works with both SQLAlchemy and SQLite.
    This allows our app to use the same code for online and offline access.
    """
    
    @staticmethod
    def get_sites():
        """Get all sites"""
        if not OFFLINE_MODE:
            from models import Site
            return Site.query.all()
        else:
            db = current_app.offline_adapter.get_db()
            if not db:
                return []
            return db.execute('SELECT * FROM sites ORDER BY name').fetchall()
    
    @staticmethod
    def get_site(site_id):
        """Get a site by ID"""
        if not OFFLINE_MODE:
            from models import Site
            from app import db
            return db.session.get(Site, site_id)
        else:
            db = current_app.offline_adapter.get_db()
            if not db:
                return None
            return db.execute('SELECT * FROM sites WHERE id = ?', (site_id,)).fetchone()
    
    @staticmethod
    def get_machines(site_id=None):
        """Get machines, optionally filtered by site_id"""
        if not OFFLINE_MODE:
            from models import Machine
            if site_id:
                return Machine.query.filter_by(site_id=site_id).all()
            else:
                return Machine.query.all()
        else:
            db = current_app.offline_adapter.get_db()
            if not db:
                return []
            
            if site_id:
                return db.execute('''
                    SELECT m.*, s.name as site_name 
                    FROM machines m
                    JOIN sites s ON m.site_id = s.id
                    WHERE m.site_id = ?
                    ORDER BY m.name
                ''', (site_id,)).fetchall()
            else:
                return db.execute('''
                    SELECT m.*, s.name as site_name 
                    FROM machines m
                    JOIN sites s ON m.site_id = s.id
                    ORDER BY m.name
                ''').fetchall()
    
    @staticmethod
    def get_machine(machine_id):
        """Get a machine by ID"""
        if not OFFLINE_MODE:
            from models import Machine
            from app import db
            return db.session.get(Machine, machine_id)
        else:
            db = current_app.offline_adapter.get_db()
            if not db:
                return None
            return db.execute('''
                SELECT m.*, s.name as site_name 
                FROM machines m
                JOIN sites s ON m.site_id = s.id
                WHERE m.id = ?
            ''', (machine_id,)).fetchone()
    
    @staticmethod
    def get_parts(machine_id=None):
        """Get parts, optionally filtered by machine_id"""
        if not OFFLINE_MODE:
            from models import Part
            if machine_id:
                return Part.query.filter_by(machine_id=machine_id).all()
            else:
                return Part.query.all()
        else:
            db = current_app.offline_adapter.get_db()
            if not db:
                return []
            
            if machine_id:
                return db.execute('''
                    SELECT p.*, m.name as machine_name
                    FROM parts p
                    JOIN machines m ON p.machine_id = m.id
                    WHERE p.machine_id = ?
                    ORDER BY p.name
                ''', (machine_id,)).fetchall()
            else:
                return db.execute('''
                    SELECT p.*, m.name as machine_name, s.name as site_name
                    FROM parts p
                    JOIN machines m ON p.machine_id = m.id
                    JOIN sites s ON m.site_id = s.id
                    ORDER BY p.name
                ''').fetchall()
    
    @staticmethod
    def get_part(part_id):
        """Get a part by ID"""
        if not OFFLINE_MODE:
            from models import Part
            from app import db
            return db.session.get(Part, part_id)
        else:
            db = current_app.offline_adapter.get_db()
            if not db:
                return None
            return db.execute('''
                SELECT p.*, m.name as machine_name
                FROM parts p
                JOIN machines m ON p.machine_id = m.id
                WHERE p.id = ?
            ''', (part_id,)).fetchone()
    
    @staticmethod
    def get_maintenance_records(part_id=None, machine_id=None):
        """Get maintenance records, optionally filtered by part_id or machine_id"""
        if not OFFLINE_MODE:
            from models import MaintenanceRecord
            query = MaintenanceRecord.query
            
            if part_id:
                query = query.filter_by(part_id=part_id)
            elif machine_id:
                query = query.filter_by(machine_id=machine_id)
                
            return query.order_by(MaintenanceRecord.date.desc()).all()
        else:
            db = current_app.offline_adapter.get_db()
            if not db:
                return []
            
            if part_id:
                return db.execute('''
                    SELECT mr.*, u.username as user_name, p.name as part_name
                    FROM maintenance_records mr
                    LEFT JOIN users u ON mr.user_id = u.id
                    LEFT JOIN parts p ON mr.part_id = p.id
                    WHERE mr.part_id = ?
                    ORDER BY mr.maintenance_date DESC
                ''', (part_id,)).fetchall()
            elif machine_id:
                return db.execute('''
                    SELECT mr.*, u.username as user_name, p.name as part_name
                    FROM maintenance_records mr
                    LEFT JOIN users u ON mr.user_id = u.id
                    LEFT JOIN parts p ON mr.part_id = p.id
                    WHERE mr.machine_id = ?
                    ORDER BY mr.maintenance_date DESC
                ''', (machine_id,)).fetchall()
            else:
                return db.execute('''
                    SELECT mr.*, u.username as user_name, 
                        m.name as machine_name, p.name as part_name,
                        s.name as site_name
                    FROM maintenance_records mr
                    LEFT JOIN users u ON mr.user_id = u.id
                    LEFT JOIN machines m ON mr.machine_id = m.id
                    LEFT JOIN parts p ON mr.part_id = p.id
                    LEFT JOIN sites s ON m.site_id = s.id
                    ORDER BY mr.maintenance_date DESC
                ''').fetchall()
    
    @staticmethod
    def create_maintenance_record(machine_id, part_id, user_id, notes):
        """Create a new maintenance record"""
        if not OFFLINE_MODE:
            from models import MaintenanceRecord
            from app import db
            from datetime import datetime
            
            record = MaintenanceRecord(
                machine_id=machine_id, 
                part_id=part_id,
                user_id=user_id,
                date=datetime.now(),
                notes=notes
            )
            db.session.add(record)
            db.session.commit()
            return record
        else:
            db = current_app.offline_adapter.get_db()
            if not db:
                return None
            
            cursor = db.execute('''
                INSERT INTO maintenance_records 
                (machine_id, part_id, user_id, maintenance_date, notes, sync_status)
                VALUES (?, ?, ?, datetime('now'), ?, 'pending')
            ''', (machine_id, part_id, user_id, notes))
            
            # Add to sync log
            db.execute('''
                INSERT INTO sync_log 
                (table_name, record_id, sync_action, sync_status, sync_timestamp)
                VALUES (?, ?, 'create', 'pending', datetime('now'))
            ''', ('maintenance_records', cursor.lastrowid))
            
            db.commit()
            
            # Get the created record
            return db.execute('''
                SELECT * FROM maintenance_records WHERE id = ?
            ''', (cursor.lastrowid,)).fetchone()

# Add more methods as needed for your specific app functionality
