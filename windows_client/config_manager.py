import os
import json
import logging
from pathlib import Path

class ConfigManager:
    """
    Manages configuration settings for the Windows client application.
    Provides methods to store and retrieve settings securely.
    """
    
    def __init__(self, config_dir=None):
        self.logger = logging.getLogger("ConfigManager")
        
        # Set up logging
        handler = logging.FileHandler("config_manager.log")
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        # Set up config directory
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # Default to user's home directory
            self.config_dir = Path(os.path.expanduser('~')) / '.amrs'
        
        # Ensure directory exists
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Path to config file
        self.config_path = self.config_dir / 'config.json'
        
        # Load configuration
        self.config = self._load_config()
        
        self.logger.info(f"ConfigManager initialized with config directory: {self.config_dir}")
    
    def _initialize_default_config(self):
        """Initialize the default configuration"""
        self.config = {
            'app_version': '1.0.0',
            'first_run': True,
            'server_url': 'http://localhost:5000',
            'sync_interval': 300,  # 5 minutes
            'auto_sync': True,
            'theme': {
                'theme': 'system',
                'custom_colors': {},
                'icon_theme': 'default'
            },
            'display': {
                'rows_per_page': 100,
                'font_size': 12,
                'font_family': 'Default',
                'date_format': 'yyyy-MM-dd',
                'time_format': 'HH:mm'
            },
            'accessibility': {
                'high_contrast': False,
                'large_text': False,
                'screen_reader_support': False,
                'keyboard_navigation': True,
                'reduced_motion': False
            },
            'performance': {
                'background_sync': True,
                'cache_data': True,
                'cache_lifetime': 3600,  # 1 hour
                'optimize_startup': True
            }
        }
    
    def _load_config(self):
        """Load configuration from file"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading config: {e}")
                return {}
        return {}
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f)
            self.logger.debug("Configuration saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
            return False
    
    def get(self, key, default=None):
        """Get a configuration value"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set a configuration value"""
        self.config[key] = value
        return self._save_config()
    
    def remove(self, key):
        """Remove a configuration value"""
        if key in self.config:
            del self.config[key]
            return self._save_config()
        return True
    
    def get_all(self):
        """Get all configuration values"""
        return self.config.copy()
    
    def clear(self):
        """Clear all configuration values"""
        self.config = {}
        return self._save_config()
    
    def get_database_config(self):
        """Get database configuration"""
        db_config = self.get('database', {})
        
        # Set defaults if not configured
        if not db_config:
            db_config = {
                'type': 'sqlite',  # 'sqlite' or 'postgresql'
                'path': str(self.config_dir / 'offline_data.db'),
                'encryption': True
            }
            self.set('database', db_config)
        
        return db_config
    
    def get_server_config(self):
        """Get server configuration"""
        server_config = self.get('server', {})
        
        # Set defaults if not configured
        if not server_config:
            server_config = {
                'url': 'http://localhost:8000',
                'timeout': 15,  # seconds
                'sync_interval': 300  # 5 minutes
            }
            self.set('server', server_config)
        
        return server_config
    
    def get_sync_config(self):
        """Get synchronization configuration"""
        sync_config = self.get('sync', {})
        
        # Set defaults if not configured
        if not sync_config:
            sync_config = {
                'batch_size': 10,
                'max_retries': 5,
                'conflict_resolution': 'server_wins',  # 'server_wins', 'client_wins', 'newest_wins'
                'data_expiry': 30  # days
            }
            self.set('sync', sync_config)
        
        return sync_config
