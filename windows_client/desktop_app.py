import os
import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Import our components
from .config_manager import ConfigManager
from .offline_db import OfflineDatabase
from .api_client import ApiClient
from .sync_manager import SyncManager
from .batch_sync_manager import BatchSyncManager
from .db_migration import DatabaseMigration
from .security_utils import SecurityUtils
from .data_pruning import DataPruningManager
from .diagnostics import DiagnosticsManager
from .sync_screen import SyncScreen
from .main_window import MainWindow
from .localization_manager import LocalizationManager
from .notification_manager import NotificationManager
from .maintenance_scheduler import MaintenanceScheduler
from .theme_manager import ThemeManager
from .accessibility_helper import AccessibilityHelper
from .ui_enhancer import UIEnhancer
from .performance_profiler import PerformanceProfiler
from .startup_optimizer import StartupOptimizer
from .database_optimizer import DatabaseOptimizer

class DesktopApp:
    """Main desktop application class for AMRS Maintenance Tracker"""
    
    def __init__(self):
        # Set up logging
        self._configure_logging()
        
        # Initialize components
        self.logger.info("Initializing desktop application...")
        
        # Application data directory
        self.app_data_dir = self._get_app_data_dir()
        os.makedirs(self.app_data_dir, exist_ok=True)
        
        # Create startup optimizer
        self.startup_optimizer = StartupOptimizer(None)
        self.startup_optimizer.start_measurement()
        
        # Initialize components
        self._initialize_components()
        
        # Create Qt application
        self.qt_app = QApplication(sys.argv)
        self.qt_app.setApplicationName("AMRS Maintenance Tracker")
        self.qt_app.setOrganizationName("AMRS")
        
        # Set application style
        self.qt_app.setStyle('Fusion')
        
        # Main window
        self.main_window = None
    
    def _configure_logging(self):
        """Configure logging for the desktop application"""
        self.logger = logging.getLogger("DesktopApp")
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def _get_app_data_dir(self):
        """Get the application data directory"""
        # Use the platform-specific app data directory
        if sys.platform == 'win32':
            app_data = os.environ.get('APPDATA')
            if app_data:
                return Path(app_data) / 'AMRS-Maintenance-Tracker'
        elif sys.platform == 'darwin':  # macOS
            return Path.home() / 'Library' / 'Application Support' / 'AMRS-Maintenance-Tracker'
        
        # Fallback to home directory
        return Path.home() / '.amrs-maintenance-tracker'
    
    def _initialize_components(self):
        """Initialize all application components"""
        try:
            # Configuration
            self.config_manager = ConfigManager(self.app_data_dir)
            
            # Update startup optimizer with config
            self.startup_optimizer = StartupOptimizer(self.config_manager)
            
            # Security utilities
            self.security = SecurityUtils(self.app_data_dir)
            
            # Database
            db_path = self.app_data_dir / 'data' / 'offline_data.db'
            os.makedirs(db_path.parent, exist_ok=True)
            self.offline_db = OfflineDatabase(db_path, encrypt=True)
            
            # Database optimization
            self.db_optimizer = DatabaseOptimizer(db_path, self.config_manager)
            
            # Run database migrations
            self.db_migration = DatabaseMigration(db_path)
            self.db_migration.run_migrations()
            
            # Apply database optimizations
            if self.config_manager.get('performance', {}).get('optimize_startup', True):
                self.startup_optimizer.optimize_database(str(db_path))
            
            # Preload data in background if enabled
            self.startup_optimizer.preload_data(self.offline_db)
            
            # Theme manager
            self.theme_manager = ThemeManager(self.config_manager)
            
            # Accessibility helper
            self.accessibility_helper = AccessibilityHelper(self.config_manager)
            
            # UI enhancer
            self.ui_enhancer = UIEnhancer(self.theme_manager)
            
            # API client
            server_url = self.config_manager.get('server_url', 'http://localhost:10000')
            self.api_client = ApiClient(base_url=server_url, config_file=self.app_data_dir / 'config.json')
            
            # Initialize notification manager with system tray
            self.notification_manager = NotificationManager(self.config_manager)
            
            # Initialize maintenance scheduler
            self.scheduler = MaintenanceScheduler(self.offline_db, self.notification_manager)
            
            # Sync managers
            self.sync_manager = SyncManager(self.api_client, self.offline_db)
            self.batch_sync_manager = BatchSyncManager(self.api_client, self.offline_db)
            
            # Data pruning manager
            self.data_pruning = DataPruningManager(self.offline_db)
            
            # Diagnostics manager
            self.diagnostics = DiagnosticsManager(config=self.config_manager, app_data_dir=self.app_data_dir)
            
            # Performance profiler
            self.performance_profiler = self._initialize_profiler()
            
            # Localization manager
            self.localization = LocalizationManager(self.app_data_dir)
            
            # Load language preference
            language = self.config_manager.get('language', 'en')
            self.localization.change_language(language)
            
            self.logger.info("All components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing components: {e}", exc_info=True)
            raise
    
    def _initialize_profiler(self):
        """Initialize the performance profiler"""
        try:
            from .performance_profiler import profiler
            
            # Configure profiler with appropriate log level
            debug_mode = self.config_manager.get('debug_mode', False)
            log_level = logging.DEBUG if debug_mode else logging.INFO
            
            profiler = PerformanceProfiler(log_level=log_level)
            return profiler
            
        except Exception as e:
            self.logger.error(f"Error initializing performance profiler: {e}")
            return None
    
    def start(self):
        """Start the application"""
        try:
            # Apply theme
            self.theme_manager.apply_theme()
            
            # Start the maintenance scheduler
            self.scheduler.start()
            
            # Show pre-login sync screen
            sync_screen = SyncScreen(self.api_client, self.offline_db)
            
            # Apply accessibility and UI enhancements
            self.accessibility_helper.apply_to_widget(sync_screen)
            self.ui_enhancer.enhance_widget(sync_screen)
            
            if not sync_screen.exec():
                return False  # User canceled
            
            # Create and show main window
            self.main_window = MainWindow(
                self.config_manager, 
                self.api_client, 
                self.sync_manager,
                server_url=self.api_client.base_url,
                localization=self.localization,
                scheduler=self.scheduler,
                notification_manager=self.notification_manager,
                theme_manager=self.theme_manager,
                accessibility_helper=self.accessibility_helper,
                ui_enhancer=self.ui_enhancer
            )
            
            # Apply accessibility and UI enhancements to main window
            self.accessibility_helper.apply_to_widget(self.main_window)
            self.accessibility_helper.install_keyboard_shortcuts(self.main_window)
            
            self.main_window.show()
            
            # Start sync manager
            self.sync_manager.start()
            
            # Start batch sync manager
            self.batch_sync_manager.start()
            
            # Start data pruning
            self.data_pruning.start()
            
            # Start diagnostics
            self.diagnostics.start_monitoring()
            
            # End startup measurement
            startup_time = self.startup_optimizer.end_measurement()
            self.logger.info(f"Application started in {startup_time:.2f} seconds")
            
            # Run application
            return self.qt_app.exec()
            
        except Exception as e:
            self.logger.error(f"Error starting application: {e}", exc_info=True)
            return False
    
    def shutdown(self):
        """Shut down the application gracefully"""
        try:
            # Stop all background threads
            self.sync_manager.stop()
            self.batch_sync_manager.stop()
            self.data_pruning.stop()
            self.diagnostics.stop_monitoring()
            
            # Stop the scheduler
            if hasattr(self, 'scheduler'):
                self.scheduler.shutdown()
            
            # Clean up UI enhancements
            if hasattr(self, 'ui_enhancer'):
                self.ui_enhancer.cleanup_enhancements()
            
            # Generate and save performance report if profiler is available
            if hasattr(self, 'performance_profiler') and self.performance_profiler:
                report = self.performance_profiler.generate_startup_report()
                
                # Save report to log
                self.logger.info(f"Performance Report:\n{report}")
                
                # Save to file
                try:
                    report_path = self.app_data_dir / 'logs' / f'performance_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
                    with open(report_path, 'w') as f:
                        f.write(report)
                except:
                    pass
            
            self.logger.info("Application shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

def main():
    """Application entry point"""
    app = DesktopApp()
    result = app.start()
    app.shutdown()
    return result

if __name__ == "__main__":
    sys.exit(main())
