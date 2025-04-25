"""
Dialog for creating and editing maintenance schedules
"""
import os
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                          QPushButton, QFormLayout, QComboBox, QSpinBox, QDateEdit,
                          QGroupBox, QDialogButtonBox, QMessageBox)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QIcon, QFont

class MaintenanceScheduleDialog(QDialog):
    """Dialog for creating or editing maintenance schedules"""
    
    schedule_created = pyqtSignal(str)  # Schedule ID
    schedule_updated = pyqtSignal(str)  # Schedule ID
    
    def __init__(self, offline_db, scheduler, part_id=None, schedule_id=None, parent=None):
        """
        Initialize the dialog
        
        Args:
            offline_db: Database instance
            scheduler: Maintenance scheduler instance
            part_id: Optional part ID for new schedules
            schedule_id: Optional schedule ID for editing existing schedule
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.db = offline_db
        self.scheduler = scheduler
        self.part_id = part_id
        self.schedule_id = schedule_id
        
        self.setWindowTitle("Schedule Maintenance" if not schedule_id else "Edit Maintenance Schedule")
        self.setMinimumWidth(450)
        
        self.init_ui()
        
        # Load schedule data if editing
        if schedule_id:
            self._load_schedule(schedule_id)
        elif part_id:
            self._initialize_part(part_id)
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Part selection section
        part_group = QGroupBox("Part")
        part_layout = QFormLayout(part_group)
        
        # Part combo box (will be populated later)
        self.part_combo = QComboBox()
        self.part_combo.setEditable(False)
        self.part_combo.currentIndexChanged.connect(self._on_part_changed)
        part_layout.addRow("Part:", self.part_combo)
        
        # Current maintenance info
        self.current_maintenance_label = QLabel("No maintenance history available")
        part_layout.addRow("Last maintenance:", self.current_maintenance_label)
        
        layout.addWidget(part_group)
        
        # Schedule settings
        schedule_group = QGroupBox("Maintenance Schedule")
        schedule_layout = QFormLayout(schedule_group)
        
        # Interval settings
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 365)
        self.interval_spin.setValue(30)  # Default to 30 days
        self.interval_spin.setSuffix(" days")
        schedule_layout.addRow("Maintenance interval:", self.interval_spin)
        
        # Next maintenance date
        self.next_due_edit = QDateEdit()
        self.next_due_edit.setCalendarPopup(True)
        self.next_due_edit.setDate(QDate.currentDate().addDays(30))  # Default to 30 days from now
        schedule_layout.addRow("Next maintenance due:", self.next_due_edit)
        
        # Advance notice settings
        self.advance_notice_spin = QSpinBox()
        self.advance_notice_spin.setRange(1, 72)
        self.advance_notice_spin.setValue(24)  # Default to 24 hours
        self.advance_notice_spin.setSuffix(" hours")
        schedule_layout.addRow("Send reminder:", self.advance_notice_spin)
        
        layout.addWidget(schedule_group)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.save_schedule)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Populate part list
        self._populate_parts()
    
    def _populate_parts(self):
        """Populate the parts combo box"""
        try:
            # Get parts from database
            parts = self.db.get_all_parts()
            
            if not parts:
                QMessageBox.warning(self, "No Parts", "No parts found in the database.")
                return
                
            # Clear and populate combo box
            self.part_combo.clear()
            
            for part in parts:
                part_name = part.get('name', f"Part #{part.get('id', 'unknown')}")
                self.part_combo.addItem(part_name, part.get('id'))
                
            # Select the specified part if provided
            if self.part_id:
                for i in range(self.part_combo.count()):
                    if self.part_combo.itemData(i) == self.part_id:
                        self.part_combo.setCurrentIndex(i)
                        break
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading parts: {str(e)}")
    
    def _initialize_part(self, part_id):
        """Initialize with a specific part"""
        try:
            # Get part data
            part_data = self.db.get_part_data(part_id)
            if not part_data:
                return
                
            # Display last maintenance info
            self._update_maintenance_info(part_id)
            
            # Check if part already has a schedule
            schedule = self.db.get_part_maintenance_schedule(part_id)
            if schedule:
                # Ask if user wants to edit existing schedule
                response = QMessageBox.question(
                    self, 
                    "Existing Schedule",
                    f"This part already has a maintenance schedule.\n\nWould you like to edit the existing schedule instead?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                
                if response == QMessageBox.StandardButton.Yes:
                    self._load_schedule(schedule['id'])
                else:
                    # Continue with creating a new schedule, but initialize from existing
                    self.interval_spin.setValue(int(schedule.get('interval_days', 30)))
                    
                    try:
                        next_due = datetime.fromisoformat(schedule.get('next_due')).date()
                        self.next_due_edit.setDate(QDate(next_due.year, next_due.month, next_due.day))
                    except (ValueError, TypeError):
                        pass
                    
                    self.advance_notice_spin.setValue(int(schedule.get('advance_notice_hours', 24)))
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error initializing part: {str(e)}")
    
    def _load_schedule(self, schedule_id):
        """Load an existing schedule for editing"""
        try:
            schedule = self.db.get_maintenance_schedule(schedule_id)
            if not schedule:
                QMessageBox.critical(self, "Error", "Schedule not found.")
                self.reject()
                return
                
            # Store schedule ID
            self.schedule_id = schedule_id
            
            # Update title
            self.setWindowTitle("Edit Maintenance Schedule")
            
            # Set part
            part_id = schedule.get('part_id')
            self.part_id = part_id
            
            # Select part in combo
            for i in range(self.part_combo.count()):
                if self.part_combo.itemData(i) == part_id:
                    self.part_combo.setCurrentIndex(i)
                    break
            
            # Set interval
            self.interval_spin.setValue(int(schedule.get('interval_days', 30)))
            
            # Set next due date
            try:
                next_due = datetime.fromisoformat(schedule.get('next_due')).date()
                self.next_due_edit.setDate(QDate(next_due.year, next_due.month, next_due.day))
            except (ValueError, TypeError):
                self.next_due_edit.setDate(QDate.currentDate().addDays(30))
            
            # Set advance notice
            self.advance_notice_spin.setValue(int(schedule.get('advance_notice_hours', 24)))
            
            # Update maintenance info
            self._update_maintenance_info(part_id)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading schedule: {str(e)}")
            self.reject()
    
    def _on_part_changed(self, index):
        """Handle part selection change"""
        part_id = self.part_combo.itemData(index)
        if part_id:
            self.part_id = part_id
            self._update_maintenance_info(part_id)
    
    def _update_maintenance_info(self, part_id):
        """Update maintenance history information"""
        try:
            # Get maintenance history for this part
            history = self.db.get_part_maintenance_history(part_id, limit=1)
            
            if history:
                # Get most recent record
                latest = history[0]
                timestamp = latest.get('timestamp', '')
                
                try:
                    # Format the timestamp
                    dt = datetime.fromisoformat(timestamp)
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M")
                    
                    # Calculate days since
                    days_since = (datetime.now() - dt).days
                    
                    self.current_maintenance_label.setText(f"Last performed: {formatted_time} ({days_since} days ago)")
                except (ValueError, TypeError):
                    self.current_maintenance_label.setText(f"Last performed: {timestamp}")
            else:
                self.current_maintenance_label.setText("No maintenance history available")
                
        except Exception as e:
            self.logger.error(f"Error updating maintenance info: {e}")
            self.current_maintenance_label.setText("Error getting maintenance history")
    
    def save_schedule(self):
        """Save the schedule"""
        try:
            # Get form data
            part_id = self.part_combo.currentData()
            
            if not part_id:
                QMessageBox.warning(self, "Missing Data", "Please select a part.")
                return
                
            interval_days = self.interval_spin.value()
            next_due = self.next_due_edit.date().toPyDate()
            advance_notice_hours = self.advance_notice_spin.value()
            
            # Convert next_due to datetime
            next_due_dt = datetime.combine(next_due, datetime.min.time())
            
            if self.schedule_id:
                # Update existing schedule
                success = self.scheduler.update_schedule(
                    self.schedule_id,
                    interval_days=interval_days,
                    next_due=next_due_dt,
                    advance_notice_hours=advance_notice_hours
                )
                
                if success:
                    self.schedule_updated.emit(self.schedule_id)
                    QMessageBox.information(self, "Success", "Maintenance schedule updated successfully.")
                    self.accept()
                else:
                    QMessageBox.critical(self, "Error", "Failed to update maintenance schedule.")
                    
            else:
                # Create new schedule
                schedule_id = self.scheduler.schedule_maintenance(
                    part_id,
                    interval_days,
                    next_due=next_due_dt,
                    advance_notice_hours=advance_notice_hours
                )
                
                if schedule_id:
                    self.schedule_created.emit(schedule_id)
                    QMessageBox.information(self, "Success", "Maintenance schedule created successfully.")
                    self.accept()
                else:
                    QMessageBox.critical(self, "Error", "Failed to create maintenance schedule.")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving schedule: {str(e)}")
