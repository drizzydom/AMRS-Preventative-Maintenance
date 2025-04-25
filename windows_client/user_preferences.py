import os
import logging
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                          QCheckBox, QComboBox, QSpinBox, QPushButton, QTabWidget,
                          QGroupBox, QFormLayout, QFileDialog, QMessageBox, QColorDialog)
from PyQt6.QtCore import Qt, QSettings, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont

class UserPreferencesDialog(QDialog):
    """
    Dialog for managing user preferences and application settings
    """
    
    preferences_changed = pyqtSignal()  # Signal emitted when preferences are saved
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setMinimumWidth(600)
        self.setMinimumHeight(450)
        
        self.config_manager = config_manager
        self.original_settings = config_manager.get_all()
        
        # Set up logging
        self.logger = logging.getLogger("UserPreferences")
        
        # Initialize UI
        self.init_ui()
        
        # Load current preferences
        self.load_preferences()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Create tabs
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # General tab
        self.general_tab = QWidget()
        self.tab_widget.addTab(self.general_tab, "General")
        self.setup_general_tab()
        
        # Synchronization tab
        self.sync_tab = QWidget()
        self.tab_widget.addTab(self.sync_tab, "Synchronization")
        self.setup_sync_tab()
        
        # Display tab
        self.display_tab = QWidget()
        self.tab_widget.addTab(self.display_tab, "Display")
        self.setup_display_tab()
        
        # Advanced tab
        self.advanced_tab = QWidget()
        self.tab_widget.addTab(self.advanced_tab, "Advanced")
        self.setup_advanced_tab()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.restore_defaults_btn = QPushButton("Restore Defaults")
        self.restore_defaults_btn.clicked.connect(self.restore_defaults)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_preferences)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.restore_defaults_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def setup_general_tab(self):
        """Set up the general settings tab"""
        layout = QVBoxLayout(self.general_tab)
        
        # Server settings
        server_group = QGroupBox("Server Connection")
        server_layout = QFormLayout(server_group)
        
        self.server_url_edit = QLineEdit()
        server_layout.addRow("Server URL:", self.server_url_edit)
        
        self.auto_connect_check = QCheckBox("Automatically connect to server at startup")
        server_layout.addRow("", self.auto_connect_check)
        
        layout.addWidget(server_group)
        
        # Application behavior
        behavior_group = QGroupBox("Application Behavior")
        behavior_layout = QFormLayout(behavior_group)
        
        self.start_minimized_check = QCheckBox("Start minimized to system tray")
        behavior_layout.addRow("", self.start_minimized_check)
        
        self.minimize_to_tray_check = QCheckBox("Minimize to system tray when closing")
        behavior_layout.addRow("", self.minimize_to_tray_check)
        
        self.confirm_exit_check = QCheckBox("Confirm before exiting")
        behavior_layout.addRow("", self.confirm_exit_check)
        
        layout.addWidget(behavior_group)
        
        # Data directory
        data_group = QGroupBox("Data Storage")
        data_layout = QHBoxLayout(data_group)
        
        self.data_dir_edit = QLineEdit()
        self.data_dir_edit.setReadOnly(True)
        data_layout.addWidget(self.data_dir_edit)
        
        self.browse_data_dir_btn = QPushButton("Browse...")
        self.browse_data_dir_btn.clicked.connect(self.browse_data_directory)
        data_layout.addWidget(self.browse_data_dir_btn)
        
        layout.addWidget(data_group)
        
        layout.addStretch()
    
    def setup_sync_tab(self):
        """Set up the synchronization settings tab"""
        layout = QVBoxLayout(self.sync_tab)
        
        # Synchronization settings
        sync_group = QGroupBox("Synchronization Settings")
        sync_layout = QFormLayout(sync_group)
        
        self.sync_interval_spin = QSpinBox()
        self.sync_interval_spin.setRange(1, 1440)
        self.sync_interval_spin.setSuffix(" minutes")
        sync_layout.addRow("Sync interval:", self.sync_interval_spin)
        
        self.auto_sync_check = QCheckBox("Automatically sync when online")
        sync_layout.addRow("", self.auto_sync_check)
        
        self.background_sync_check = QCheckBox("Continue syncing in background")
        sync_layout.addRow("", self.background_sync_check)
        
        layout.addWidget(sync_group)
        
        # Conflict resolution
        conflict_group = QGroupBox("Conflict Resolution")
        conflict_layout = QFormLayout(conflict_group)
        
        self.conflict_strategy_combo = QComboBox()
        self.conflict_strategy_combo.addItems([
            "Server wins (use server version)",
            "Client wins (use local version)",
            "Newest wins (use most recent version)",
            "Ask me every time"
        ])
        conflict_layout.addRow("When conflicts occur:", self.conflict_strategy_combo)
        
        layout.addWidget(conflict_group)
        
        # Data pruning
        pruning_group = QGroupBox("Data Pruning")
        pruning_layout = QFormLayout(pruning_group)
        
        self.auto_prune_check = QCheckBox("Automatically prune old data")
        pruning_layout.addRow("", self.auto_prune_check)
        
        self.prune_days_spin = QSpinBox()
        self.prune_days_spin.setRange(7, 365)
        self.prune_days_spin.setSuffix(" days")
        pruning_layout.addRow("Keep history for:", self.prune_days_spin)
        
        layout.addWidget(pruning_group)
        
        layout.addStretch()
    
    def setup_display_tab(self):
        """Set up the display settings tab"""
        layout = QVBoxLayout(self.display_tab)
        
        # Theme settings
        theme_group = QGroupBox("Theme")
        theme_layout = QFormLayout(theme_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["System Default", "Light", "Dark", "Custom"])
        theme_layout.addRow("Application theme:", self.theme_combo)
        
        # Color picker buttons
        colors_layout = QHBoxLayout()
        
        self.primary_color_btn = QPushButton("Primary Color")
        self.primary_color_btn.clicked.connect(lambda: self.pick_color("primary_color"))
        colors_layout.addWidget(self.primary_color_btn)
        
        self.accent_color_btn = QPushButton("Accent Color")
        self.accent_color_btn.clicked.connect(lambda: self.pick_color("accent_color"))
        colors_layout.addWidget(self.accent_color_btn)
        
        theme_layout.addRow("Custom colors:", colors_layout)
        
        layout.addWidget(theme_group)
        
        # Language settings
        language_group = QGroupBox("Language")
        language_layout = QFormLayout(language_group)
        
        self.language_combo = QComboBox()
        self.language_layout = language_layout
        
        # Will be populated in load_preferences when languages are available
        self.language_combo.addItem("English")
        
        language_layout.addRow("Language:", self.language_combo)
        
        # Change language button
        self.change_language_btn = QPushButton("Change Language...")
        self.change_language_btn.clicked.connect(self.show_language_dialog)
        language_layout.addRow("", self.change_language_btn)
        
        layout.addWidget(language_group)
        
        # Font settings
        font_group = QGroupBox("Font")
        font_layout = QFormLayout(font_group)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        font_layout.addRow("Font size:", self.font_size_spin)
        
        layout.addWidget(font_group)
        
        # Table display
        table_group = QGroupBox("Table Display")
        table_layout = QFormLayout(table_group)
        
        self.rows_per_page_spin = QSpinBox()
        self.rows_per_page_spin.setRange(10, 1000)
        table_layout.addRow("Rows per page:", self.rows_per_page_spin)
        
        self.alt_row_color_check = QCheckBox("Use alternating row colors")
        table_layout.addRow("", self.alt_row_color_check)
        
        layout.addWidget(table_group)
        
        layout.addStretch()
    
    def setup_advanced_tab(self):
        """Set up the advanced settings tab"""
        layout = QVBoxLayout(self.advanced_tab)
        
        # Logging settings
        logging_group = QGroupBox("Logging")
        logging_layout = QFormLayout(logging_group)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["Debug", "Info", "Warning", "Error", "Critical"])
        logging_layout.addRow("Log level:", self.log_level_combo)
        
        self.log_retention_spin = QSpinBox()
        self.log_retention_spin.setRange(1, 365)
        self.log_retention_spin.setSuffix(" days")
        logging_layout.addRow("Log retention:", self.log_retention_spin)
        
        layout.addWidget(logging_group)
        
        # Diagnostics
        diag_group = QGroupBox("Diagnostics")
        diag_layout = QFormLayout(diag_group)
        
        self.collect_metrics_check = QCheckBox("Collect performance metrics")
        diag_layout.addRow("", self.collect_metrics_check)
        
        self.send_error_reports_check = QCheckBox("Send anonymous error reports")
        diag_layout.addRow("", self.send_error_reports_check)
        
        layout.addWidget(diag_group)
        
        # Security
        security_group = QGroupBox("Security")
        security_layout = QFormLayout(security_group)
        
        self.encrypt_data_check = QCheckBox("Encrypt local database")
        security_layout.addRow("", self.encrypt_data_check)
        
        self.auto_logout_spin = QSpinBox()
        self.auto_logout_spin.setRange(0, 1440)
        self.auto_logout_spin.setSuffix(" minutes (0 = never)")
        security_layout.addRow("Auto logout after:", self.auto_logout_spin)
        
        layout.addWidget(security_group)
        
        layout.addStretch()
    
    def load_preferences(self):
        """Load current preferences into UI controls"""
        try:
            # General tab
            server_config = self.config_manager.get_server_config()
            self.server_url_edit.setText(server_config.get('url', ''))
            self.auto_connect_check.setChecked(server_config.get('auto_connect', True))
            
            # Application behavior
            self.start_minimized_check.setChecked(self.config_manager.get('start_minimized', False))
            self.minimize_to_tray_check.setChecked(self.config_manager.get('minimize_to_tray', True))
            self.confirm_exit_check.setChecked(self.config_manager.get('confirm_exit', True))
            
            # Data directory
            db_config = self.config_manager.get_database_config()
            data_dir = os.path.dirname(db_config.get('path', ''))
            self.data_dir_edit.setText(data_dir)
            
            # Sync tab
            sync_config = self.config_manager.get_sync_config()
            self.sync_interval_spin.setValue(sync_config.get('sync_interval', 5))
            self.auto_sync_check.setChecked(sync_config.get('auto_sync', True))
            self.background_sync_check.setChecked(sync_config.get('background_sync', True))
            
            # Conflict resolution
            strategies = {
                'server_wins': 0,
                'client_wins': 1,
                'newest_wins': 2,
                'ask': 3
            }
            strategy = sync_config.get('conflict_resolution', 'server_wins')
            self.conflict_strategy_combo.setCurrentIndex(strategies.get(strategy, 0))
            
            # Data pruning
            self.auto_prune_check.setChecked(self.config_manager.get('auto_prune', True))
            self.prune_days_spin.setValue(self.config_manager.get('default_retention_days', 90))
            
            # Display tab
            display = self.config_manager.get('display', {})
            themes = {'system': 0, 'light': 1, 'dark': 2, 'custom': 3}
            self.theme_combo.setCurrentIndex(themes.get(display.get('theme', 'system'), 0))
            
            self.font_size_spin.setValue(display.get('font_size', 12))
            self.rows_per_page_spin.setValue(display.get('rows_per_page', 100))
            self.alt_row_color_check.setChecked(display.get('alt_row_colors', True))
            
            # Language settings
            if hasattr(self, 'language_combo'):
                # Get available languages from localization manager if possible
                languages = []
                try:
                    from .localization import LocalizationManager
                    localization = LocalizationManager(self.config_manager.get('app_data_dir'))
                    self.localization = localization  # Store for later use
                    
                    languages = localization.available_languages
                    self.language_combo.clear()
                    
                    for lang in languages:
                        self.language_combo.addItem(lang["name"], lang["code"])
                        
                    # Set current language
                    current_lang = self.config_manager.get('language', 'en')
                    index = self.language_combo.findData(current_lang)
                    if index >= 0:
                        self.language_combo.setCurrentIndex(index)
                except Exception as e:
                    self.logger.error(f"Error loading language options: {e}")
            
            # Advanced tab
            log_levels = {'debug': 0, 'info': 1, 'warning': 2, 'error': 3, 'critical': 4}
            self.log_level_combo.setCurrentIndex(log_levels.get(self.config_manager.get('log_level', 'info'), 1))
            
            self.log_retention_spin.setValue(self.config_manager.get('log_rotation_days', 7))
            self.collect_metrics_check.setChecked(self.config_manager.get('collect_system_metrics', True))
            self.send_error_reports_check.setChecked(self.config_manager.get('error_report_enabled', True))
            
            self.encrypt_data_check.setChecked(db_config.get('encryption', True))
            self.auto_logout_spin.setValue(self.config_manager.get('auto_logout_minutes', 30))
            
        except Exception as e:
            self.logger.error(f"Error loading preferences: {str(e)}", exc_info=True)
            QMessageBox.warning(self, "Error", f"Error loading preferences: {str(e)}")
    
    def save_preferences(self):
        """Save preferences to configuration"""
        try:
            # General tab - Server settings
            server_config = {
                'url': self.server_url_edit.text(),
                'auto_connect': self.auto_connect_check.isChecked(),
                'timeout': 15  # Default timeout
            }
            self.config_manager.set('server', server_config)
            
            # Application behavior
            self.config_manager.set('start_minimized', self.start_minimized_check.isChecked())
            self.config_manager.set('minimize_to_tray', self.minimize_to_tray_check.isChecked())
            self.config_manager.set('confirm_exit', self.confirm_exit_check.isChecked())
            
            # Data directory is handled by browse_data_directory
            
            # Sync tab
            sync_interval = self.sync_interval_spin.value()
            conflict_strategies = ['server_wins', 'client_wins', 'newest_wins', 'ask']
            selected_strategy = conflict_strategies[self.conflict_strategy_combo.currentIndex()]
            
            sync_config = {
                'sync_interval': sync_interval,
                'auto_sync': self.auto_sync_check.isChecked(),
                'background_sync': self.background_sync_check.isChecked(),
                'conflict_resolution': selected_strategy,
                'batch_size': 10  # Default batch size
            }
            self.config_manager.set('sync', sync_config)
            
            # Data pruning
            self.config_manager.set('auto_prune', self.auto_prune_check.isChecked())
            self.config_manager.set('default_retention_days', self.prune_days_spin.value())
            
            # Display tab
            themes = ['system', 'light', 'dark', 'custom']
            selected_theme = themes[self.theme_combo.currentIndex()]
            
            display_config = {
                'theme': selected_theme,
                'font_size': self.font_size_spin.value(),
                'rows_per_page': self.rows_per_page_spin.value(),
                'alt_row_colors': self.alt_row_color_check.isChecked()
            }
            self.config_manager.set('display', display_config)
            
            # Language settings
            if hasattr(self, 'language_combo') and self.language_combo.currentData():
                language_code = self.language_combo.currentData()
                self.config_manager.set('language', language_code)
            
            # Advanced tab
            log_levels = ['debug', 'info', 'warning', 'error', 'critical']
            selected_log_level = log_levels[self.log_level_combo.currentIndex()]
            
            self.config_manager.set('log_level', selected_log_level)
            self.config_manager.set('log_rotation_days', self.log_retention_spin.value())
            self.config_manager.set('collect_system_metrics', self.collect_metrics_check.isChecked())
            self.config_manager.set('error_report_enabled', self.send_error_reports_check.isChecked())
            
            # Database encryption
            db_config = self.config_manager.get_database_config()
            db_config['encryption'] = self.encrypt_data_check.isChecked()
            self.config_manager.set('database', db_config)
            
            self.config_manager.set('auto_logout_minutes', self.auto_logout_spin.value())
            
            # Emit signal that preferences have changed
            self.preferences_changed.emit()
            
            # Accept the dialog
            self.accept()
            
        except Exception as e:
            self.logger.error(f"Error saving preferences: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error saving preferences: {str(e)}")
    
    def restore_defaults(self):
        """Restore default preferences"""
        response = QMessageBox.question(
            self,
            "Restore Defaults",
            "Are you sure you want to restore all settings to default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if response == QMessageBox.StandardButton.Yes:
            # Set default values for all controls
            self.server_url_edit.setText("http://localhost:10000")
            self.auto_connect_check.setChecked(True)
            self.start_minimized_check.setChecked(False)
            self.minimize_to_tray_check.setChecked(True)
            self.confirm_exit_check.setChecked(True)
            
            self.sync_interval_spin.setValue(5)
            self.auto_sync_check.setChecked(True)
            self.background_sync_check.setChecked(True)
            self.conflict_strategy_combo.setCurrentIndex(0)
            
            self.auto_prune_check.setChecked(True)
            self.prune_days_spin.setValue(90)
            
            self.theme_combo.setCurrentIndex(0)
            self.font_size_spin.setValue(12)
            self.rows_per_page_spin.setValue(100)
            self.alt_row_color_check.setChecked(True)
            
            self.log_level_combo.setCurrentIndex(1)
            self.log_retention_spin.setValue(7)
            self.collect_metrics_check.setChecked(True)
            self.send_error_reports_check.setChecked(True)
            
            self.encrypt_data_check.setChecked(True)
            self.auto_logout_spin.setValue(30)
    
    def browse_data_directory(self):
        """Browse for data directory"""
        current_dir = self.data_dir_edit.text()
        if not current_dir:
            current_dir = os.path.expanduser("~")
            
        directory = QFileDialog.getExistingDirectory(
            self, "Select Data Directory", current_dir,
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )
        
        if directory:
            # Ask for confirmation if changing existing data directory
            if (self.data_dir_edit.text() and 
                self.data_dir_edit.text() != directory and
                os.path.exists(os.path.join(self.data_dir_edit.text(), "offline_data.db"))):
                
                response = QMessageBox.warning(
                    self,
                    "Change Data Directory",
                    "Changing the data directory will not move your existing data. "
                    "Do you want to continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if response == QMessageBox.StandardButton.No:
                    return
            
            # Update the directory
            self.data_dir_edit.setText(directory)
            
            # Update the database path in config
            db_config = self.config_manager.get_database_config()
            db_config['path'] = os.path.join(directory, "offline_data.db")
            self.config_manager.set('database', db_config)
    
    def pick_color(self, color_key):
        """Show color picker dialog"""
        display = self.config_manager.get('display', {})
        current_color = display.get(color_key, "#000000")
        
        color = QColorDialog.getColor(
            Qt.GlobalColor.white, self, f"Select {color_key.replace('_', ' ').title()}"
        )
        
        if color.isValid():
            # Store the color in config
            display[color_key] = color.name()
            self.config_manager.set('display', display)
            
            # Update button style
            button = self.primary_color_btn if color_key == "primary_color" else self.accent_color_btn
            button.setStyleSheet(f"background-color: {color.name()}; color: {'black' if color.lightness() > 128 else 'white'};")
    
    def show_language_dialog(self):
        """Show language selection dialog"""
        from .language_dialog import LanguageDialog
        from .localization import LocalizationManager
        
        try:
            # Get the localization manager
            localization = getattr(self, 'localization', None)
            
            # If no localization manager exists, try to get it from parent
            if not localization and hasattr(self, 'parent') and hasattr(self.parent(), 'localization'):
                localization = self.parent().localization
            
            # If still no localization, create a new instance
            if not localization:
                config = self.config_manager.get_all()
                app_data_dir = config.get('app_data_dir')
                localization = LocalizationManager(app_data_dir)
            
            # Create and show language dialog
            dialog = LanguageDialog(localization, self)
            dialog.language_changed.connect(self._on_language_changed)
            dialog.exec()
            
        except Exception as e:
            import traceback
            print(f"Error showing language dialog: {e}")
            print(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"Could not open language settings: {str(e)}")

    def _on_language_changed(self, language_code):
        """Handle language change event"""
        # Update the language in preferences
        self.config_manager.set('language', language_code)
        
        # Update the UI
        QMessageBox.information(
            self, 
            "Language Changed",
            "The language has been changed. Some changes will take effect after restarting the application."
        )
        
        # Reload the preferences page to reflect new language
        self.load_preferences()
