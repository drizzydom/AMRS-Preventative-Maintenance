"""
Language selection dialog for the application
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
                           QListWidgetItem, QPushButton, QDialogButtonBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QFont

class LanguageDialog(QDialog):
    """Dialog for selecting application language"""
    
    language_changed = pyqtSignal(str)  # Signal emitted when language is changed
    
    def __init__(self, localization_manager, parent=None):
        super().__init__(parent)
        self.localization = localization_manager
        self.selected_language = self.localization.current_language
        
        self.setWindowTitle(self.localization.get_text("settings.language", "Language"))
        self.setMinimumWidth(350)
        self.setMinimumHeight(300)
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Title label
        title_label = QLabel(self.localization.get_text("settings.language", "Language"))
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Instructions label
        instructions = QLabel(self.localization.get_text(
            "settings.language_instructions", 
            "Select your preferred language:"
        ))
        layout.addWidget(instructions)
        
        # Language list
        self.language_list = QListWidget()
        self.language_list.setAlternatingRowColors(True)
        layout.addWidget(self.language_list)
        
        # Populate language list
        self._populate_language_list()
        
        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # Get localized button text
        ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        cancel_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        
        ok_button.setText(self.localization.get_text("general.ok", "OK"))
        cancel_button.setText(self.localization.get_text("general.cancel", "Cancel"))
        
        layout.addWidget(button_box)
    
    def _populate_language_list(self):
        """Populate the list of available languages"""
        self.language_list.clear()
        
        for language in self.localization.available_languages:
            item = QListWidgetItem(language["name"])
            item.setData(Qt.ItemDataRole.UserRole, language["code"])
            
            # Set the current language as selected
            if language["code"] == self.localization.current_language:
                self.language_list.setCurrentItem(item)
            
            self.language_list.addItem(item)
        
        # Connect item selection
        self.language_list.itemSelectionChanged.connect(self._on_selection_changed)
    
    def _on_selection_changed(self):
        """Handle language selection change"""
        selected_items = self.language_list.selectedItems()
        if selected_items:
            self.selected_language = selected_items[0].data(Qt.ItemDataRole.UserRole)
    
    def accept(self):
        """Handle dialog acceptance"""
        # Change language if different from current
        if self.selected_language != self.localization.current_language:
            success = self.localization.change_language(self.selected_language)
            if success:
                self.language_changed.emit(self.selected_language)
            
        super().accept()
