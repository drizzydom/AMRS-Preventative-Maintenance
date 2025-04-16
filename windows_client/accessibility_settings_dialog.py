"""
Dialog for managing accessibility settings
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
                           QComboBox, QSpinBox, QGroupBox, QFormLayout,
                           QPushButton, QDialogButtonBox, QFontComboBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class AccessibilitySettingsDialog(QDialog):
    """Dialog for configuring accessibility settings"""
    
    settings_changed = pyqtSignal(dict)  # Signal emitted when settings are changed
    
    def __init__(self, config_manager=None, accessibility_helper=None, theme_manager=None, parent=None):
        super().__init__(parent)
        
        self.config_manager = config_manager
        self.a11y_helper = accessibility_helper
        self.theme_manager = theme_manager
        
        self.setWindowTitle("Accessibility Settings")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        # Initialize current settings
        self.current_settings = {
            'high_contrast': False,
            'large_text': False,
            'screen_reader_support': False,
            'keyboard_navigation': True,
            'reduced_motion': False,
            'font_family': 'Default',
            'font_size_adjustment': 0
        }
        
        # Load current settings if helper is provided
        if self.a11y_helper:
            self.current_settings = self.a11y_helper.settings
            
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Vision settings group
        vision_group = QGroupBox("Vision Settings")
        vision_layout = QVBoxLayout(vision_group)
        
        # High contrast mode
        self.high_contrast_check = QCheckBox("High Contrast Mode")
        self.high_contrast_check.setChecked(self.current_settings.get('high_contrast', False))
        self.high_contrast_check.setToolTip("Increases contrast for better visibility")
        vision_layout.addWidget(self.high_contrast_check)
        
        # Large text
        self.large_text_check = QCheckBox("Large Text")
        self.large_text_check.setChecked(self.current_settings.get('large_text', False))
        self.large_text_check.setToolTip("Increases text size throughout the application")
        vision_layout.addWidget(self.large_text_check)
        
        # Font settings
        font_layout = QFormLayout()
        
        # Font family
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont(self.current_settings.get('font_family', 'Default')))
        font_layout.addRow("Font:", self.font_combo)
        
        # Font size adjustment
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(-5, 10)
        self.font_size_spin.setValue(self.current_settings.get('font_size_adjustment', 0))
        self.font_size_spin.setPrefix("Adjust by: ")
        self.font_size_spin.setSuffix(" pt")
        font_layout.addRow("Font Size:", self.font_size_spin)
        
        vision_layout.addLayout(font_layout)
        layout.addWidget(vision_group)
        
        # Interaction settings group
        interaction_group = QGroupBox("Interaction Settings")
        interaction_layout = QVBoxLayout(interaction_group)
        
        # Screen reader support
        self.screen_reader_check = QCheckBox("Screen Reader Support")
        self.screen_reader_check.setChecked(self.current_settings.get('screen_reader_support', False))
        self.screen_reader_check.setToolTip("Enhances compatibility with screen readers")
        interaction_layout.addWidget(self.screen_reader_check)
        
        # Keyboard navigation
        self.keyboard_nav_check = QCheckBox("Enhanced Keyboard Navigation")
        self.keyboard_nav_check.setChecked(self.current_settings.get('keyboard_navigation', True))
        self.keyboard_nav_check.setToolTip("Improves keyboard-only navigation")
        interaction_layout.addWidget(self.keyboard_nav_check)
        
        # Reduced motion
        self.reduced_motion_check = QCheckBox("Reduced Motion")
        self.reduced_motion_check.setChecked(self.current_settings.get('reduced_motion', False))
        self.reduced_motion_check.setToolTip("Minimizes animations and motion effects")
        interaction_layout.addWidget(self.reduced_motion_check)
        
        layout.addWidget(interaction_group)
        
        # Theme section
        if self.theme_manager:
            theme_group = QGroupBox("Theme Settings")
            theme_layout = QFormLayout(theme_group)
            
            self.theme_combo = QComboBox()
            themes = self.theme_manager.get_available_themes()
            for name, display_name in themes.items():
                self.theme_combo.addItem(display_name, name)
            
            # Set current theme
            current_theme = self.theme_manager.get_current_theme_name()
            for i in range(self.theme_combo.count()):
                if self.theme_combo.itemData(i) == current_theme:
                    self.theme_combo.setCurrentIndex(i)
                    break
                    
            theme_layout.addRow("Theme:", self.theme_combo)
            layout.addWidget(theme_group)
        
        # Preview section
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        preview_label = QLabel("This is a preview of how text will appear with your selected settings.")
        preview_layout.addWidget(preview_label)
        
        # Sample form elements
        form_layout = QFormLayout()
        
        sample_input = QLineEdit("Sample input text")
        form_layout.addRow("Text Input:", sample_input)
        
        sample_combo = QComboBox()
        sample_combo.addItems(["Option 1", "Option 2", "Option 3"])
        form_layout.addRow("Dropdown:", sample_combo)
        
        sample_check = QCheckBox("Sample checkbox")
        sample_check.setChecked(True)
        form_layout.addRow("Checkbox:", sample_check)
        
        preview_layout.addLayout(form_layout)
        
        # Update preview when settings change
        self.high_contrast_check.toggled.connect(lambda: self._update_preview(preview_group))
        self.large_text_check.toggled.connect(lambda: self._update_preview(preview_group))
        self.font_combo.currentFontChanged.connect(lambda: self._update_preview(preview_group))
        self.font_size_spin.valueChanged.connect(lambda: self._update_preview(preview_group))
        
        layout.addWidget(preview_group)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | 
                                    QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.save_settings)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
        
        # Initial preview update
        self._update_preview(preview_group)
    
    def _update_preview(self, preview_group):
        """Update the preview with current settings"""
        try:
            # Create sample settings
            sample_settings = {
                'high_contrast': self.high_contrast_check.isChecked(),
                'large_text': self.large_text_check.isChecked(),
                'font_family': self.font_combo.currentFont().family(),
                'font_size_adjustment': self.font_size_spin.value()
            }
            
            # Apply to preview
            font = preview_group.font()
            
            # Font family
            if sample_settings['font_family'] != 'Default':
                font.setFamily(sample_settings['font_family'])
                
            # Font size
            size_adjustment = 2 if sample_settings['large_text'] else 0
            size_adjustment += sample_settings['font_size_adjustment']
            
            if size_adjustment != 0:
                font.setPointSize(font.pointSize() + size_adjustment)
                
            preview_group.setFont(font)
            
            # High contrast
            if sample_settings['high_contrast']:
                preview_group.setStyleSheet("""
                    QGroupBox {
                        color: white;
                        background-color: black;
                        border: 2px solid white;
                        padding: 15px;
                    }
                    QLabel {
                        color: white;
                    }
                    QLineEdit {
                        color: white;
                        background-color: black;
                        border: 1px solid white;
                    }
                    QComboBox {
                        color: white;
                        background-color: black;
                        border: 1px solid white;
                    }
                    QCheckBox {
                        color: white;
                    }
                """)
            else:
                preview_group.setStyleSheet("")
                
        except Exception as e:
            print(f"Error updating preview: {e}")
    
    def save_settings(self):
        """Save accessibility settings"""
        # Update settings
        settings = {
            'high_contrast': self.high_contrast_check.isChecked(),
            'large_text': self.large_text_check.isChecked(),
            'screen_reader_support': self.screen_reader_check.isChecked(),
            'keyboard_navigation': self.keyboard_nav_check.isChecked(),
            'reduced_motion': self.reduced_motion_check.isChecked(),
            'font_family': self.font_combo.currentFont().family(),
            'font_size_adjustment': self.font_size_spin.value()
        }
        
        # Update config
        if self.config_manager:
            self.config_manager.set('accessibility', settings)
            
        # Update accessibility helper
        if self.a11y_helper:
            for key, value in settings.items():
                self.a11y_helper.set_setting(key, value)
                
        # Update theme if theme manager is available
        if self.theme_manager and hasattr(self, 'theme_combo'):
            theme_name = self.theme_combo.currentData()
            if theme_name:
                self.theme_manager.set_theme(theme_name)
                
        # Emit settings changed signal
        self.settings_changed.emit(settings)
        
        # Accept dialog
        self.accept()
