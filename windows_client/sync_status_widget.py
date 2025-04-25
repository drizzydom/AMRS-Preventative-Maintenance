import os
from datetime import datetime, timezone
from PyQt6.QtWidgets import (QWidget, QLabel, QProgressBar, QPushButton, QVBoxLayout, 
                           QHBoxLayout, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QIcon, QPixmap

class SyncStatusWidget(QWidget):
    """
    Widget to display synchronization status and provide sync controls
    for the Windows client application.
    """
    
    def __init__(self, sync_manager, parent=None):
        super().__init__(parent)
        self.sync_manager = sync_manager
        
        # Connect to sync manager signals
        self.sync_manager.sync_started.connect(self.on_sync_started)
        self.sync_manager.sync_completed.connect(self.on_sync_completed)
        self.sync_manager.sync_progress.connect(self.on_sync_progress)
        self.sync_manager.connection_state_changed.connect(self.on_connection_state_changed)
        
        # Set up UI
        self.init_ui()
        
        # Update display with current state
        self.on_connection_state_changed(self.sync_manager.is_connected())
        
        # Start timer to update "last sync" time
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_last_sync_text)
        self.update_timer.start(60000)  # Update every minute
    
    def init_ui(self):
        """Initialize the user interface"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Status section
        status_frame = QFrame()
        status_frame.setFrameShape(QFrame.Shape.StyledPanel)
        status_frame.setStyleSheet("background-color: #f5f5f5; border-radius: 5px;")
        
        status_layout = QVBoxLayout(status_frame)
        
        # Connection status
        connection_layout = QHBoxLayout()
        
        self.connection_icon = QLabel()
        self.connection_icon.setFixedSize(16, 16)
        connection_layout.addWidget(self.connection_icon)
        
        self.connection_label = QLabel("Connection Status: Unknown")
        connection_layout.addWidget(self.connection_label, 1)
        
        self.force_sync_button = QPushButton("Force Sync")
        self.force_sync_button.setToolTip("Force immediate synchronization")
        self.force_sync_button.clicked.connect(self.on_force_sync_clicked)
        connection_layout.addWidget(self.force_sync_button)
        
        status_layout.addLayout(connection_layout)
        
        # Last sync time
        self.last_sync_label = QLabel("Last Sync: Never")
        status_layout.addWidget(self.last_sync_label)
        
        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        # Add status frame to main layout
        main_layout.addWidget(status_frame)
        
        # Sync statistics section
        stats_frame = QFrame()
        stats_frame.setFrameShape(QFrame.Shape.StyledPanel)
        stats_frame.setStyleSheet("background-color: #f5f5f5; border-radius: 5px;")
        
        stats_layout = QVBoxLayout(stats_frame)
        
        self.pending_operations_label = QLabel("Pending Operations: 0")
        stats_layout.addWidget(self.pending_operations_label)
        
        self.pending_maintenance_label = QLabel("Pending Maintenance Records: 0")
        stats_layout.addWidget(self.pending_maintenance_label)
        
        self.failed_operations_label = QLabel("Failed Operations: 0")
        self.failed_operations_label.setStyleSheet("color: #d9534f;")
        stats_layout.addWidget(self.failed_operations_label)
        
        # Add stats frame to main layout
        main_layout.addWidget(stats_frame)
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
    
    def update_sync_stats(self):
        """Update the displayed sync statistics"""
        if not hasattr(self.sync_manager, 'db'):
            return
            
        # Get counts from the offline database
        db = self.sync_manager.db
        
        # Count pending operations
        pending_ops = len(db.get_pending_operations())
        self.pending_operations_label.setText(f"Pending Operations: {pending_ops}")
        
        # Count pending maintenance records
        pending_maintenance = len(db.get_pending_maintenance())
        self.pending_maintenance_label.setText(f"Pending Maintenance Records: {pending_maintenance}")
        
        # Count failed operations
        failed_ops = db.get_failed_operations_count()
        self.failed_operations_label.setText(f"Failed Operations: {failed_ops}")
        
        # Show/hide the failed operations label
        self.failed_operations_label.setVisible(failed_ops > 0)
    
    def update_last_sync_text(self):
        """Update the last sync time text"""
        last_sync = self.sync_manager.db.get_setting('last_sync')
        
        if not last_sync:
            self.last_sync_label.setText("Last Sync: Never")
            return
            
        try:
            sync_time = datetime.fromisoformat(last_sync)
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            
            # Calculate time difference
            diff = now - sync_time
            
            if diff.days > 0:
                sync_text = f"Last Sync: {diff.days} day(s) ago"
            elif diff.seconds >= 3600:
                sync_text = f"Last Sync: {diff.seconds // 3600} hour(s) ago"
            elif diff.seconds >= 60:
                sync_text = f"Last Sync: {diff.seconds // 60} minute(s) ago"
            else:
                sync_text = f"Last Sync: {diff.seconds} seconds ago"
                
            self.last_sync_label.setText(sync_text)
        except Exception as e:
            self.last_sync_label.setText(f"Last Sync: {last_sync}")
    
    @pyqtSlot()
    def on_force_sync_clicked(self):
        """Handle force sync button click"""
        if self.sync_manager.is_connected():
            self.sync_manager.force_sync()
            self.force_sync_button.setEnabled(False)
            QTimer.singleShot(3000, lambda: self.force_sync_button.setEnabled(True))
        else:
            self.show_error_message("Cannot sync while offline")
    
    @pyqtSlot()
    def on_sync_started(self):
        """Handle sync start event"""
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.force_sync_button.setEnabled(False)
    
    @pyqtSlot(bool, str)
    def on_sync_completed(self, success, message):
        """Handle sync completion event"""
        # Hide progress bar
        self.progress_bar.setVisible(False)
        
        # Update last sync time
        self.update_last_sync_text()
        
        # Update sync statistics
        self.update_sync_stats()
        
        # Re-enable force sync button
        self.force_sync_button.setEnabled(True)
    
    @pyqtSlot(int, int)
    def on_sync_progress(self, current, total):
        """Handle sync progress update"""
        if total > 0:
            progress_percent = int((current / total) * 100)
            self.progress_bar.setValue(progress_percent)
    
    @pyqtSlot(bool)
    def on_connection_state_changed(self, is_online):
        """Handle connection state change"""
        if is_online:
            # Online state
            self.connection_icon.setPixmap(self.get_status_icon("online"))
            self.connection_label.setText("Connection Status: Online")
            self.connection_label.setStyleSheet("color: #5cb85c;")
            self.force_sync_button.setEnabled(True)
        else:
            # Offline state
            self.connection_icon.setPixmap(self.get_status_icon("offline"))
            self.connection_label.setText("Connection Status: Offline")
            self.connection_label.setStyleSheet("color: #d9534f;")
            self.force_sync_button.setEnabled(False)
    
    def get_status_icon(self, status_type):
        """Get the appropriate status icon"""
        icon_path = None
        
        if status_type == "online":
            icon_path = os.path.join(os.path.dirname(__file__), "..", "static", "img", "online.png")
        elif status_type == "offline":
            icon_path = os.path.join(os.path.dirname(__file__), "..", "static", "img", "offline.png")
        
        # Use a default if the file doesn't exist
        if not icon_path or not os.path.exists(icon_path):
            return QPixmap(16, 16)  # Return an empty pixmap
        
        return QPixmap(icon_path).scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    
    def show_error_message(self, message):
        """Show an error message in the UI"""
        # In a real implementation, you might use a QMessageBox or toast notification
        print(f"ERROR: {message}")  # For now just print to console
