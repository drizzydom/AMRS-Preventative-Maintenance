import sqlite3
import os
import json
from datetime import datetime, timedelta
import uuid
import logging
from pathlib import Path
from .security_utils import SecurityUtils

class OfflineDatabase:
    def __init__(self, db_path, encrypt=True):
        self.db_path = db_path
        self.encrypt = encrypt
        self.logger = logging.getLogger("OfflineDatabase")
        
        # Initialize security utils if encryption is enabled
        if self.encrypt:
            app_data_dir = os.path.dirname(self.db_path)
            self.security = SecurityUtils(app_data_dir)
            self.logger.info("Database encryption enabled")
        else:
            self.security = None
            self.logger.info("Database encryption disabled")
            
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.initialize_db()
        
    def _get_connection(self):
        """Get a database connection"""
        return sqlite3.connect(self.db_path)

    def initialize_db(self):
        """Initialize the database schema"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Table for storing operations to sync
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_operations (
                id TEXT PRIMARY KEY,
                endpoint TEXT NOT NULL,
                method TEXT NOT NULL,
                data TEXT,
                data_hash TEXT,
                timestamp TEXT,
                synced INTEGER DEFAULT 0,
                sync_attempts INTEGER DEFAULT 0,
                last_sync_attempt TEXT,
                failure_data TEXT,
                version INTEGER DEFAULT 1
            )
            ''')
            
            # Table for caching GET responses
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS cached_data (
                endpoint TEXT PRIMARY KEY,
                data TEXT,
                data_hash TEXT,
                timestamp TEXT,
                expires_at TEXT
            )
            ''')
            
            # Table for maintaining machine state
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS machines (
                id TEXT PRIMARY KEY,
                data TEXT,
                data_hash TEXT,
                last_updated TEXT,
                version INTEGER DEFAULT 1
            )
            ''')
            
            # Table for maintenance history
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS maintenance_history (
                id TEXT PRIMARY KEY,
                machine_id TEXT,
                part_id TEXT,
                timestamp TEXT,
                data TEXT,
                data_hash TEXT,
                synced INTEGER DEFAULT 0,
                sync_attempts INTEGER DEFAULT 0,
                last_sync_attempt TEXT,
                failure_data TEXT,
                version INTEGER DEFAULT 1,
                FOREIGN KEY (machine_id) REFERENCES machines (id)
            )
            ''')
            
            # New table for auth tokens
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS auth_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT,
                refresh_token TEXT,
                expires_at TEXT,
                user_id TEXT,
                last_used TEXT
            )
            ''')
            
            # New table for user-specific data access control
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_access (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                role TEXT,
                permissions TEXT,
                allowed_sites TEXT
            )
            ''')
            
            # Create maintenance_schedule table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS maintenance_schedule (
                id TEXT PRIMARY KEY,
                part_id TEXT NOT NULL,
                interval_days INTEGER NOT NULL,
                next_due TEXT NOT NULL,
                advance_notice_hours INTEGER DEFAULT 24,
                created_at TEXT NOT NULL,
                schedule_type TEXT DEFAULT 'interval',
                schedule_data TEXT,
                FOREIGN KEY (part_id) REFERENCES cached_data (id)
            )
            ''')
            
            # Create notification_history table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS notification_history (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                category TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                read INTEGER DEFAULT 0,
                data_json TEXT
            )
            ''')
            
            # Create necessary indices
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_maintenance_schedule_part_id ON maintenance_schedule (part_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_maintenance_schedule_next_due ON maintenance_schedule (next_due)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_notification_history_category ON notification_history (category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_notification_history_timestamp ON notification_history (timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_notification_history_read ON notification_history (read)')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}", exc_info=True)
            raise

    def store_maintenance_schedule(self, schedule):
        """
        Store a maintenance schedule
        
        Args:
            schedule: Dictionary with schedule data
            
        Returns:
            Schedule ID if successful, None otherwise
        """
        try:
            # Generate ID if not provided
            schedule_id = schedule.get('id', self._generate_id())
            
            # Get required fields
            part_id = schedule.get('part_id')
            interval_days = schedule.get('interval_days')
            next_due = schedule.get('next_due')
            
            if not all([part_id, interval_days, next_due]):
                self.logger.error("Missing required fields for maintenance schedule")
                return None
                
            # Extract other fields with defaults
            advance_notice_hours = schedule.get('advance_notice_hours', 24)
            created_at = schedule.get('created_at', datetime.now().isoformat())
            schedule_type = schedule.get('schedule_type', 'interval')
            schedule_data = schedule.get('schedule_data', '{}')
            
            # Ensure schedule_data is a string
            if not isinstance(schedule_data, str):
                schedule_data = json.dumps(schedule_data)
                
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Insert or replace schedule
            cursor.execute(
                '''
                INSERT OR REPLACE INTO maintenance_schedule 
                (id, part_id, interval_days, next_due, advance_notice_hours, created_at, schedule_type, schedule_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (schedule_id, part_id, interval_days, next_due, advance_notice_hours, created_at, schedule_type, schedule_data)
            )
            
            conn.commit()
            conn.close()
            
            return schedule_id
            
        except Exception as e:
            self.logger.error(f"Error storing maintenance schedule: {e}")
            return None

    def update_maintenance_schedule(self, schedule_id, updates):
        """
        Update a maintenance schedule
        
        Args:
            schedule_id: ID of schedule to update
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if schedule exists
            schedule = self.get_maintenance_schedule(schedule_id)
            if not schedule:
                self.logger.error(f"Schedule {schedule_id} not found")
                return False
                
            # Build SQL update parts
            set_parts = []
            params = []
            
            for field, value in updates.items():
                if field in ['id', 'part_id', 'created_at']:
                    # Don't update these fields
                    continue
                    
                set_parts.append(f"{field} = ?")
                params.append(value)
                
            if not set_parts:
                return True  # No updates needed
                
            # Complete the parameter list with the ID
            params.append(schedule_id)
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Execute update
            cursor.execute(
                f"UPDATE maintenance_schedule SET {', '.join(set_parts)} WHERE id = ?",
                params
            )
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating maintenance schedule: {e}")
            return False

    def delete_maintenance_schedule(self, schedule_id):
        """
        Delete a maintenance schedule
        
        Args:
            schedule_id: ID of schedule to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Delete the schedule
            cursor.execute(
                "DELETE FROM maintenance_schedule WHERE id = ?",
                (schedule_id,)
            )
            
            deleted = cursor.rowcount > 0
            
            conn.commit()
            conn.close()
            
            return deleted
            
        except Exception as e:
            self.logger.error(f"Error deleting maintenance schedule: {e}")
            return False

    def get_maintenance_schedule(self, schedule_id):
        """
        Get a specific maintenance schedule
        
        Args:
            schedule_id: ID of schedule to retrieve
            
        Returns:
            Schedule dictionary or None if not found
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                '''
                SELECT id, part_id, interval_days, next_due, advance_notice_hours, 
                       created_at, schedule_type, schedule_data
                FROM maintenance_schedule
                WHERE id = ?
                ''',
                (schedule_id,)
            )
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
                
            # Parse schedule data
            schedule_data = {}
            try:
                if row[7]:  # schedule_data
                    schedule_data = json.loads(row[7])
            except json.JSONDecodeError:
                pass
                
            # Build schedule dictionary
            return {
                'id': row[0],
                'part_id': row[1],
                'interval_days': row[2],
                'next_due': row[3],
                'advance_notice_hours': row[4],
                'created_at': row[5],
                'schedule_type': row[6],
                'schedule_data': schedule_data
            }
            
        except Exception as e:
            self.logger.error(f"Error getting maintenance schedule: {e}")
            return None

    def get_part_maintenance_schedule(self, part_id):
        """
        Get maintenance schedule for a specific part
        
        Args:
            part_id: ID of part to get schedule for
            
        Returns:
            Schedule dictionary or None if not found
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                '''
                SELECT id, part_id, interval_days, next_due, advance_notice_hours, 
                       created_at, schedule_type, schedule_data
                FROM maintenance_schedule
                WHERE part_id = ?
                ORDER BY next_due ASC
                LIMIT 1
                ''',
                (part_id,)
            )
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
                
            # Parse schedule data
            schedule_data = {}
            try:
                if row[7]:  # schedule_data
                    schedule_data = json.loads(row[7])
            except json.JSONDecodeError:
                pass
                
            # Build schedule dictionary
            return {
                'id': row[0],
                'part_id': row[1],
                'interval_days': row[2],
                'next_due': row[3],
                'advance_notice_hours': row[4],
                'created_at': row[5],
                'schedule_type': row[6],
                'schedule_data': schedule_data
            }
            
        except Exception as e:
            self.logger.error(f"Error getting part maintenance schedule: {e}")
            return None

    def get_maintenance_schedules(self, include_part_info=False):
        """
        Get all maintenance schedules
        
        Args:
            include_part_info: Whether to include part name and other info
            
        Returns:
            List of schedule dictionaries
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if include_part_info:
                cursor.execute(
                    '''
                    SELECT ms.id, ms.part_id, ms.interval_days, ms.next_due, ms.advance_notice_hours, 
                           ms.created_at, ms.schedule_type, ms.schedule_data,
                           p.data_json
                    FROM maintenance_schedule ms
                    LEFT JOIN cached_data p ON p.id = ms.part_id AND p.type = 'part'
                    ORDER BY ms.next_due ASC
                    '''
                )
            else:
                cursor.execute(
                    '''
                    SELECT id, part_id, interval_days, next_due, advance_notice_hours, 
                           created_at, schedule_type, schedule_data
                    FROM maintenance_schedule
                    ORDER BY next_due ASC
                    '''
                )
            
            rows = cursor.fetchall()
            conn.close()
            
            schedules = []
            for row in rows:
                # Parse schedule data
                schedule_data = {}
                try:
                    if row[7]:  # schedule_data
                        schedule_data = json.loads(row[7])
                except json.JSONDecodeError:
                    pass
                    
                # Build schedule dictionary
                schedule = {
                    'id': row[0],
                    'part_id': row[1],
                    'interval_days': row[2],
                    'next_due': row[3],
                    'advance_notice_hours': row[4],
                    'created_at': row[5],
                    'schedule_type': row[6],
                    'schedule_data': schedule_data
                }
                
                # Add part info if included
                if include_part_info and len(row) > 8 and row[8]:
                    try:
                        part_data = self._decrypt_data(row[8], None)
                        part_info = json.loads(part_data) if part_data else {}
                        
                        schedule['part_name'] = part_info.get('name', f"Part #{row[1]}")
                        schedule['machine_id'] = part_info.get('machine_id')
                        
                        # Get machine info
                        if schedule['machine_id']:
                            machine_data = self.get_machine_data(schedule['machine_id'])
                            if machine_data:
                                schedule['machine_name'] = machine_data.get('name', f"Machine #{schedule['machine_id']}")
                                schedule['site_id'] = machine_data.get('site_id')
                                
                                # Get site info
                                if schedule['site_id']:
                                    site_data = self.get_site_data(schedule['site_id'])
                                    if site_data:
                                        schedule['site_name'] = site_data.get('name', f"Site #{schedule['site_id']}")
                    except Exception as e:
                        self.logger.error(f"Error parsing part data: {e}")
                
                schedules.append(schedule)
                
            return schedules
            
        except Exception as e:
            self.logger.error(f"Error getting maintenance schedules: {e}")
            return []

    def get_upcoming_maintenance(self, days=7, include_overdue=True):
        """
        Get upcoming maintenance due within specified days
        
        Args:
            days: Number of days ahead to look
            include_overdue: Whether to include overdue maintenance
            
        Returns:
            List of maintenance schedules due soon
        """
        try:
            now = datetime.now()
            future = now + timedelta(days=days)
            
            now_str = now.isoformat()
            future_str = future.isoformat()
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if include_overdue:
                cursor.execute(
                    '''
                    SELECT ms.id, ms.part_id, ms.interval_days, ms.next_due, ms.advance_notice_hours, 
                           ms.created_at, ms.schedule_type, ms.schedule_data
                    FROM maintenance_schedule ms
                    WHERE ms.next_due <= ?
                    ORDER BY ms.next_due ASC
                    ''',
                    (future_str,)
                )
            else:
                cursor.execute(
                    '''
                    SELECT ms.id, ms.part_id, ms.interval_days, ms.next_due, ms.advance_notice_hours, 
                           ms.created_at, ms.schedule_type, ms.schedule_data
                    FROM maintenance_schedule ms
                    WHERE ms.next_due > ? AND ms.next_due <= ?
                    ORDER BY ms.next_due ASC
                    ''',
                    (now_str, future_str)
                )
            
            rows = cursor.fetchall()
            conn.close()
            
            # Process results
            schedules = []
            for row in rows:
                # Parse schedule data
                schedule_data = {}
                try:
                    if row[7]:  # schedule_data
                        schedule_data = json.loads(row[7])
                except json.JSONDecodeError:
                    pass
                    
                # Build schedule dictionary
                schedule = {
                    'id': row[0],
                    'part_id': row[1],
                    'interval_days': row[2],
                    'next_due': row[3],
                    'advance_notice_hours': row[4],
                    'created_at': row[5],
                    'schedule_type': row[6],
                    'schedule_data': schedule_data
                }
                
                # Add part and machine info
                self._add_part_context(schedule)
                
                # Calculate time until due
                try:
                    due_date = datetime.fromisoformat(schedule['next_due'])
                    time_until = due_date - now
                    schedule['days_until_due'] = time_until.days
                    schedule['hours_until_due'] = time_until.total_seconds() / 3600
                    schedule['is_overdue'] = time_until.total_seconds() < 0
                except (ValueError, TypeError):
                    schedule['days_until_due'] = 0
                    schedule['hours_until_due'] = 0
                    schedule['is_overdue'] = False
                
                schedules.append(schedule)
                
            return schedules
            
        except Exception as e:
            self.logger.error(f"Error getting upcoming maintenance: {e}")
            return []

    def _add_part_context(self, schedule):
        """Add part, machine, and site context to a schedule"""
        try:
            part_id = schedule.get('part_id')
            if not part_id:
                return
                
            # Get part data
            part_data = self.get_part_data(part_id)
            if not part_data:
                return
                
            schedule['part_name'] = part_data.get('name', f"Part #{part_id}")
            schedule['machine_id'] = part_data.get('machine_id')
            
            # Get machine info if available
            if schedule.get('machine_id'):
                machine_data = self.get_machine_data(schedule['machine_id'])
                if machine_data:
                    schedule['machine_name'] = machine_data.get('name', f"Machine #{schedule['machine_id']}")
                    schedule['site_id'] = machine_data.get('site_id')
                    
                    # Get site info if available
                    if schedule.get('site_id'):
                        site_data = self.get_site_data(schedule['site_id'])
                        if site_data:
                            schedule['site_name'] = site_data.get('name', f"Site #{schedule['site_id']}")
                            
        except Exception as e:
            self.logger.error(f"Error adding context to schedule: {e}")
