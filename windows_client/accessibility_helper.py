"""
Accessibility enhancements for improved usability
"""
import os
import logging
from PyQt6.QtWidgets import (QWidget, QPushButton, QLabel, QLineEdit, QComboBox,
                           QCheckBox, QRadioButton, QTabWidget, QMessageBox)
from PyQt6.QtCore import Qt, QObject, QEvent
from PyQt6.QtGui import QFontDatabase, QFont

class AccessibilityHelper:
    """
    Helper class for improving application accessibility
    """
    
    def __init__(self, config_manager=None):
        """
        Initialize accessibility helper
        
        Args:
            config_manager: Optional configuration manager for storing settings
        """
        self.config = config_manager
        self.logger = logging.getLogger("AccessibilityHelper")
        
        # Load settings
        self.settings = {
            'high_contrast': False,
            'large_text': False,
            'screen_reader_support': False,
            'keyboard_navigation': True,
            'reduced_motion': False,
            'font_family': 'Default',
            'font_size_adjustment': 0
        }
        
        if self.config:
            self._load_settings()
    
    def _load_settings(self):
        """Load accessibility settings from config"""
        if not self.config:
            return
            
        try:
            a11y = self.config.get('accessibility', {})
            
            for key in self.settings:
                if key in a11y:
                    self.settings[key] = a11y[key]
                    
        except Exception as e:
            self.logger.error(f"Error loading accessibility settings: {e}")
    
    def _save_settings(self):
        """Save accessibility settings to config"""
        if not self.config:
            return
            
        try:
            self.config.set('accessibility', self.settings)
        except Exception as e:
            self.logger.error(f"Error saving accessibility settings: {e}")
    
    def apply_to_widget(self, widget, recursive=True):
        """
        Apply accessibility enhancements to a widget
        
        Args:
            widget: Widget to enhance
            recursive: Whether to apply to child widgets recursively
        """
        if not widget:
            return
            
        try:
            # Apply based on widget type
            if isinstance(widget, QLabel):
                self._enhance_label(widget)
            elif isinstance(widget, QPushButton):
                self._enhance_button(widget)
            elif isinstance(widget, QLineEdit):
                self._enhance_text_input(widget)
            elif isinstance(widget, QComboBox):
                self._enhance_combo_box(widget)
            elif isinstance(widget, QCheckBox) or isinstance(widget, QRadioButton):
                self._enhance_checkbox(widget)
            elif isinstance(widget, QTabWidget):
                self._enhance_tab_widget(widget)
            
            # Apply general enhancements
            self._apply_font_adjustments(widget)
            self._apply_contrast_settings(widget)
            self._apply_focus_indication(widget)
            
            # Apply to children if recursive
            if recursive and hasattr(widget, 'children'):
                for child in widget.children():
                    if isinstance(child, QWidget):
                        self.apply_to_widget(child, recursive=True)
                        
        except Exception as e:
            self.logger.error(f"Error applying accessibility to widget: {e}")
    
    def _enhance_label(self, label):
        """Enhance accessibility for label"""
        # Store text in accessibleName if not set
        if not label.accessibleName() and label.text():
            label.setAccessibleName(label.text().replace('&', ''))
            
        # Make sure labels have proper for/buddy relationships if they're form labels
        if hasattr(label, 'buddy') and not label.buddy():
            # Look for a sibling input that could be the buddy
            parent = label.parent()
            if parent:
                for sibling in parent.children():
                    if isinstance(sibling, (QLineEdit, QComboBox, QCheckBox, QRadioButton)):
                        label.setBuddy(sibling)
                        break
    
    def _enhance_button(self, button):
        """Enhance accessibility for button"""
        # Set role
        button.setAccessibleDescription(f"Button: {button.text().replace('&', '')}")
        
        # Make sure there's a visible focus indicator
        button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def _enhance_text_input(self, text_input):
        """Enhance accessibility for text input"""
        # Set appropriate placeholder text if empty
        if not text_input.placeholderText() and text_input.accessibleName():
            text_input.setPlaceholderText(f"Enter {text_input.accessibleName()}")
            
        # Make sure there's auto-completion where appropriate
        if hasattr(text_input, 'setCompleter') and not text_input.completer():
            # Check for common fields that should have auto-completion
            name = text_input.accessibleName().lower() if text_input.accessibleName() else ""
            if any(field in name for field in ['email', 'mail']):
                text_input.setInputMethodHints(Qt.InputMethodHint.ImhEmailCharactersOnly)
            elif any(field in name for field in ['phone', 'mobile', 'cell']):
                text_input.setInputMethodHints(Qt.InputMethodHint.ImhDialableCharactersOnly)
            elif any(field in name for field in ['url', 'website', 'web']):
                text_input.setInputMethodHints(Qt.InputMethodHint.ImhUrlCharactersOnly)
    
    def _enhance_combo_box(self, combo):
        """Enhance accessibility for combo box"""
        # Make sure there's a visible focus indicator
        combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Set appropriate accessible description
        if not combo.accessibleDescription():
            combo.setAccessibleDescription("Dropdown selection box")
    
    def _enhance_checkbox(self, checkbox):
        """Enhance accessibility for checkbox or radio button"""
        # Set role
        if isinstance(checkbox, QRadioButton):
            checkbox.setAccessibleDescription(f"Radio button: {checkbox.text().replace('&', '')}")
        else:
            checkbox.setAccessibleDescription(f"Checkbox: {checkbox.text().replace('&', '')}")
            
        # Make sure there's a visible focus indicator
        checkbox.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def _enhance_tab_widget(self, tab_widget):
        """Enhance accessibility for tab widget"""
        # Make sure tab navigation works properly
        tab_widget.setTabBarAutoHide(False)  # Always show tab bar for accessibility
        
        # Set accessible names for each tab if not already set
        for i in range(tab_widget.count()):
            tab = tab_widget.widget(i)
            if tab and not tab.accessibleName():
                tab.setAccessibleName(tab_widget.tabText(i))
    
    def _apply_font_adjustments(self, widget):
        """Apply font adjustments based on accessibility settings"""
        if not hasattr(widget, 'font'):
            return
            
        # Get current font
        font = widget.font()
        
        # Apply font family if set
        if self.settings['font_family'] != 'Default':
            font.setFamily(self.settings['font_family'])
            
        # Apply font size adjustments
        if self.settings['large_text'] or self.settings['font_size_adjustment'] != 0:
            size_adjustment = 2 if self.settings['large_text'] else 0
            size_adjustment += self.settings['font_size_adjustment']
            
            if size_adjustment != 0:
                current_size = font.pointSize()
                if current_size > 0:  # Make sure it's a valid size
                    font.setPointSize(max(6, current_size + size_adjustment))
                else:
                    # If point size is not valid, use pixel size instead
                    current_px = font.pixelSize()
                    if current_px > 0:
                        font.setPixelSize(max(8, current_px + (size_adjustment * 2)))
        
        # Apply the modified font
        widget.setFont(font)
    
    def _apply_contrast_settings(self, widget):
        """Apply high contrast settings if enabled"""
        if not self.settings['high_contrast']:
            return
            
        # Skip if the widget has explicit styling already
        if widget.styleSheet():
            return
            
        # Apply high contrast colors based on widget type
        if isinstance(widget, QLabel):
            widget.setStyleSheet("color: white; background-color: transparent;")
        elif isinstance(widget, QPushButton):
            widget.setStyleSheet("""
                QPushButton {
                    color: white;
                    background-color: #0057b3;
                    border: 2px solid white;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #0069d9;
                }
                QPushButton:focus {
                    border: 3px solid yellow;
                }
            """)
        elif isinstance(widget, QLineEdit):
            widget.setStyleSheet("""
                QLineEdit {
                    color: white;
                    background-color: #303030;
                    border: 1px solid white;
                    selection-background-color: #0057b3;
                }
                QLineEdit:focus {
                    border: 2px solid yellow;
                }
            """)
        elif isinstance(widget, QComboBox):
            widget.setStyleSheet("""
                QComboBox {
                    color: white;
                    background-color: #303030;
                    border: 1px solid white;
                    padding: 3px;
                }
                QComboBox:focus {
                    border: 2px solid yellow;
                }
                QComboBox QAbstractItemView {
                    color: white;
                    background-color: #303030;
                    selection-background-color: #0057b3;
                }
            """)
    
    def _apply_focus_indication(self, widget):
        """Enhance focus indication for better keyboard navigation"""
        # Skip widgets that don't need focus
        if isinstance(widget, QLabel) and not widget.buddy():
            return
            
        # Make sure the widget can receive focus via keyboard
        if widget.focusPolicy() == Qt.FocusPolicy.NoFocus:
            widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            
        # Add focus visual indication if high contrast or keyboard navigation is enabled
        if self.settings['high_contrast'] or self.settings['keyboard_navigation']:
            # We already set focus styles for high contrast mode in _apply_contrast_settings
            if not self.settings['high_contrast']:
                # Add a focus style sheet that won't interfere with existing styles
                current_ss = widget.styleSheet()
                if ':focus' not in current_ss:
                    widget.setStyleSheet(current_ss + """
                        :focus {
                            border: 2px solid #0069d9;
                            outline: 1px solid white;
                        }
                    """)
    
    def install_keyboard_shortcuts(self, main_window):
        """
        Install keyboard shortcuts and event filter for keyboard navigation
        
        Args:
            main_window: Main application window
        """
        try:
            if not self.settings['keyboard_navigation']:
                return
                
            # Install event filter to enhance keyboard navigation
            keyboard_filter = KeyboardNavigation(main_window)
            main_window.installEventFilter(keyboard_filter)
            
        except Exception as e:
            self.logger.error(f"Error installing keyboard shortcuts: {e}")
    
    def set_setting(self, setting_name, value):
        """
        Change an accessibility setting
        
        Args:
            setting_name: Name of the setting to change
            value: New value for the setting
            
        Returns:
            True if setting was changed, False otherwise
        """
        if setting_name not in self.settings:
            return False
            
        if self.settings[setting_name] == value:
            return True  # No change needed
            
        self.settings[setting_name] = value
        
        # Save settings
        if self.config:
            self._save_settings()
            
        return True
    
    def get_available_fonts(self, accessibility_oriented=True):
        """
        Get a list of available fonts, optionally filtered to those good for accessibility
        
        Args:
            accessibility_oriented: Whether to return only fonts good for accessibility
            
        Returns:
            List of font family names
        """
        font_db = QFontDatabase()
        all_families = font_db.families()
        
        if not accessibility_oriented:
            return all_families
            
        # Filter to accessible fonts (common system fonts with good readability)
        accessible_fonts = []
        
        # Add sans-serif fonts first (generally more readable)
        for family in ["Arial", "Helvetica", "Verdana", "Tahoma", "Calibri", 
                      "Segoe UI", "Roboto", "Open Sans"]:
            if family in all_families:
                accessible_fonts.append(family)
                
        # Add dyslexia-friendly fonts if available
        for family in ["OpenDyslexic", "Comic Sans MS", "Lexie Readable"]:
            if family in all_families:
                accessible_fonts.append(family)
                
        # Add system default sans-serif
        system_sans = QFont().defaultFamily()
        if system_sans not in accessible_fonts:
            accessible_fonts.append(system_sans)
            
        return accessible_fonts
    
    def create_screen_reader_labels(self, window):
        """
        Add hidden labels for screen readers to improve context
        
        Args:
            window: Window to enhance with screen reader labels
            
        Returns:
            List of created labels
        """
        if not self.settings['screen_reader_support']:
            return []
            
        created_labels = []
        
        try:
            # Add context labels to different areas of the application
            sections = {
                'navigation': window.findChild(QWidget, 'navigation_sidebar'),
                'content': window.findChild(QWidget, 'main_content_area'),
                'status': window.findChild(QWidget, 'status_bar_area')
            }
            
            for name, widget in sections.items():
                if widget:
                    label = QLabel(f"{name.capitalize()} section", widget)
                    label.setObjectName(f"sr_label_{name}")
                    label.setVisible(False)  # Hidden visually but accessible to screen readers
                    label.setAccessibleName(f"{name.capitalize()} section")
                    label.setAccessibleDescription(f"Start of {name} section")
                    created_labels.append(label)
                    
            # Add end-of-section markers for better navigation
            for name, widget in sections.items():
                if widget:
                    label = QLabel(f"End of {name} section", widget)
                    label.setObjectName(f"sr_label_{name}_end")
                    label.setVisible(False)
                    label.setAccessibleName(f"End of {name} section")
                    label.setAccessibleDescription(f"End of {name} section")
                    created_labels.append(label)
                    
        except Exception as e:
            self.logger.error(f"Error creating screen reader labels: {e}")
            
        return created_labels

class KeyboardNavigation(QObject):
    """Event filter for enhanced keyboard navigation"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger("KeyboardNavigation")
        
    def eventFilter(self, obj, event):
        """Filter events to enhance keyboard navigation"""
        # Handle keyboard navigation events
        if event.type() == QEvent.Type.KeyPress:
            # Make Tab navigation more predictable
            if event.key() == Qt.Key.Key_Tab:
                # Standard tab behavior is usually fine
                pass
                
            # Allow Escape to close dialogs
            elif event.key() == Qt.Key.Key_Escape:
                # Find the top level widget
                top_widget = obj
                while top_widget.parent() and not isinstance(top_widget, QDialog):
                    top_widget = top_widget.parent()
                
                if isinstance(top_widget, QDialog):
                    top_widget.reject()
                    return True
                    
            # Allow spacebar to activate buttons when focused
            elif event.key() == Qt.Key.Key_Space:
                if isinstance(obj, QPushButton) and not obj.isCheckable():
                    obj.click()
                    return True
                    
        return super().eventFilter(obj, event)
