"""
Theme management and UI styling
"""
import os
import json
import logging
from typing import Dict, Optional
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt, QSettings

class ThemeManager:
    """
    Manages application themes and styling
    """
    
    # Color scheme definitions
    LIGHT_THEME = {
        'window': '#F5F5F5',
        'windowText': '#212529',
        'base': '#FFFFFF',
        'alternateBase': '#F8F9FA',
        'toolTipBase': '#FFFFDC',
        'toolTipText': '#000000',
        'text': '#212529',
        'button': '#E9ECEF',
        'buttonText': '#212529',
        'brightText': '#FFFFFF',
        'highlight': '#007BFF',
        'highlightedText': '#FFFFFF',
        'link': '#007BFF',
        'midlight': '#DEE2E6',
        'dark': '#ADB5BD',
        'mid': '#CED4DA',
        'shadow': '#343A40',
        'accent': '#0069D9',
        'error': '#DC3545',
        'warning': '#FFC107',
        'success': '#28A745',
        'info': '#17A2B8'
    }
    
    DARK_THEME = {
        'window': '#212529',
        'windowText': '#F8F9FA',
        'base': '#2A2E32',
        'alternateBase': '#343A40',
        'toolTipBase': '#495057',
        'toolTipText': '#F8F9FA',
        'text': '#F8F9FA',
        'button': '#343A40',
        'buttonText': '#F8F9FA',
        'brightText': '#F8F9FA',
        'highlight': '#007BFF',
        'highlightedText': '#FFFFFF',
        'link': '#45BAFF',
        'midlight': '#495057',
        'dark': '#212529',
        'mid': '#343A40',
        'shadow': '#121416',
        'accent': '#0D6EFD',
        'error': '#DC3545',
        'warning': '#FFC107',
        'success': '#28A745',
        'info': '#17A2B8'
    }
    
    # High contrast theme for accessibility
    HIGH_CONTRAST_THEME = {
        'window': '#000000',
        'windowText': '#FFFFFF',
        'base': '#000000',
        'alternateBase': '#0A0A0A',
        'toolTipBase': '#000000',
        'toolTipText': '#FFFFFF',
        'text': '#FFFFFF',
        'button': '#0057B3',
        'buttonText': '#FFFFFF',
        'brightText': '#FFFFFF',
        'highlight': '#FFFF00',
        'highlightedText': '#000000',
        'link': '#00CBFF',
        'midlight': '#0A0A0A',
        'dark': '#000000',
        'mid': '#0A0A0A',
        'shadow': '#000000',
        'accent': '#00CBFF',
        'error': '#FF0000',
        'warning': '#FFFF00',
        'success': '#00FF00',
        'info': '#00CBFF'
    }
    
    def __init__(self, config_manager=None):
        """
        Initialize the theme manager
        
        Args:
            config_manager: Optional configuration manager for storing settings
        """
        self.config = config_manager
        self.logger = logging.getLogger("ThemeManager")
        
        # Default theme settings
        self.settings = {
            'theme': 'system',  # 'system', 'light', 'dark', 'custom', 'high_contrast'
            'custom_colors': {},
            'icon_theme': 'default'
        }
        
        # Default palette to restore
        self._default_palette = None
        
        # Built-in theme definitions
        self.themes = {
            'light': self.LIGHT_THEME,
            'dark': self.DARK_THEME,
            'high_contrast': self.HIGH_CONTRAST_THEME
        }
        
        # Storage for custom themes
        self.custom_themes = {}
        
        # Load settings
        if self.config:
            self._load_settings()
            self._load_custom_themes()
    
    def _load_settings(self):
        """Load theme settings from config"""
        if not self.config:
            return
            
        try:
            theme_settings = self.config.get('theme', {})
            
            for key in self.settings:
                if key in theme_settings:
                    self.settings[key] = theme_settings[key]
                    
        except Exception as e:
            self.logger.error(f"Error loading theme settings: {e}")
    
    def _save_settings(self):
        """Save theme settings to config"""
        if not self.config:
            return
            
        try:
            self.config.set('theme', self.settings)
        except Exception as e:
            self.logger.error(f"Error saving theme settings: {e}")
    
    def _load_custom_themes(self):
        """Load custom themes from config or file"""
        if not self.config:
            return
            
        try:
            # Try to load from config first
            custom_themes = self.config.get('custom_themes', {})
            if custom_themes:
                self.custom_themes = custom_themes
                return
                
            # Otherwise load from file if it exists
            themes_file = os.path.join(os.path.dirname(__file__), 'custom_themes.json')
            if os.path.exists(themes_file):
                with open(themes_file, 'r', encoding='utf-8') as f:
                    self.custom_themes = json.load(f)
                    
        except Exception as e:
            self.logger.error(f"Error loading custom themes: {e}")
    
    def _save_custom_themes(self):
        """Save custom themes to config"""
        if not self.config:
            return
            
        try:
            self.config.set('custom_themes', self.custom_themes)
        except Exception as e:
            self.logger.error(f"Error saving custom themes: {e}")
    
    def get_current_theme_name(self) -> str:
        """
        Get current theme name
        
        Returns:
            Theme name as string
        """
        return self.settings['theme']
    
    def set_theme(self, theme_name: str) -> bool:
        """
        Set the active theme
        
        Args:
            theme_name: Name of theme to activate
            
        Returns:
            True if theme was activated, False otherwise
        """
        # Check if theme exists
        if theme_name not in ['system', 'light', 'dark', 'high_contrast'] and \
           theme_name not in self.custom_themes:
            self.logger.error(f"Theme {theme_name} does not exist")
            return False
            
        # Store previous theme
        previous_theme = self.settings['theme']
        
        # Update setting
        self.settings['theme'] = theme_name
        
        # Save settings
        if self.config:
            self._save_settings()
            
        # Apply theme if different
        if previous_theme != theme_name:
            self.apply_theme()
            
        return True
    
    def apply_theme(self):
        """
        Apply the active theme to the application
        
        Returns:
            True if successful, False otherwise
        """
        try:
            app = QApplication.instance()
            if not app:
                self.logger.error("No QApplication instance")
                return False
                
            # Store default palette on first run
            if self._default_palette is None:
                self._default_palette = app.palette()
                
            # Get theme colors
            theme_name = self.settings['theme']
            
            # For system theme, check OS preference
            if theme_name == 'system':
                # Check system color scheme preference
                settings = QSettings()
                is_dark = False
                
                if settings.contains('Appearance/ColorScheme'):
                    color_scheme = settings.value('Appearance/ColorScheme')
                    is_dark = color_scheme == 'dark'
                else:
                    # Alternatively, check if default window background is dark
                    window_color = self._default_palette.color(QPalette.ColorRole.Window)
                    is_dark = window_color.lightness() < 128
                
                # Use built-in dark or light theme
                theme_colors = self.DARK_THEME if is_dark else self.LIGHT_THEME
                
            elif theme_name == 'custom':
                # Use custom colors with fallbacks to light theme
                theme_colors = {}
                for key, value in self.LIGHT_THEME.items():
                    theme_colors[key] = self.settings['custom_colors'].get(key, value)
                    
            elif theme_name in self.custom_themes:
                # Use saved custom theme
                theme_colors = self.custom_themes[theme_name]
                
            else:
                # Use built-in theme
                theme_colors = self.themes.get(theme_name, self.LIGHT_THEME)
            
            # Create new palette 
            palette = QPalette()
            
            # Set colors
            palette.setColor(QPalette.ColorRole.Window, QColor(theme_colors['window']))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(theme_colors['windowText']))
            palette.setColor(QPalette.ColorRole.Base, QColor(theme_colors['base']))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(theme_colors['alternateBase']))
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(theme_colors['toolTipBase']))
            palette.setColor(QPalette.ColorRole.ToolTipText, QColor(theme_colors['toolTipText']))
            palette.setColor(QPalette.ColorRole.Text, QColor(theme_colors['text']))
            palette.setColor(QPalette.ColorRole.Button, QColor(theme_colors['button']))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor(theme_colors['buttonText']))
            palette.setColor(QPalette.ColorRole.BrightText, QColor(theme_colors['brightText']))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(theme_colors['highlight']))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor(theme_colors['highlightedText']))
            palette.setColor(QPalette.ColorRole.Link, QColor(theme_colors['link']))
            
            # Set the palette
            app.setPalette(palette)
            
            # Apply stylesheet if using a built-in theme
            if theme_name in ['light', 'dark', 'high_contrast']:
                app.setStyleSheet(self._get_stylesheet_for_theme(theme_name))
            elif theme_name in self.custom_themes:
                # Use custom stylesheet if defined
                if 'stylesheet' in self.custom_themes[theme_name]:
                    app.setStyleSheet(self.custom_themes[theme_name]['stylesheet'])
                else:
                    # Otherwise clear stylesheet
                    app.setStyleSheet("")
            else:
                # Clear stylesheet for system theme
                app.setStyleSheet("")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error applying theme: {e}")
            return False
    
    def _get_stylesheet_for_theme(self, theme_name: str) -> str:
        """
        Get stylesheet for a built-in theme
        
        Args:
            theme_name: Theme name
            
        Returns:
            Stylesheet string
        """
        if theme_name == 'light':
            return """
                QToolTip {
                    border: 1px solid #CED4DA;
                    background-color: #FFFFDC;
                    color: #000000;
                    padding: 5px;
                }
                
                QTableView {
                    gridline-color: #DEE2E6;
                }
                
                QPushButton {
                    background-color: #E9ECEF;
                    border: 1px solid #CED4DA;
                    padding: 5px 15px;
                    border-radius: 4px;
                }
                
                QPushButton:hover {
                    background-color: #DEE2E6;
                }
                
                QPushButton:pressed {
                    background-color: #CED4DA;
                }
                
                QPushButton:focus {
                    border: 1px solid #007BFF;
                }
            """
            
        elif theme_name == 'dark':
            return """
                QToolTip {
                    border: 1px solid #495057;
                    background-color: #495057;
                    color: #F8F9FA;
                    padding: 5px;
                }
                
                QTableView {
                    gridline-color: #495057;
                }
                
                QPushButton {
                    background-color: #343A40;
                    border: 1px solid #495057;
                    color: #F8F9FA;
                    padding: 5px 15px;
                    border-radius: 4px;
                }
                
                QPushButton:hover {
                    background-color: #495057;
                }
                
                QPushButton:pressed {
                    background-color: #212529;
                }
                
                QPushButton:focus {
                    border: 1px solid #007BFF;
                }
                
                QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {
                    background-color: #2A2E32;
                    border: 1px solid #495057;
                    color: #F8F9FA;
                    selection-background-color: #007BFF;
                    selection-color: #FFFFFF;
                }
                
                QTabWidget::pane {
                    border: 1px solid #495057;
                    background-color: #2A2E32;
                }
                
                QTabBar::tab {
                    background-color: #343A40;
                    color: #F8F9FA;
                    padding: 5px 10px;
                    border: 1px solid #495057;
                    border-bottom: none;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                }
                
                QTabBar::tab:selected {
                    background-color: #2A2E32;
                    border-bottom: none;
                }
            """
            
        elif theme_name == 'high_contrast':
            return """
                QWidget {
                    background-color: #000000;
                    color: #FFFFFF;
                }
                
                QToolTip {
                    border: 1px solid #FFFFFF;
                    background-color: #000000;
                    color: #FFFFFF;
                    padding: 5px;
                }
                
                QTableView {
                    gridline-color: #FFFFFF;
                }
                
                QPushButton {
                    background-color: #0057B3;
                    border: 2px solid #FFFFFF;
                    color: #FFFFFF;
                    padding: 5px 15px;
                    border-radius: 0px;
                }
                
                QPushButton:hover {
                    background-color: #0069D9;
                }
                
                QPushButton:pressed {
                    background-color: #004494;
                }
                
                QPushButton:focus {
                    border: 3px solid #FFFF00;
                }
                
                QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {
                    background-color: #000000;
                    border: 2px solid #FFFFFF;
                    color: #FFFFFF;
                    selection-background-color: #FFFF00;
                    selection-color: #000000;
                }
                
                QTabWidget::pane {
                    border: 2px solid #FFFFFF;
                    background-color: #000000;
                }
                
                QTabBar::tab {
                    background-color: #0057B3;
                    color: #FFFFFF;
                    padding: 5px 10px;
                    border: 2px solid #FFFFFF;
                }
                
                QTabBar::tab:selected {
                    background-color: #000000;
                }
                
                QCheckBox, QRadioButton {
                    color: #FFFFFF;
                    spacing: 8px;
                }
                
                QCheckBox::indicator, QRadioButton::indicator {
                    width: 16px;
                    height: 16px;
                    border: 2px solid #FFFFFF;
                    background-color: #000000;
                }
                
                QCheckBox::indicator:checked, QRadioButton::indicator:checked {
                    background-color: #FFFF00;
                }
            """
        
        return ""
    
    def save_custom_theme(self, name: str, colors: Dict, stylesheet: Optional[str] = None) -> bool:
        """
        Save a custom theme
        
        Args:
            name: Theme name
            colors: Dictionary of theme colors
            stylesheet: Optional custom stylesheet
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Make sure we have all required colors
            for key in self.LIGHT_THEME.keys():
                if key not in colors:
                    colors[key] = self.LIGHT_THEME[key]
            
            # Create theme
            theme = {
                'name': name,
                'colors': colors
            }
            
            # Add stylesheet if provided
            if stylesheet:
                theme['stylesheet'] = stylesheet
                
            # Save to custom themes
            self.custom_themes[name] = theme
            
            # Save to config
            self._save_custom_themes()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving custom theme: {e}")
            return False
    
    def delete_custom_theme(self, name: str) -> bool:
        """
        Delete a custom theme
        
        Args:
            name: Theme name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if theme exists
            if name not in self.custom_themes:
                self.logger.error(f"Theme {name} does not exist")
                return False
                
            # Remove from custom themes
            del self.custom_themes[name]
            
            # Save to config
            self._save_custom_themes()
            
            # If current theme was deleted, switch to system
            if self.settings['theme'] == name:
                self.set_theme('system')
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting custom theme: {e}")
            return False
    
    def get_theme_colors(self, theme_name: Optional[str] = None) -> Dict:
        """
        Get colors for a specific theme
        
        Args:
            theme_name: Theme name, or None for current theme
            
        Returns:
            Dictionary of theme colors
        """
        if theme_name is None:
            theme_name = self.settings['theme']
            
        if theme_name == 'custom':
            return self.settings['custom_colors']
            
        elif theme_name == 'system':
            # Determine system theme
            settings = QSettings()
            is_dark = False
            
            if settings.contains('Appearance/ColorScheme'):
                color_scheme = settings.value('Appearance/ColorScheme')
                is_dark = color_scheme == 'dark'
            else:
                # Check default palette color
                app = QApplication.instance()
                if app:
                    window_color = app.palette().color(QPalette.ColorRole.Window)
                    is_dark = window_color.lightness() < 128
            
            # Return appropriate theme
            return self.DARK_THEME if is_dark else self.LIGHT_THEME
            
        elif theme_name in self.custom_themes:
            return self.custom_themes[theme_name].get('colors', self.LIGHT_THEME)
            
        else:
            return self.themes.get(theme_name, self.LIGHT_THEME)
    
    def get_available_themes(self) -> Dict:
        """
        Get all available themes
        
        Returns:
            Dictionary mapping theme names to display names
        """
        themes = {
            'system': 'System Default',
            'light': 'Light Theme',
            'dark': 'Dark Theme',
            'high_contrast': 'High Contrast'
        }
        
        # Add custom themes
        for name in self.custom_themes:
            themes[name] = f"Custom: {name}"
            
        return themes
    
    def set_custom_color(self, key: str, color: str) -> bool:
        """
        Set a custom theme color
        
        Args:
            key: Color key (e.g., 'window', 'text')
            color: Hex color string
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update custom colors
            self.settings['custom_colors'][key] = color
            
            # Save settings
            self._save_settings()
            
            # Apply theme if using custom theme
            if self.settings['theme'] == 'custom':
                self.apply_theme()
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting custom color: {e}")
            return False
    
    def reset_to_default(self):
        """Reset to default theme"""
        # Reset settings
        self.settings = {
            'theme': 'system',
            'custom_colors': {},
            'icon_theme': 'default'
        }
        
        # Save settings
        if self.config:
            self._save_settings()
            
        # Restore default palette if available
        app = QApplication.instance()
        if app and self._default_palette:
            app.setPalette(self._default_palette)
            app.setStyleSheet("")
