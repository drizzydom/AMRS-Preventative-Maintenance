import os
import sys
import logging
import argparse
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from .config_manager import ConfigManager
from .offline_db import OfflineDatabase
from .api_client import ApiClient
from .sync_manager import SyncManager
from .main_window import MainWindow
from .db_migration import DatabaseMigration
from .security_utils import SecurityUtils

# Create logger for the application module
logger = logging.getLogger("Application")

class Application:
    """Main application class for the Windows client"""
    
    def __init__(self):
        # Parse command line arguments
        self.args = self.parse_arguments()
        
        # Set up logging
        self.setup_logging()
        
        # Set up application directories
        self.setup_directories()
        
        # Initialize components
        self.init_components()
        
        # Initialize Qt application
        self.qt_app = QApplication(sys.argv)
        self.qt_app.setApplicationName("AMRS Maintenance Tracker")
        self.qt_app.setOrganizationName("AMRS")
        self.qt_app.setOrganizationDomain("amrs.com")
        
        # Show splash screen
        # self.show_splash_screen()
        
        # Create and show the main window
        self.main_window = None
        
    def parse_arguments(self):
        """Parse command line arguments"""
        parser = argparse.ArgumentParser(description="AMRS Maintenance Tracker Windows Client")
        parser.add_argument("--server", help="Server URL")
        parser.add_argument("--offline", action="store_true", help="Start in offline mode")
        parser.add_argument("--debug", action="store_true", help="Enable debug logging")
        parser.add_argument("--no-encryption", action="store_true", help="Disable database encryption")
        parser.add_argument("--config-dir", help="Custom configuration directory")
        return parser.parse_args()
    
    def setup_logging(self):
        """Set up logging configuration"""
        log_level = logging.DEBUG if self.args.debug else logging.INFO
        
        # Determine log directory
        if self.args.config_dir:
            log_dir = Path(self.args.config_dir) / "logs"
        else:
            log_dir = Path(os.path.expanduser("~")) / ".amrs" / "logs"
        
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Set up file handler
        log_file = log_dir / "maintenance_tracker.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        
        # Set up console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        # Log basic information
        logger.info(f"AMRS Maintenance Tracker starting up")
        logger.info(f"Log file: {log_file}")
        logger.info(f"Debug mode: {'enabled' if self.args.debug else 'disabled'}")
    
    def setup_directories(self):
        """Set up application directories"""
        # Use custom config directory if provided
        if self.args.config_dir:
            self.config_dir = Path(self.args.config_dir)
        else:
            self.config_dir = Path(os.path.expanduser("~")) / ".amrs"
        
        # Create necessary directories
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.config_dir / "data", exist_ok=True)
        os.makedirs(self.config_dir / "logs", exist_ok=True)
        os.makedirs(self.config_dir / "temp", exist_ok=True)
        
        logger.info(f"Using configuration directory: {self.config_dir}")
    
    def init_components(self):
        """Initialize application components"""
        try:
            # Initialize configuration manager
            self.config_manager = ConfigManager(self.config_dir)
            logger.info("Initialized configuration manager")
            
            # Initialize security utilities
            self.security = SecurityUtils(self.config_dir)
            logger.info("Initialized security utilities")
            
            # Initialize offline database
            db_path = self.config_dir / "data" / "offline_data.db"
            use_encryption = not self.args.no_encryption
            self.offline_db = OfflineDatabase(db_path, encrypt=use_encryption)
            logger.info(f"Initialized offline database at {db_path}")
            
            # Run database migrations
            self.run_migrations()
            
            # Initialize API client
            server_url = self.args.server or self.config_manager.get_server_config().get('url')
            self.api_client = ApiClient(base_url=server_url, config_file=self.config_dir / "config.json")
            logger.info(f"Initialized API client with server URL: {server_url}")
            
            # Initialize sync manager
            self.sync_manager = SyncManager(self.api_client, self.offline_db)
            self.sync_manager.is_online = not self.args.offline  # Honor --offline flag
            logger.info("Initialized sync manager")
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.critical(f"Failed to initialize components: {e}", exc_info=True)
            self.show_error_and_exit("Initialization Error", 
                                    f"Failed to initialize application components: {str(e)}")
    
    def run_migrations(self):
        """Run database migrations"""
        try:
            migration = DatabaseMigration(self.offline_db.db_path)
            success = migration.run_migrations()
            
            if success:
                logger.info("Database migrations completed successfully")
            else:
                logger.error("Database migrations failed")
        except Exception as e:
            logger.error(f"Error running migrations: {e}", exc_info=True)
    
    def run(self):
        """Run the application"""
        try:
            # Create the main window
            self.main_window = MainWindow(
                self.config_manager,
                self.api_client,
                self.sync_manager,
                server_url=self.api_client.base_url
            )
            
            # Run the application
            return self.qt_app.exec()
            
        except Exception as e:
            logger.critical(f"Application crashed: {e}", exc_info=True)
            self.show_error_and_exit("Application Error", 
                                    f"The application encountered a critical error: {str(e)}")
            return 1
    
    def show_error_and_exit(self, title, message):
        """Show an error message and exit the application"""
        from PyQt6.QtWidgets import QMessageBox
        
        # Create an application instance if it doesn't exist yet
        if not hasattr(self, 'qt_app') or self.qt_app is None:
            self.qt_app = QApplication(sys.argv)
        
        # Show the error message
        QMessageBox.critical(None, title, message)
        
        # Exit with error code
        sys.exit(1)

def main():
    """Application entry point"""
    app = Application()
    sys.exit(app.run())

if __name__ == "__main__":
    main()
