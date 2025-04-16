import os
import csv
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                          QDateEdit, QCheckBox, QGroupBox, QComboBox, QFileDialog, 
                          QMessageBox, QProgressBar, QTextEdit)
from PyQt6.QtCore import Qt, QDate, QDateTime, QThread, pyqtSignal

class ReportGeneratorWorker(QThread):
    """Worker thread for generating sync reports"""
    
    progress_updated = pyqtSignal(int, int)  # current, total
    report_finished = pyqtSignal(bool, str, str)  # success, message, file_path
    
    def __init__(self, offline_db, report_type, start_date, end_date, options, output_path):
        super().__init__()
        self.db = offline_db
        self.report_type = report_type
        self.start_date = start_date
        self.end_date = end_date
        self.options = options
        self.output_path = output_path
        self.logger = logging.getLogger("ReportGenerator")
    
    # ... existing code ...
    
    def _generate_sync_stats_report(self):
        """Generate a summary statistics report"""
        try:
            # Get statistics from database
            stats = self.db.get_sync_statistics(self.start_date, self.end_date)
            
            if not stats:
                return False, "No sync statistics available for the selected date range", ""
            
            # Determine file path
            if not self.output_path:
                filename = f"sync_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                if self.options.get('format') == 'json':
                    filename += ".json"
                else:
                    filename += ".csv"
                self.output_path = str(Path.home() / "Documents" / filename)
            
            # Format depends on options
            if self.options.get('format') == 'json':
                with open(self.output_path, 'w') as f:
                    json.dump({
                        "report_type": "sync_statistics",
                        "generated_at": datetime.now().isoformat(),
                        "start_date": self.start_date.isoformat(),
                        "end_date": self.end_date.isoformat(),
                        "statistics": stats
                    }, f, indent=2)
            else:  # Default to CSV
                with open(self.output_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    
                    # Write header
                    writer.writerow(['Metric', 'Value'])
                    
                    # Write data rows
                    for key, value in stats.items():
                        writer.writerow([key, value])
            
            return True, "Generated sync statistics report", self.output_path
            
        except Exception as e:
            self.logger.error(f"Error generating sync stats report: {str(e)}", exc_info=True)
            return False, f"Error generating sync stats report: {str(e)}", ""

class SyncReportGenerator(QDialog):
    """Dialog for generating synchronization reports"""
    
    def __init__(self, offline_db, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Synchronization Report Generator")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        self.db = offline_db
        self.worker = None
        
        # Set up logger
        self.logger = logging.getLogger("SyncReportGenerator")
        
        # Initialize UI
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Report type selection
        type_group = QGroupBox("Report Type")
        type_layout = QVBoxLayout(type_group)
        
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems([
            "Synchronization History", 
            "Failed Operations", 
            "Performance Metrics",
            "Synchronization Statistics"
        ])
        type_layout.addWidget(self.report_type_combo)
        
        layout.addWidget(type_group)
        
        # Date range selection
        date_group = QGroupBox("Date Range")
        date_layout = QHBoxLayout(date_group)
        
        date_layout.addWidget(QLabel("Start Date:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-1))
        date_layout.addWidget(self.start_date_edit)
        
        date_layout.addWidget(QLabel("End Date:"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        date_layout.addWidget(self.end_date_edit)
        
        layout.addWidget(date_group)
        
        # Report options
        options_group = QGroupBox("Report Options")
        options_layout = QVBoxLayout(options_group)
        
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["CSV", "JSON"])
        format_layout.addWidget(self.format_combo)
        options_layout.addLayout(format_layout)
        
        self.include_details_check = QCheckBox("Include detailed information")
        self.include_details_check.setChecked(True)
        options_layout.addWidget(self.include_details_check)
        
        layout.addWidget(options_group)
        
        # Output file selection
        output_group = QGroupBox("Output")
        output_layout = QHBoxLayout(output_group)
        
        self.output_path_label = QLabel("No output file selected")
        output_layout.addWidget(self.output_path_label, 1)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_output_file)
        output_layout.addWidget(self.browse_btn)
        
        layout.addWidget(output_group)
        
        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("Generate Report")
        self.generate_btn.clicked.connect(self.generate_report)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.generate_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def browse_output_file(self):
        """Browse for output file location"""
        # Get the file extension based on selected format
        file_ext = ".json" if self.format_combo.currentText() == "JSON" else ".csv"
        
        # Generate default filename
        default_filename = f"sync_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_ext}"
        
        # Show save dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Report As", str(Path.home() / "Documents" / default_filename),
            f"Report Files (*{file_ext});;All Files (*)"
        )
        
        if file_path:
            self.output_path_label.setText(file_path)
    
    def generate_report(self):
        """Generate the selected report"""
        # Get report parameters
        report_type_map = {
            "Synchronization History": "sync_history",
            "Failed Operations": "failed_operations",
            "Performance Metrics": "performance_metrics",
            "Synchronization Statistics": "sync_stats"
        }
        
        report_type = report_type_map[self.report_type_combo.currentText()]
        start_date = self.start_date_edit.date().toPyDate()
        end_date = self.end_date_edit.date().toPyDate()
        
        # Get output path
        output_path = self.output_path_label.text()
        if output_path == "No output file selected":
            output_path = None
        
        # Options
        options = {
            'format': self.format_combo.currentText().lower(),
            'include_details': self.include_details_check.isChecked()
        }
        
        # Check date range
        if start_date > end_date:
            QMessageBox.warning(self, "Invalid Date Range", "Start date must be before end date.")
            return
        
        # Disable controls during generation
        self.setControlsEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Generating report...")
        
        # Create and start worker
        self.worker = ReportGeneratorWorker(
            self.db, report_type, start_date, end_date, options, output_path
        )
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.report_finished.connect(self.report_generation_finished)
        self.worker.start()
    
    def update_progress(self, current, total):
        """Update the progress bar"""
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
    
    def report_generation_finished(self, success, message, file_path):
        """Handle report generation completion"""
        # Re-enable controls
        self.setControlsEnabled(True)
        
        # Update UI
        self.progress_bar.setVisible(False)
        self.status_label.setText(message)
        
        # Show result message
        if success:
            response = QMessageBox.information(
                self,
                "Report Generation Complete",
                f"{message}\n\nDo you want to open the report now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if response == QMessageBox.StandardButton.Yes:
                # Open the file with the default application
                try:
                    import os
                    if os.name == 'nt':  # Windows
                        os.startfile(file_path)
                    elif os.name == 'posix':  # macOS, Linux
                        import subprocess
                        subprocess.call(('open', file_path))
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Could not open the file: {str(e)}")
        else:
            QMessageBox.warning(self, "Report Generation Failed", message)
    
    def setControlsEnabled(self, enabled):
        """Enable or disable all controls"""
        self.report_type_combo.setEnabled(enabled)
        self.start_date_edit.setEnabled(enabled)
        self.end_date_edit.setEnabled(enabled)
        self.format_combo.setEnabled(enabled)
        self.include_details_check.setEnabled(enabled)
        self.browse_btn.setEnabled(enabled)
        self.generate_btn.setEnabled(enabled)
        self.cancel_btn.setEnabled(enabled)
