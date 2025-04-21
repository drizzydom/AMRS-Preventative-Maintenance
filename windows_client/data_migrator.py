import os
import sys
import logging
import sqlite3
import json
import psycopg2
import csv
import tempfile
from datetime import datetime
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QProgressBar, 
                           QPushButton, QComboBox, QMessageBox, QFileDialog,
                           QHBoxLayout, QCheckBox, QGroupBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# Whitelist for allowed table names
ALLOWED_TABLES = {'user', 'site', 'machine', 'part', 'maintenance_record', 'pending_operations', 'cached_data', 'notification_history', 'maintenance_schedule'}

class MigrationWorker(QThread):
    """Worker thread for database migration tasks"""
    
    update_progress = pyqtSignal(int, int, str)  # current, total, message
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, source_type, source_path, target_type, target_conn_string, 
                tables=None, include_data=True):
        super().__init__()
        self.source_type = source_type
        self.source_path = source_path
        self.target_type = target_type
        self.target_conn_string = target_conn_string
        self.tables = tables or []
        self.include_data = include_data
        self.logger = logging.getLogger("MigrationWorker")
        
    def run(self):
        """Execute the migration process"""
        try:
            if self.source_type == "sqlite" and self.target_type == "postgresql":
                success, message = self._migrate_sqlite_to_postgres()
            elif self.source_type == "postgresql" and self.target_type == "sqlite":
                success, message = self._migrate_postgres_to_sqlite()
            else:
                success, message = False, f"Unsupported migration path: {self.source_type} to {self.target_type}"
            
            self.finished.emit(success, message)
        
        except Exception as e:
            self.logger.error(f"Migration error: {e}", exc_info=True)
            self.finished.emit(False, f"Migration failed: {str(e)}")
    
    def _migrate_sqlite_to_postgres(self):
        """Migrate data from SQLite to PostgreSQL"""
        try:
            # Connect to SQLite database
            sqlite_conn = sqlite3.connect(self.source_path)
            sqlite_cursor = sqlite_conn.cursor()
            
            # Connect to PostgreSQL database
            pg_conn = psycopg2.connect(self.target_conn_string)
            pg_cursor = pg_conn.cursor()
            
            # Get list of tables if not provided
            if not self.tables:
                sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                self.tables = [row[0] for row in sqlite_cursor.fetchall()]
            
            total_tables = len(self.tables)
            
            # Process each table
            for i, table in enumerate(self.tables):
                if table not in ALLOWED_TABLES:
                    continue
                self.update_progress.emit(i, total_tables, f"Processing table {table}...")
                
                # Get table schema
                sqlite_cursor.execute(f"PRAGMA table_info({table})")
                columns_info = sqlite_cursor.fetchall()
                column_names = [col[1] for col in columns_info]
                
                # Create table in PostgreSQL (with adjustments for PostgreSQL)
                create_sql = f"CREATE TABLE IF NOT EXISTS {table} ("
                column_defs = []
                
                for col in columns_info:
                    name = col[1]
                    sqlite_type = col[2].upper()
                    is_pk = col[5] == 1
                    not_null = col[3] == 1
                    
                    # Map SQLite types to PostgreSQL types
                    pg_type = self._map_sqlite_type_to_postgres(sqlite_type)
                    
                    # Build column definition
                    col_def = f"{name} {pg_type}"
                    if is_pk:
                        col_def += " PRIMARY KEY"
                    if not_null:
                        col_def += " NOT NULL"
                    
                    column_defs.append(col_def)
                
                create_sql += ", ".join(column_defs) + ")"
                
                # Create the table
                try:
                    pg_cursor.execute(create_sql)
                except Exception as e:
                    self.logger.warning(f"Error creating table {table}: {e}")
                    # Continue with next table if this one fails
                    continue
                
                # Copy data if requested
                if self.include_data:
                    if table not in ALLOWED_TABLES:
                        continue
                    # Get data from SQLite
                    sqlite_cursor.execute(f"SELECT * FROM {table}")
                    rows = sqlite_cursor.fetchall()
                    
                    if rows:
                        # Prepare for bulk insert using COPY
                        column_list = ", ".join(column_names)
                        placeholders = ", ".join(["%s" for _ in column_names])
                        
                        # Use a temporary file for COPY
                        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
                            # Write data to CSV
                            csv_writer = csv.writer(temp_file)
                            for row in rows:
                                csv_writer.writerow(row)
                            
                            temp_file.flush()
                        
                        # Use COPY to bulk load data
                        try:
                            with open(temp_file.name, 'r') as f:
                                pg_cursor.copy_from(f, table, sep=',', null='')
                        except Exception as e:
                            self.logger.error(f"Error copying data for table {table}: {e}")
                            
                            # Fall back to regular inserts if COPY fails
                            for row in rows:
                                try:
                                    insert_sql = f"INSERT INTO {table} ({column_list}) VALUES ({placeholders})"
                                    pg_cursor.execute(insert_sql, row)
                                except Exception as insert_e:
                                    self.logger.warning(f"Error inserting row into {table}: {insert_e}")
                        
                        # Delete the temp file
                        os.unlink(temp_file.name)
            
            # Commit changes
            pg_conn.commit()
            
            # Close connections
            sqlite_conn.close()
            pg_conn.close()
            
            return True, f"Successfully migrated {total_tables} tables from SQLite to PostgreSQL"
        
        except Exception as e:
            self.logger.error(f"Migration error: {e}", exc_info=True)
            return False, f"Migration failed: {str(e)}"
    
    def _migrate_postgres_to_sqlite(self):
        """Migrate data from PostgreSQL to SQLite"""
        try:
            # Connect to PostgreSQL database
            pg_conn = psycopg2.connect(self.target_conn_string)
            pg_cursor = pg_conn.cursor()
            
            # Connect to SQLite database
            sqlite_conn = sqlite3.connect(self.source_path)
            sqlite_cursor = sqlite_conn.cursor()
            
            # Get list of tables if not provided
            if not self.tables:
                pg_cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
                self.tables = [row[0] for row in pg_cursor.fetchall()]
            
            total_tables = len(self.tables)
            
            # Process each table
            for i, table in enumerate(self.tables):
                if table not in ALLOWED_TABLES:
                    continue
                self.update_progress.emit(i, total_tables, f"Processing table {table}...")
                
                # Get table schema from PostgreSQL
                pg_cursor.execute(f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, (table,))
                
                columns_info = pg_cursor.fetchall()
                column_names = [col[0] for col in columns_info]
                
                # Get primary key information
                pg_cursor.execute(f"""
                    SELECT a.attname
                    FROM pg_index i
                    JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                    WHERE i.indrelid = %s::regclass AND i.indisprimary
                """, (table,))
                
                primary_keys = [row[0] for row in pg_cursor.fetchall()]
                
                # Create table in SQLite
                create_sql = f"CREATE TABLE IF NOT EXISTS {table} ("
                column_defs = []
                
                for col in columns_info:
                    name = col[0]
                    pg_type = col[1]
                    is_nullable = col[2] == "YES"
                    is_pk = name in primary_keys
                    
                    # Map PostgreSQL types to SQLite types
                    sqlite_type = self._map_postgres_type_to_sqlite(pg_type)
                    
                    # Build column definition
                    col_def = f"{name} {sqlite_type}"
                    if is_pk:
                        col_def += " PRIMARY KEY"
                    if not is_nullable:
                        col_def += " NOT NULL"
                    
                    column_defs.append(col_def)
                
                create_sql += ", ".join(column_defs) + ")"
                
                # Create the table
                try:
                    sqlite_cursor.execute(create_sql)
                except Exception as e:
                    self.logger.warning(f"Error creating table {table}: {e}")
                    # Continue with next table if this one fails
                    continue
                
                # Copy data if requested
                if self.include_data:
                    if table not in ALLOWED_TABLES:
                        continue
                    # Get data from PostgreSQL
                    column_list = ", ".join(column_names)
                    pg_cursor.execute(f"SELECT {column_list} FROM {table}")
                    rows = pg_cursor.fetchall()
                    
                    if rows:
                        # Prepare for bulk insert
                        placeholders = ", ".join(["?" for _ in column_names])
                        insert_sql = f"INSERT INTO {table} ({column_list}) VALUES ({placeholders})"
                        
                        # Use executemany for better performance
                        try:
                            sqlite_cursor.executemany(insert_sql, rows)
                        except Exception as e:
                            self.logger.error(f"Error bulk inserting into {table}: {e}")
                            
                            # Fall back to individual inserts
                            for row in rows:
                                try:
                                    sqlite_cursor.execute(insert_sql, row)
                                except Exception as insert_e:
                                    self.logger.warning(f"Error inserting row into {table}: {insert_e}")
            
            # Commit changes
            sqlite_conn.commit()
            
            # Close connections
            sqlite_conn.close()
            pg_conn.close()
            
            return True, f"Successfully migrated {total_tables} tables from PostgreSQL to SQLite"
        
        except Exception as e:
            self.logger.error(f"Migration error: {e}", exc_info=True)
            return False, f"Migration failed: {str(e)}"
    
    def _map_sqlite_type_to_postgres(self, sqlite_type):
        """Map SQLite data types to PostgreSQL data types"""
        sqlite_type = sqlite_type.upper()
        mapping = {
            "INTEGER": "INTEGER",
            "REAL": "DOUBLE PRECISION",
            "TEXT": "TEXT",
            "BLOB": "BYTEA",
            "BOOLEAN": "BOOLEAN",
            "NUMERIC": "NUMERIC",
            "DATETIME": "TIMESTAMP",
            "DATE": "DATE",
            "TIME": "TIME"
        }
        
        # Handle VARCHAR types
        if "VARCHAR" in sqlite_type:
            return sqlite_type  # Keep as is
        
        return mapping.get(sqlite_type, "TEXT")  # Default to TEXT for unknown types
    
    def _map_postgres_type_to_sqlite(self, pg_type):
        """Map PostgreSQL data types to SQLite data types"""
        pg_type = pg_type.lower()
        mapping = {
            "integer": "INTEGER",
            "bigint": "INTEGER",
            "smallint": "INTEGER",
            "double precision": "REAL",
            "real": "REAL",
            "numeric": "NUMERIC",
            "text": "TEXT",
            "character varying": "TEXT",
            "varchar": "TEXT",
            "char": "TEXT",
            "bytea": "BLOB",
            "boolean": "BOOLEAN",
            "timestamp": "DATETIME",
            "timestamptz": "DATETIME",
            "date": "DATE",
            "time": "TIME"
        }
        
        return mapping.get(pg_type, "TEXT")  # Default to TEXT for unknown types

class DataMigratorDialog(QDialog):
    """Dialog for migrating data between databases"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Database Migration Tool")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        # Set up logger
        self.logger = logging.getLogger("DataMigrator")
        
        # Initialize UI
        self.init_ui()
        
        # Initialize worker thread
        self.worker = None
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Source database section
        source_group = QGroupBox("Source Database")
        source_layout = QVBoxLayout(source_group)
        
        self.source_type_combo = QComboBox()
        self.source_type_combo.addItems(["SQLite", "PostgreSQL"])
        self.source_type_combo.currentTextChanged.connect(self.on_source_type_changed)
        source_layout.addWidget(QLabel("Database Type:"))
        source_layout.addWidget(self.source_type_combo)
        
        # Source path/connection string
        source_path_layout = QHBoxLayout()
        self.source_path_label = QLabel("Database File:")
        self.source_path_input = QLabel("No database selected")
        self.source_browse_btn = QPushButton("Browse...")
        self.source_browse_btn.clicked.connect(self.browse_source_db)
        
        source_path_layout.addWidget(self.source_path_label)
        source_path_layout.addWidget(self.source_path_input, 1)
        source_path_layout.addWidget(self.source_browse_btn)
        source_layout.addLayout(source_path_layout)
        
        layout.addWidget(source_group)
        
        # Target database section
        target_group = QGroupBox("Target Database")
        target_layout = QVBoxLayout(target_group)
        
        self.target_type_combo = QComboBox()
        self.target_type_combo.addItems(["PostgreSQL", "SQLite"])
        self.target_type_combo.currentTextChanged.connect(self.on_target_type_changed)
        target_layout.addWidget(QLabel("Database Type:"))
        target_layout.addWidget(self.target_type_combo)
        
        # Target path/connection string
        target_path_layout = QHBoxLayout()
        self.target_path_label = QLabel("Connection String:")
        self.target_path_input = QLabel("No target database configured")
        self.target_browse_btn = QPushButton("Configure...")
        self.target_browse_btn.clicked.connect(self.configure_target_db)
        
        target_path_layout.addWidget(self.target_path_label)
        target_path_layout.addWidget(self.target_path_input, 1)
        target_path_layout.addWidget(self.target_browse_btn)
        target_layout.addLayout(target_path_layout)
        
        layout.addWidget(target_group)
        
        # Options
        options_group = QGroupBox("Migration Options")
        options_layout = QVBoxLayout(options_group)
        
        self.include_data_check = QCheckBox("Include data (not just schema)")
        self.include_data_check.setChecked(True)
        options_layout.addWidget(self.include_data_check)
        
        layout.addWidget(options_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready to migrate data")
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Migration")
        self.start_btn.clicked.connect(self.start_migration)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        # Set initial state
        self.on_source_type_changed(self.source_type_combo.currentText())
        self.on_target_type_changed(self.target_type_combo.currentText())
    
    def on_source_type_changed(self, db_type):
        """Handle source database type change"""
        if db_type.lower() == "sqlite":
            self.source_path_label.setText("Database File:")
            self.source_browse_btn.setText("Browse...")
        else:
            self.source_path_label.setText("Connection String:")
            self.source_browse_btn.setText("Configure...")
        
        # Reset the source path
        self.source_path_input.setText("No database selected")
        self.source_path = None
    
    def on_target_type_changed(self, db_type):
        """Handle target database type change"""
        if db_type.lower() == "sqlite":
            self.target_path_label.setText("Database File:")
            self.target_browse_btn.setText("Browse...")
        else:
            self.target_path_label.setText("Connection String:")
            self.target_browse_btn.setText("Configure...")
        
        # Reset the target path
        self.target_path_input.setText("No target database configured")
        self.target_path = None
    
    def browse_source_db(self):
        """Browse for source database file or configure connection string"""
        source_type = self.source_type_combo.currentText().lower()
        
        if source_type == "sqlite":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select SQLite Database", "", "SQLite Database (*.db *.sqlite);;All Files (*)"
            )
            
            if file_path:
                self.source_path = file_path
                self.source_path_input.setText(file_path)
        else:
            # For PostgreSQL, show a dialog to configure connection string
            conn_string, ok = QInputDialog.getText(
                self, "PostgreSQL Connection", 
                "Enter PostgreSQL connection string:",
                text="postgresql://username:password@hostname:port/database"
            )
            
            if ok and conn_string:
                self.source_path = conn_string
                # Mask the password in the displayed string
                masked_conn = self._mask_password_in_conn_string(conn_string)
                self.source_path_input.setText(masked_conn)
    
    def configure_target_db(self):
        """Configure target database file or connection string"""
        target_type = self.target_type_combo.currentText().lower()
        
        if target_type == "sqlite":
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Set SQLite Database", "", "SQLite Database (*.db *.sqlite);;All Files (*)"
            )
            
            if file_path:
                self.target_path = file_path
                self.target_path_input.setText(file_path)
        else:
            # For PostgreSQL, show a dialog to configure connection string
            conn_string, ok = QInputDialog.getText(
                self, "PostgreSQL Connection", 
                "Enter PostgreSQL connection string:",
                text="postgresql://username:password@hostname:port/database"
            )
            
            if ok and conn_string:
                self.target_path = conn_string
                # Mask the password in the displayed string
                masked_conn = self._mask_password_in_conn_string(conn_string)
                self.target_path_input.setText(masked_conn)
    
    def _mask_password_in_conn_string(self, conn_string):
        """Mask the password in a connection string for display"""
        if "://" in conn_string and "@" in conn_string:
            parts = conn_string.split("://", 1)
            auth_parts = parts[1].split("@", 1)
            
            if ":" in auth_parts[0]:
                user_parts = auth_parts[0].split(":", 1)
                return f"{parts[0]}://{user_parts[0]}:****@{auth_parts[1]}"
        
        return conn_string
    
    def start_migration(self):
        """Start the migration process"""
        if not self.source_path:
            QMessageBox.warning(self, "Missing Source", "Please select a source database.")
            return
        
        if not self.target_path:
            QMessageBox.warning(self, "Missing Target", "Please configure a target database.")
            return
        
        # Confirm the migration
        response = QMessageBox.question(
            self,
            "Confirm Migration",
            "Are you sure you want to start the migration? This operation may take a while and can potentially overwrite data in the target database.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if response == QMessageBox.StandardButton.No:
            return
        
        # Disable controls during migration
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.source_type_combo.setEnabled(False)
        self.target_type_combo.setEnabled(False)
        self.source_browse_btn.setEnabled(False)
        self.target_browse_btn.setEnabled(False)
        self.include_data_check.setEnabled(False)
        
        # Reset progress bar
        self.progress_bar.setValue(0)
        self.status_label.setText("Initializing migration...")
        
        # Start worker thread
        self.worker = MigrationWorker(
            source_type=self.source_type_combo.currentText().lower(),
            source_path=self.source_path,
            target_type=self.target_type_combo.currentText().lower(),
            target_conn_string=self.target_path,
            include_data=self.include_data_check.isChecked()
        )
        
        self.worker.update_progress.connect(self.update_progress)
        self.worker.finished.connect(self.migration_finished)
        self.worker.start()
    
    def update_progress(self, current, total, message):
        """Update the progress bar and status label"""
        if total > 0:
            self.progress_bar.setValue(int(current * 100 / total))
        else:
            self.progress_bar.setValue(0)
        
        self.status_label.setText(message)
    
    def migration_finished(self, success, message):
        """Handle migration completion"""
        # Re-enable controls
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        self.source_type_combo.setEnabled(True)
        self.target_type_combo.setEnabled(True)
        self.source_browse_btn.setEnabled(True)
        self.target_browse_btn.setEnabled(True)
        self.include_data_check.setEnabled(True)
        
        # Update UI
        self.status_label.setText(message)
        
        if success:
            self.progress_bar.setValue(100)
            QMessageBox.information(self, "Migration Complete", message)
        else:
            self.progress_bar.setValue(0)
            QMessageBox.critical(self, "Migration Failed", message)
        
        # Clean up worker
        if self.worker:
            self.worker.wait()
            self.worker = None
