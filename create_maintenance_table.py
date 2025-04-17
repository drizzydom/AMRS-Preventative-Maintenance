#!/usr/bin/env python3
"""
Script to create the maintenance_log table in the database.
Run this script to add the new table for tracking maintenance history.
"""

import sqlite3
import os
from app import db, app
from db_utils import execute_sql
from sqlalchemy import text

def create_maintenance_log_table():
    """Create the maintenance_log table in the SQLite database."""
    try:
        with app.app_context():
            # Try SQLAlchemy method first
            execute_sql('''
                CREATE TABLE IF NOT EXISTS maintenance_log (
                    id SERIAL PRIMARY KEY,
                    part_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    notes TEXT,
                    FOREIGN KEY (part_id) REFERENCES part (id),
                    FOREIGN KEY (user_id) REFERENCES user (id)
                )
            ''')
            print("Successfully created maintenance_log table using SQLAlchemy")
            return True
    except Exception as e:
        print(f"SQLAlchemy method failed: {str(e)}")
        
        # Fallback to direct SQLite approach
        try:
            # Path to the SQLite database
            db_path = os.path.join(os.path.dirname(__file__), 'instance', 'maintenance.db')
            if not os.path.exists(db_path):
                print(f"Database file not found at {db_path}")
                return False
                
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if table already exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='maintenance_log'")
            if cursor.fetchone():
                print("Table maintenance_log already exists")
                conn.close()
                return True
                
            # Create table
            cursor.execute('''
                CREATE TABLE maintenance_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    machine_id INTEGER NOT NULL,
                    part_id INTEGER NOT NULL,
                    performed_by VARCHAR(100) NOT NULL,
                    invoice_number VARCHAR(50),
                    maintenance_date DATETIME NOT NULL,
                    notes TEXT,
                    FOREIGN KEY (machine_id) REFERENCES machine (id),
                    FOREIGN KEY (part_id) REFERENCES part (id)
                )
            ''')
            
            conn.commit()
            conn.close()
            print("Successfully created maintenance_log table using direct SQLite")
            return True
        except Exception as sqlite_error:
            print(f"Direct SQLite method also failed: {str(sqlite_error)}")
            return False

if __name__ == "__main__":
    create_maintenance_log_table()
