import os
import sys
import time
import logging
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, 
                            QProgressBar, QPushButton, QWidget)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QFont

from .sync_manager import SyncManager
from .offline_db import OfflineDatabase
from .api_client import ApiClient

class SyncWorker(QThread):
    """Background thread for synchronization tasks"""
    update_progress = pyqtSignal(int, int, str)  # current, total, message
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, api_client, offline_db):
        super().__init__()
        self.api_client = api_client
        self.offline_db = offline_db
        self.sync_manager = SyncManager(api_client, offline_db)
        
    def run(self):
        """Run the synchronization process"""
        try:
            # First check server connection
            self.update_progress.emit(1, 3, "Checking server connection...")
            server_available = self.api_client.check_server()
            
            if not server_available:
                self.update_progress.emit(1, 3, "Server unavailable, continuing in offline mode")
                time.sleep(2)  # Give user time to read the message
                self.finished.emit(False, "Continuing in offline mode")
                return
                
            # Attempt to authenticate with stored credentials
            self.update_progress.emit(2, 3, "Authenticating...")
            authenticated = self.api_client.authenticate_with_stored_credentials()
            
            if not authenticated:
                self.update_progress.emit(2, 3, "Authentication required")
                time.sleep(1)
                self.finished.emit(True, "Authentication required")
                return
                
            # Sync data
            self.update_progress.emit(3, 3, "Synchronizing data...")
            
            # Register for sync progress updates
            self.sync_manager.sync_progress.connect(
                lambda current, total: self.update_progress.emit(current, total, "Synchronizing...")
            )
            
            # Trigger sync and wait for completion
            self.sync_manager.force_sync()
            time.sleep(0.5)  # Brief pause for UI update
            
            self.finished.emit(True, "Synchronization complete")
            
        except Exception as e:
            self.update_progress.emit(0, 0, f"Error: {str(e)}")
            self.finished.emit(False, f"Error: {str(e)}")

class SyncScreen(QMainWindow):
    """Pre-login synchronization screen"""
    
    def __init__(self, api_client, offline_db):
        super().__init__()
        
        self.api_client = api_client
        self.offline_db = offline_db
        self.sync_required = True
        
        # Set window properties
        self.setWindowTitle("AMRS Maintenance Tracker - Synchronizing")
        self.setFixedSize(500, 400)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Add logo
        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), "..", "static", "img", "logo.png")
        if os.path.exists(logo_path):
            logo = QPixmap(logo_path)
            logo = logo.scaledToWidth(200, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(logo)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(logo_label)
            layout.addSpacing(20)
        
        # Add title
        title_label = QLabel("AMRS Maintenance Tracker")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Add status label
        self.status_label = QLabel("Initializing...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        layout.addSpacing(20)
        
        # Add progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress_bar)
        layout.addSpacing(30)
        
        # Add skip button to bypass sync
        self.skip_button = QPushButton("Continue Without Syncing")
        self.skip_button.clicked.connect(self.skip_sync)
        layout.addWidget(self.skip_button)
        
        # Add retry button (initially hidden)
        self.retry_button = QPushButton("Retry Sync")
        self.retry_button.clicked.connect(self.start_sync)
        self.retry_button.setVisible(False)
        layout.addWidget(self.retry_button)
        
        # Initialize sync worker
        self.sync_worker = None
        
        # Start sync process with slight delay
        QTimer.singleShot(500, self.start_sync)
    
    def start_sync(self):
        """Start the synchronization process"""
        self.progress_bar.setValue(0)
        self.status_label.setText("Connecting to server...")
        self.retry_button.setVisible(False)
        
        # Create and start worker thread
        self.sync_worker = SyncWorker(self.api_client, self.offline_db)
        self.sync_worker.update_progress.connect(self.update_progress)
        self.sync_worker.finished.connect(self.sync_finished)
        self.sync_worker.start()
    
    def update_progress(self, current, total, message):
        """Update the progress bar and status message"""
        if total > 0:
            progress = int((current / total) * 100)
            self.progress_bar.setValue(progress)
        
        self.status_label.setText(message)
    
    def sync_finished(self, success, message):
        """Handle completion of sync process"""
        if success:
            # Auto-close after a short delay
            self.status_label.setText(message)
            QTimer.singleShot(1000, self.accept)
        else:
            # Show retry button
            self.status_label.setText(message)
            self.retry_button.setVisible(True)
    
    def skip_sync(self):
        """Skip synchronization and continue"""
        self.sync_required = False
        self.accept()
    
    def accept(self):
        """Close this window and proceed"""
        self.close()
        
    def closeEvent(self, event):
        """Handle window close event"""
        # If worker thread is running, stop it
        if self.sync_worker and self.sync_worker.isRunning():
            self.sync_worker.terminate()
            self.sync_worker.wait()
        event.accept()
