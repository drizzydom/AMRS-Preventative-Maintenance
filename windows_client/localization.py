"""
Localization module for AMRS Maintenance Tracker
Provides translation support for the application
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Optional, List
from PyQt6.QtCore import QTranslator, QLocale, QCoreApplication

class LocalizationManager:
    """
    Manages translations and localization for the application
    """
    
    def __init__(self, app_data_dir: Optional[Path] = None):
        """
        Initialize the localization manager
        
        Args:
            app_data_dir: Application data directory, will create a subdirectory for translations
        """
        self.logger = logging.getLogger("LocalizationManager")
        
        # Set up translations directory
        if app_data_dir:
            self.translations_dir = app_data_dir / "translations"
        else:
            self.translations_dir = Path(os.path.abspath(os.path.dirname(__file__))) / "translations"
        
        os.makedirs(self.translations_dir, exist_ok=True)
        
        # Create default translation file if it doesn't exist
        self.default_language = "en"
        self.default_file = self.translations_dir / f"{self.default_language}.json"
        
        if not self.default_file.exists():
            self._create_default_translation_file()
        
        # Load available languages
        self.available_languages = self._get_available_languages()
        
        # Initialize the currently loaded language
        self.current_language = self.default_language
        self.translations = self._load_translations(self.current_language)
        
        # Create Qt translator
        self.translator = QTranslator()
    
    def _create_default_translation_file(self):
        """Create the default English translation file"""
        default_translations = {
            "app_name": "AMRS Maintenance Tracker",
            "general": {
                "ok": "OK",
                "cancel": "Cancel",
                "save": "Save",
                "delete": "Delete",
                "edit": "Edit",
                "close": "Close",
                "back": "Back",
                "next": "Next",
                "search": "Search",
                "filter": "Filter",
                "settings": "Settings",
                "help": "Help",
                "about": "About",
                "logout": "Logout",
                "login": "Login",
                "username": "Username",
                "password": "Password",
                "error": "Error",
                "warning": "Warning",
                "info": "Information",
                "success": "Success",
                "loading": "Loading...",
                "refresh": "Refresh"
            },
            "login": {
                "title": "Login",
                "remember_me": "Remember me",
                "forgot_password": "Forgot password?",
                "login_button": "Login",
                "invalid_credentials": "Invalid username or password"
            },
            "dashboard": {
                "title": "Dashboard",
                "welcome": "Welcome, {username}!",
                "overview": "Overview",
                "sites": "Sites",
                "machines": "Machines",
                "parts": "Parts",
                "maintenance": "Maintenance"
            },
            "sync": {
                "status": "Sync Status",
                "online": "Online",
                "offline": "Offline",
                "last_sync": "Last sync: {time}",
                "force_sync": "Force Sync",
                "sync_in_progress": "Sync in progress...",
                "sync_complete": "Sync complete",
                "sync_failed": "Sync failed: {error}",
                "pending_operations": "Pending operations: {count}"
            },
            "maintenance": {
                "record": "Maintenance Record",
                "new_record": "New Maintenance Record",
                "edit_record": "Edit Maintenance Record",
                "date": "Date",
                "notes": "Notes",
                "completed_by": "Completed by",
                "is_preventative": "Preventative maintenance",
                "is_corrective": "Corrective maintenance",
                "next_maintenance": "Next maintenance due: {date}",
                "overdue": "Overdue",
                "due_soon": "Due soon",
                "mark_complete": "Mark Complete"
            },
            "analytics": {
                "title": "Analytics",
                "maintenance_stats": "Maintenance Statistics",
                "system_health": "System Health",
                "filter_by_date": "Filter by date",
                "start_date": "Start date",
                "end_date": "End date",
                "apply_filters": "Apply Filters",
                "total_count": "Total Maintenance",
                "preventative_count": "Preventative",
                "corrective_count": "Corrective",
                "unique_parts": "Unique Parts",
                "avg_time": "Avg. Time Between",
                "maintenance_trend": "Maintenance Trend",
                "maintenance_by_part": "Maintenance by Part",
                "no_data": "No data available",
                "loading_chart": "Loading chart..."
            },
            "settings": {
                "title": "Settings",
                "general": "General",
                "connection": "Connection",
                "display": "Display",
                "language": "Language",
                "server_url": "Server URL",
                "auto_connect": "Connect automatically at startup",
                "theme": "Theme",
                "system_theme": "System Theme",
                "light_theme": "Light Theme",
                "dark_theme": "Dark Theme",
                "sync_interval": "Sync interval (minutes)",
                "save_settings": "Save Settings",
                "reset_defaults": "Reset to Defaults"
            },
            "errors": {
                "connection_failed": "Connection to server failed",
                "sync_failed": "Synchronization failed",
                "data_not_found": "Data not found",
                "invalid_input": "Invalid input",
                "operation_failed": "Operation failed",
                "authentication_failed": "Authentication failed"
            }
        }
        
        try:
            with open(self.default_file, 'w', encoding='utf-8') as f:
                json.dump(default_translations, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"Created default translation file: {self.default_file}")
        except Exception as e:
            self.logger.error(f"Error creating default translation file: {e}")
    
    def _get_available_languages(self) -> List[Dict]:
        """
        Get list of available languages based on translation files
        
        Returns:
            List of language dictionaries with code and name
        """
        languages = []
        
        # Map of language codes to names
        language_names = {
            "en": "English",
            "es": "Español",
            "fr": "Français",
            "de": "Deutsch",
            "it": "Italiano",
            "pt": "Português",
            "ru": "Русский",
            "zh": "中文",
            "ja": "日本語",
            "ko": "한국어"
        }
        
        # Check available translation files
        for file in self.translations_dir.glob("*.json"):
            lang_code = file.stem
            
            # Get language name if known, otherwise use the code
            lang_name = language_names.get(lang_code, lang_code)
            
            languages.append({
                "code": lang_code,
                "name": lang_name,
                "file": str(file)
            })
        
        return languages
    
    def _load_translations(self, language_code: str) -> Dict:
        """
        Load translations for specified language
        
        Args:
            language_code: Two-letter language code (e.g., 'en', 'es')
            
        Returns:
            Dictionary of translations or empty dict if loading fails
        """
        file_path = self.translations_dir / f"{language_code}.json"
        
        if not file_path.exists():
            self.logger.warning(f"Translation file not found for language: {language_code}")
            # Fall back to default language if the requested one doesn't exist
            if language_code != self.default_language:
                return self._load_translations(self.default_language)
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                translations = json.load(f)
                
            self.logger.info(f"Loaded translations for language: {language_code}")
            return translations
        except Exception as e:
            self.logger.error(f"Error loading translations for {language_code}: {e}")
            # Fall back to default language if there's an error
            if language_code != self.default_language:
                return self._load_translations(self.default_language)
            return {}
    
    def change_language(self, language_code: str) -> bool:
        """
        Change the current language
        
        Args:
            language_code: Two-letter language code (e.g., 'en', 'es')
            
        Returns:
            True if language was changed successfully, False otherwise
        """
        if language_code == self.current_language:
            return True
            
        # Check if language is available
        available_codes = [lang["code"] for lang in self.available_languages]
        if language_code not in available_codes:
            self.logger.warning(f"Language not available: {language_code}")
            return False
        
        # Load translations for the new language
        translations = self._load_translations(language_code)
        if not translations:
            return False
            
        # Update current language and translations
        self.current_language = language_code
        self.translations = translations
        
        # Load Qt translator for this language
        qm_file = self.translations_dir / f"{language_code}.qm"
        if qm_file.exists():
            if self.translator.load(str(qm_file)):
                QCoreApplication.installTranslator(self.translator)
                self.logger.info(f"Installed Qt translator for language: {language_code}")
            else:
                self.logger.warning(f"Failed to load Qt translator: {qm_file}")
        
        return True
    
    def get_text(self, key: str, default: str = None) -> str:
        """
        Get translated text for a key
        
        Args:
            key: Translation key in dot notation (e.g., 'general.ok')
            default: Default text to return if key not found
            
        Returns:
            Translated text or default if not found
        """
        if not key:
            return default or key
            
        # Split the key into parts (e.g., 'general.ok' -> ['general', 'ok'])
        key_parts = key.split('.')
        
        # Navigate through the translations dictionary
        current = self.translations
        for part in key_parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default or key
        
        # If we reached a string, return it
        if isinstance(current, str):
            return current
        else:
            return default or key
    
    def get_formatted(self, key: str, **kwargs) -> str:
        """
        Get translated text with format variables
        
        Args:
            key: Translation key in dot notation
            **kwargs: Format variables to substitute in the text
            
        Returns:
            Formatted translation text
        """
        text = self.get_text(key)
        
        # Apply formatting if the text contains format placeholders
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            self.logger.warning(f"Error formatting text for key: {key}")
            return text
    
    def create_translation_template(self, output_file=None):
        """
        Create a translation template file based on the default (en) translation
        
        Args:
            output_file: Optional output file path, defaults to 'template.json' in translations dir
        """
        if not output_file:
            output_file = self.translations_dir / "template.json"
            
        try:
            # Load the default translations
            default_translations = self._load_translations(self.default_language)
            
            # Write the template file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(default_translations, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"Created translation template: {output_file}")
            return True
        except Exception as e:
            self.logger.error(f"Error creating translation template: {e}")
            return False
