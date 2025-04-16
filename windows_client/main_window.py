import os
import sys
import logging
import webbrowser
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (QMainWindow, QApplication, QPushButton, QVBoxLayout, QHBoxLayout, 
                           QWidget, QLabel, QTabWidget, QSystemTrayIcon, QMenu, QMessageBox,
                           QSplitter, QFrame, QProgressBar, QDialog)
from PyQt6.QtCore import Qt, QSize, QUrl, QTimer
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWebEngineWidgets import QWebEngineView

from .sync_status_widget import SyncStatusWidget
from .sync_screen import SyncScreen
from .config_manager import ConfigManager
from .db_migration import DatabaseMigration
from .analytics.dashboard import AnalyticsDashboard

class ErrorDialog(QDialog):
    """Dialog to show error details"""
    def __init__(self, title, message, details=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # Error message
        error_label = QLabel(message)
        error_label.setWordWrap(True)
        layout.addWidget(error_label)
        
        # Details if provided
        if details:
            details_label = QLabel(details)
            details_label.setWordWrap(True)
            details_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            
            # Create a frame to contain the details
            details_frame = QFrame()
            details_frame.setFrameShape(QFrame.Shape.StyledPanel)
            details_frame.setStyleSheet("background-color: #f9f9f9; padding: 10px;")
            
            details_layout = QVBoxLayout(details_frame)
            details_layout.addWidget(details_label)
            
            layout.addWidget(details_frame)
        
        # OK button
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        
        layout.addLayout(button_layout)

class MainWindow(QMainWindow):
    """
    Main application window for the Windows client
    Incorporates web view, sync status, and system tray support
    """
    
    def __init__(self, config_manager, api_client, sync_manager, server_url=None, localization=None):
        super().__init__()
        
        self.config_manager = config_manager
        self.api_client = api_client
        self.sync_manager = sync_manager
        self.server_url = server_url or "http://localhost:5000"
        self.localization = localization  # Store localization manager
        
        self.logger = logging.getLogger("MainWindow")
        handler = logging.FileHandler("main_window.log")
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        # Initialize UI components
        self.init_ui()
        
        # Connect signals
        self.sync_manager.connection_state_changed.connect(self.on_connection_state_changed)
        self.sync_manager.sync_started.connect(self.on_sync_started)
        self.sync_manager.sync_completed.connect(self.on_sync_completed)
        
        # Start sync manager
        self.sync_manager.start()
        
        # Ensure window is visible
        self.show()
        
        # Set window state to maximized
        self.showMaximized()
        
        # Show pre-login sync screen
        self.show_pre_login_sync()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle(self._translate("app_name", "AMRS Maintenance Tracker"))
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "..", "static", "img", "logo.png")))
        self.setMinimumSize(1024, 768)
        
        # Create central widget with main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create menu bar
        self._create_menu_bar()
        
        # Create splitter for resizable sections
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Add web view to splitter
        self.web_view = QWebEngineView()
        splitter.addWidget(self.web_view)
        
        # Add status section to splitter
        status_container = QWidget()
        status_layout = QVBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add sync status widget
        self.sync_status = SyncStatusWidget(self.sync_manager)
        status_layout.addWidget(self.sync_status)
        
        # Add status container to splitter
        splitter.addWidget(status_container)
        
        # Set stretch factor to give more space to web view
        splitter.setStretchFactor(0, 3)  # Web view
        splitter.setStretchFactor(1, 1)  # Status section
        
        # Add splitter to main layout
        main_layout.addWidget(splitter)
        
        # Create tab widget for main content areas
        self.content_tabs = QTabWidget()
        main_layout.addWidget(self.content_tabs)
        
        # Add web view as first tab
        self.content_tabs.addTab(self.web_view, "Maintenance")
        
        # Add analytics dashboard tab if analytics is available
        try:
            self.analytics_dashboard = AnalyticsDashboard(self.sync_manager.db, self.sync_manager.diagnostics_manager)
            self.content_tabs.addTab(self.analytics_dashboard, "Analytics")
            # Connect refresh signal to update status
            self.analytics_dashboard.refresh_triggered.connect(lambda: self.statusBar().showMessage("Refreshing analytics..."))
        except ImportError as e:
            self.logger.warning(f"Analytics dashboard not available: {e}")
        except Exception as e:
            self.logger.error(f"Error initializing analytics dashboard: {e}", exc_info=True)
        
        # Create status bar
        self.statusBar().showMessage(self._translate("general.ready", "Ready"))
        
        # Create system tray icon
        self.create_tray_icon()
        
        # Navigate to the server URL
        self.web_view.load(QUrl(self.server_url))
        
        # Set up navigation refresh timer (auto-retry on failure)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.check_navigation)
        self.refresh_timer.start(5000)  # Check every 5 seconds
        
        # Connect web view signals
        self.web_view.loadStarted.connect(lambda: self.statusBar().showMessage("Loading..."))
        self.web_view.loadProgress.connect(lambda p: self.statusBar().showMessage(f"Loading... {p}%"))
        self.web_view.loadFinished.connect(self.on_load_finished)
    
    def _create_menu_bar(self):
        """Create the application menu bar"""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu(self._translate("general.file", "File"))
        
        # Settings action
        settings_action = QAction(self._translate("general.settings", "Settings"), self)
        settings_action.triggered.connect(self.show_preferences)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction(self._translate("general.exit", "Exit"), self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menu_bar.addMenu(self._translate("general.tools", "Tools"))
        
        # Force sync action
        sync_action = QAction(self._translate("sync.force_sync", "Force Sync"), self)
        sync_action.triggered.connect(self.force_sync)
        tools_menu.addAction(sync_action)
        
        # Change language action
        language_action = QAction(self._translate("settings.language", "Language"), self)
        language_action.triggered.connect(self.show_language_dialog)
        tools_menu.addAction(language_action)
        
        # Help menu
        help_menu = menu_bar.addMenu(self._translate("general.help", "Help"))
        
        # About action
        about_action = QAction(self._translate("general.about", "About"), self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
    
    def _translate(self, key, default=None):
        """Translate text using localization manager"""
        if self.localization:
            return self.localization.get_text(key, default)
        return default
    
    def show_preferences(self):
        """Show preferences dialog"""
        from .user_preferences import UserPreferencesDialog
        
        dialog = UserPreferencesDialog(self.config_manager, self)
        result = dialog.exec()
        
        # If dialog was accepted and we have a localization manager,
        # check if we need to update the language
        if result and self.localization:
            language = self.config_manager.get('language')
            if language != self.localization.current_language:
                self.localization.change_language(language)
                self._update_translations()
    
    def show_language_dialog(self):
        """Show language selection dialog"""
        from .language_dialog import LanguageDialog
        
        if self.localization:
            dialog = LanguageDialog(self.localization, self)
            dialog.language_changed.connect(self._on_language_changed)
            dialog.exec()
    
    def _on_language_changed(self, language_code):
        """Handle language change event"""
        # Save the language preference
        self.config_manager.set('language', language_code)
        
        # Update the UI
        self._update_translations()
    
    def _update_translations(self):
        """Update UI elements with new translations"""
        # Update window title
        self.setWindowTitle(self._translate("app_name", "AMRS Maintenance Tracker"))
        
        # Recreate menu bar with new translations
        self.menuBar().clear()
        self._create_menu_bar()
        
        # Update status bar text
        self.statusBar().showMessage(self._translate("general.ready", "Ready"))
        
        # Update tray menu text if exists
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self._update_tray_menu()
    
    def _update_tray_menu(self):
        """Update system tray menu with new translations"""
        tray_menu = QMenu()
        
        # Add menu actions
        show_action = QAction(self._translate("general.show", "Show"), self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        sync_action = QAction(self._translate("sync.force_sync", "Force Sync"), self)
        sync_action.triggered.connect(self.force_sync)
        tray_menu.addAction(sync_action)
        
        tray_menu.addSeparator()
        
        refresh_action = QAction(self._translate("general.refresh", "Refresh"), self)
        refresh_action.triggered.connect(self.refresh_web_view)
        tray_menu.addAction(refresh_action)
        
        tray_menu.addSeparator()
        
        exit_action = QAction(self._translate("general.exit", "Exit"), self)
        exit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(exit_action)
        
        # Set the tray menu
        self.tray_icon.setContextMenu(tray_menu)
    
    def show_about_dialog(self):
        """Show about dialog"""
        QMessageBox.about(
            self, 
            self._translate("general.about", "About"),
            f"{self._translate('app_name', 'AMRS Maintenance Tracker')} v1.0.0\n\n"
            f"{self._translate('about.description', 'A maintenance tracking application that works online and offline.')}\n\n"
            f"© 2023 AMRS Technologies"
        )
    
    def create_tray_icon(self):
        """Create system tray icon and menu"""
        # Create the tray icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "..", "static", "img", "logo.png")))
        
        # Create the tray menu
        self._update_tray_menu()
        
        # Set tooltip
        self.tray_icon.setToolTip(self._translate("app_name", "AMRS Maintenance Tracker"))
        
        # Connect activation signal (double-click)
        self.tray_icon.activated.connect(self.on_tray_activated)
        
        # Show the tray icon
        self.tray_icon.show()
    
    def on_tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()
    
    def show_pre_login_sync(self):
        """Show the pre-login synchronization screen"""
        sync_screen = SyncScreen(self.api_client, self.sync_manager.db)
        sync_screen.exec()
    
    def check_navigation(self):
        """Check if navigation is working, retry if not"""
        if not hasattr(self, 'last_url'):
            self.last_url = self.web_view.url().toString()
            self.navigation_failures = 0
            return
        
        current_url = self.web_view.url().toString()
        
        # If URL hasn't changed and not at server URL, might be stuck
        if (current_url == self.last_url and 
            current_url == "about:blank" and
            self.navigation_failures < 3):
            
            self.navigation_failures += 1
            self.logger.warning(f"Navigation may be stuck, retrying ({self.navigation_failures}/3)")
            self.refresh_web_view()
        else:
            self.navigation_failures = 0
            
        self.last_url = current_url
    
    def refresh_web_view(self):
        """Refresh the web view"""
        self.web_view.load(QUrl(self.server_url))
    
    def force_sync(self):
        """Force synchronization"""
        if self.sync_manager.is_connected():
            self.sync_manager.force_sync()
            self.statusBar().showMessage(self._translate("sync.started", "Synchronization started"))
        else:
            self.statusBar().showMessage(self._translate("sync.offline", "Cannot sync while offline"))
    
    def on_load_finished(self, success):
        """Handle web page load completion"""
        if success:
            url = self.web_view.url().toString()
            self.statusBar().showMessage(f"{self._translate('general.loaded', 'Loaded')}: {url}")
        else:
            self.statusBar().showMessage(self._translate("general.failed_to_load", "Failed to load page"))
            
            # Check if offline and we're trying to load the server URL
            if not self.sync_manager.is_connected() and self.web_view.url().toString() == self.server_url:
                # Show offline message
                self.web_view.setHtml(self.get_offline_html())
    
    def on_connection_state_changed(self, is_online):
        """Handle connection state change"""
        if is_online:
            self.statusBar().showMessage(self._translate("general.online_mode", "Online mode"))
            
            # If we're showing the offline page, reload the real page
            if self.web_view.url().toString().startswith("data:"):
                self.refresh_web_view()
        else:
            self.statusBar().showMessage(self._translate("general.offline_mode", "Offline mode"))
            
            # If we're trying to show the server URL, show offline page instead
            if self.web_view.url().toString() == self.server_url:
                self.web_view.setHtml(self.get_offline_html())
        
        # Update analytics dashboard if it exists
        if hasattr(self, 'analytics_dashboard'):
            # Refresh data when connection state changes to online
            if is_online:
                self.analytics_dashboard.refresh_data()
    
    def on_sync_started(self):
        """Handle sync start event"""
        self.statusBar().showMessage(self._translate("sync.in_progress", "Synchronization in progress"))
    
    def on_sync_completed(self, success, message):
        """Handle sync completion event"""
        if success:
            self.statusBar().showMessage(f"{self._translate('sync.completed', 'Sync completed')}: {message}")
        else:
            self.statusBar().showMessage(f"{self._translate('sync.error', 'Sync error')}: {message}")
    
    def get_offline_html(self):
        """Generate HTML content for offline mode"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{self._translate("app_name", "AMRS Maintenance Tracker")} - {self._translate("general.offline_mode", "Offline Mode")}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                    color: #333;
                    text-align: center;
                    padding: 50px;
                    margin: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #FE7900;
                }}
                .status {{
                    margin: 30px 0;
                    padding: 15px;
                    background-color: #f8d7da;
                    border: 1px solid #f5c6cb;
                    border-radius: 5px;
                    color: #721c24;
                }}
                .info {{
                    margin-top: 30px;
                    font-size: 0.9em;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{self._translate("app_name", "AMRS Maintenance Tracker")}</h1>
                <div class="status">
                    <h2>{self._translate("general.currently_offline", "Currently Offline")}</h2>
                    <p>{self._translate("general.offline_message", "You are working in offline mode. Connection to the server is not available.")}</p>
                </div>
                <p>{self._translate("general.offline_continue", "You can continue working offline. Your changes will be synchronized when connection is restored.")}</p>
                <div class="info">
                    <p>{self._translate("general.last_sync_attempt", "Last sync attempt")}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>{self._translate("general.server_url", "Server URL")}: {self.server_url}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def show_error(self, title, message, details=None):
        """Show an error dialog"""
        dialog = ErrorDialog(title, message, details, self)
        return dialog.exec()
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Minimize to tray instead of closing
        if self.config_manager.get("minimize_to_tray", True):
            event.ignore()
            self.hide()
            
            # Show a balloon message
            if self.tray_icon.isVisible():
                self.tray_icon.showMessage(
                    self._translate("app_name", "AMRS Maintenance Tracker"),
                    self._translate("general.tray_message", "Application is still running in the system tray."),
                    QSystemTrayIcon.MessageIcon.Information,
                    3000
                )
        else:
            # Actually close the application
            event.accept()
