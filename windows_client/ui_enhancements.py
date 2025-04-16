"""
UI enhancement utilities for a polished look and feel
"""
import os
import time
import logging
from PyQt6.QtWidgets import (QWidget, QLabel, QTableView, QPushButton, QComboBox,
                          QLineEdit, QProgressBar, QTabWidget, QLayout)
from PyQt6.QtGui import QIcon, QPainter, QPalette, QColor, QPen, QBrush, QFontMetrics
from PyQt6.QtCore import Qt, QPoint, QSize, QObject, QEvent, QTimer, QPropertyAnimation

class UIEnhancer:
    """
    Provides UI enhancement utilities for a polished look and feel
    """
    
    def __init__(self, theme_manager=None):
        """
        Initialize UI enhancer
        
        Args:
            theme_manager: Optional theme manager for coordinated styling
        """
        self.theme_manager = theme_manager
        self.logger = logging.getLogger("UIEnhancer")
        
        # Options
        self.options = {
            'enable_animations': True,
            'button_hover_effect': True,
            'use_rounded_corners': True,
            'enable_shadows': True,
            'progress_animation': True,
            'modern_controls': True,
            'consistent_icons': True,
            'smooth_transitions': True,
            'animation_scale': 1.0
        }
        
        # Track enhanced widgets for cleanup
        self.enhanced_widgets = {}
        
        # Load icons if needed
        self.icons = {}
    
    def enhance_widget(self, widget, options=None):
        """
        Apply enhancements to a widget
        
        Args:
            widget: Widget to enhance
            options: Optional dict of specific options for this widget
            
        Returns:
            True if enhanced, False otherwise
        """
        if not widget:
            return False
            
        # Apply specific options, falling back to defaults
        active_options = self.options.copy()
        if options:
            active_options.update(options)
            
        # Install event filter for hover effects
        if active_options['button_hover_effect'] or active_options['enable_animations']:
            event_filter = HoverEventFilter(widget, active_options)
            widget.installEventFilter(event_filter)
            
            # Track for cleanup
            self.enhanced_widgets[widget] = event_filter
        
        # Apply widget-specific enhancements
        try:
            if isinstance(widget, QPushButton):
                self._enhance_button(widget, active_options)
                
            elif isinstance(widget, QTableView):
                self._enhance_table(widget, active_options)
                
            elif isinstance(widget, QTabWidget):
                self._enhance_tab_widget(widget, active_options)
                
            elif isinstance(widget, QProgressBar):
                self._enhance_progress_bar(widget, active_options)
                
            # Apply consistent icons if requested
            if active_options['consistent_icons'] and hasattr(widget, 'icon') and hasattr(widget, 'objectName'):
                self._apply_consistent_icon(widget)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error enhancing widget: {e}")
            return False
    
    def _enhance_button(self, button, options):
        """Apply enhancements to buttons"""
        # Set rounded corners via stylesheet
        if options['use_rounded_corners']:
            radius = "4px"
            
            # Check if part of a button group
            if button.parent() and hasattr(button.parent(), 'findChildren'):
                siblings = button.parent().findChildren(QPushButton)
                if len(siblings) > 1:
                    # Buttons in a group should have different corner radii
                    # based on position
                    pass  # Advanced styling would go here
            
            current_ss = button.styleSheet()
            if "border-radius" not in current_ss:
                button.setStyleSheet(current_ss + f"QPushButton {{ border-radius: {radius}; }}")
        
        # Add shadow if enabled
        if options['enable_shadows'] and hasattr(button, 'setGraphicsEffect'):
            from PyQt6.QtWidgets import QGraphicsDropShadowEffect
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(4)
            shadow.setOffset(0, 2)
            shadow.setColor(QColor(0, 0, 0, 50))
            button.setGraphicsEffect(shadow)
    
    def _enhance_table(self, table, options):
        """Apply enhancements to table views"""
        # Set alternating row colors
        table.setAlternatingRowColors(True)
        
        # Set modern selection style
        if options['modern_controls']:
            table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
            table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
            
            # Apply stylesheet for modern row selection
            current_ss = table.styleSheet()
            if "QTableView::item:selected" not in current_ss:
                highlight_color = "#007bff"
                
                # If theme manager is available, use theme color
                if self.theme_manager:
                    theme_colors = self.theme_manager.get_theme_colors()
                    highlight_color = theme_colors.get('highlight', highlight_color)
                    
                table.setStyleSheet(current_ss + f"""
                    QTableView::item:selected {{
                        background-color: {highlight_color};
                        color: white;
                    }}
                """)
    
    def _enhance_tab_widget(self, tab_widget, options):
        """Apply enhancements to tab widgets"""
        if options['modern_controls']:
            # Apply modern tab styling
            current_ss = tab_widget.styleSheet()
            
            if "QTabBar::tab" not in current_ss:
                tab_widget.setStyleSheet(current_ss + """
                    QTabBar::tab {
                        padding: 8px 16px;
                        margin-right: 2px;
                    }
                    
                    QTabBar::tab:selected {
                        border-bottom: 2px solid palette(highlight);
                    }
                """)
        
        # Add smooth transitions if enabled
        if options['smooth_transitions'] and options['enable_animations']:
            # Subclass the tab widget to add transition animations
            # Implementation would go here
            pass
    
    def _enhance_progress_bar(self, progress_bar, options):
        """Apply enhancements to progress bars"""
        # Set modern style
        if options['modern_controls']:
            progress_bar.setTextVisible(True)
            progress_bar.setFixedHeight(10)
            
            # Apply rounded corners
            if options['use_rounded_corners']:
                progress_bar.setStyleSheet("""
                    QProgressBar {
                        border-radius: 5px;
                        background-color: #f0f0f0;
                        text-align: center;
                    }
                    
                    QProgressBar::chunk {
                        border-radius: 5px;
                        background-color: palette(highlight);
                    }
                """)
                
        # Add progress animation if enabled
        if options['progress_animation'] and options['enable_animations']:
            # Implementation would animate the progress changes
            pass
    
    def _apply_consistent_icon(self, widget):
        """Apply consistent icon based on widget's objectName"""
        if not hasattr(widget, 'setIcon'):
            return
            
        name = widget.objectName().lower()
        icon_name = None
        
        # Map common names to icon names
        if 'save' in name:
            icon_name = "save"
        elif 'add' in name or 'new' in name or 'create' in name:
            icon_name = "add"
        elif 'delete' in name or 'remove' in name:
            icon_name = "delete"
        elif 'edit' in name:
            icon_name = "edit"
        elif 'sync' in name:
            icon_name = "sync"
        elif 'search' in name:
            icon_name = "search"
        elif 'settings' in name or 'config' in name:
            icon_name = "settings"
        elif 'help' in name:
            icon_name = "help"
        elif 'refresh' in name or 'reload' in name:
            icon_name = "refresh"
        
        # Set icon if mapped
        if icon_name:
            icon = self.get_icon(icon_name)
            if icon:
                widget.setIcon(icon)
    
    def get_icon(self, name):
        """
        Get an icon by name
        
        Args:
            name: Icon name
            
        Returns:
            QIcon instance or None
        """
        if name in self.icons:
            return self.icons[name]
            
        # Try to load icon
        icon_path = os.path.join(os.path.dirname(__file__), 'resources', 'icons', f"{name}.png")
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            self.icons[name] = icon
            return icon
            
        return None
    
    def enhance_layout_spacing(self, layout):
        """
        Apply consistent spacing to layout
        
        Args:
            layout: Layout to enhance
        """
        if not isinstance(layout, QLayout):
            return
            
        # Set consistent margins and spacing
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Apply to child layouts recursively
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.layout():
                self.enhance_layout_spacing(item.layout())
    
    def enable_ripple_effect(self, widget):
        """
        Enable ripple effect on button click
        
        Args:
            widget: Widget to add ripple effect to
        """
        if not self.options['enable_animations']:
            return
            
        # Create and install ripple effect filter
        ripple_filter = RippleEffect(widget)
        widget.installEventFilter(ripple_filter)
        
        # Track for cleanup
        self.enhanced_widgets[widget] = ripple_filter
    
    def cleanup_enhancements(self):
        """Remove enhancements from all tracked widgets"""
        for widget, effect in list(self.enhanced_widgets.items()):
            try:
                if widget:
                    widget.removeEventFilter(effect)
            except:
                pass
                
        self.enhanced_widgets.clear()

class HoverEventFilter(QObject):
    """Event filter for button hover effects"""
    
    def __init__(self, parent, options):
        super().__init__(parent)
        self.options = options
        self.is_hovering = False
        self.animation = None
        
    def eventFilter(self, obj, event):
        if not self.options['enable_animations'] or not self.options['button_hover_effect']:
            return False
            
        if isinstance(obj, QPushButton):
            if event.type() == QEvent.Type.Enter and not self.is_hovering:
                self.is_hovering = True
                self._start_hover_animation(obj, True)
                return True
                
            elif event.type() == QEvent.Type.Leave and self.is_hovering:
                self.is_hovering = False
                self._start_hover_animation(obj, False)
                return True
                
        return False
    
    def _start_hover_animation(self, button, hovering):
        """Start hover animation"""
        if self.animation and self.animation.state() == QPropertyAnimation.State.Running:
            self.animation.stop()
            
        # Create new animation
        self.animation = QPropertyAnimation(button, b"iconSize")
        
        # Calculate icon sizes
        current_size = button.iconSize()
        original_size = QSize(16, 16)  # Default size
        hover_size = QSize(18, 18)     # Slightly larger
        
        if hovering:
            self.animation.setStartValue(current_size)
            self.animation.setEndValue(hover_size)
        else:
            self.animation.setStartValue(current_size)
            self.animation.setEndValue(original_size)
            
        # Configure animation
        duration = int(300 * self.options['animation_scale'])
        self.animation.setDuration(duration)
        self.animation.setEasingCurve(Qt.CurveShape.OutCubic)
        
        # Start animation
        self.animation.start()

class RippleEffect(QObject):
    """Event filter that draws a ripple effect on buttons"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.ripple_opacity = 0
        self.ripple_pos = QPoint()
        self.ripple_radius = 0
        self.max_radius = 0
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Paint and self.ripple_opacity > 0:
            self._draw_ripple(obj)
            
        elif event.type() == QEvent.Type.MouseButtonPress:
            self._start_ripple(obj, event.position().toPoint())
            
        return False
    
    def _start_ripple(self, widget, pos):
        """Start ripple animation at pos"""
        self.ripple_pos = pos
        self.ripple_opacity = 1.0
        
        # Calculate maximum radius based on widget size
        widget_rect = widget.rect()
        self.max_radius = max(widget_rect.width(), widget_rect.height()) * 0.7
        self.ripple_radius = 0
        
        # Start animation
        self.animation_timer.start(16)  # ~60fps
        
    def update_animation(self):
        """Update ripple animation"""
        parent = self.parent()
        
        # Increase radius
        self.ripple_radius += 5
        
        # Decrease opacity
        self.ripple_opacity -= 0.05
        
        # Stop animation when complete
        if self.ripple_opacity <= 0:
            self.animation_timer.stop()
            self.ripple_opacity = 0
            
        # Trigger repaint
        if parent:
            parent.update()
    
    def _draw_ripple(self, widget):
        """Draw ripple effect on widget"""
        painter = QPainter(widget)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Set up the painter
        painter.setPen(Qt.PenStyle.NoPen)
        highlight_color = widget.palette().color(QPalette.ColorRole.Highlight)
        ripple_color = QColor(highlight_color)
        ripple_color.setAlphaF(self.ripple_opacity * 0.3)  # Semi-transparent
        
        painter.setBrush(ripple_color)
        
        # Draw ripple circle
        painter.drawEllipse(self.ripple_pos, 
                           int(self.ripple_radius), 
                           int(self.ripple_radius))
