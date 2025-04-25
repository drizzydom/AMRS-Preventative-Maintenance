"""
Notification manager for displaying system notifications and alerts
"""
import os
import sys
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QWidget
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, Qt

# Try to import platform-specific notification libraries
try:
    from plyer import notification as system_notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False

class NotificationManager(QObject):
    """
    Manages system notifications, in-app alerts, and notification history
    """
    
    # Signals
    notification_received = pyqtSignal(dict)  # Notification data
    notification_clicked = pyqtSignal(str, dict)  # Category, notification data
    
    def __init__(self, config_manager=None, tray_icon=None, max_history=100):
        """
        Initialize the notification manager
        
        Args:
            config_manager: Application configuration manager
            tray_icon: System tray icon instance or None
            max_history: Maximum number of notifications to keep in history
        """
        super().__init__()
        self.config = config_manager
        self.tray_icon = tray_icon
        self.max_history = max_history
        
        self.logger = logging.getLogger("NotificationManager")
        
        # Notification history
        self.notifications = []
        
        # Notification counters by category
        self.notification_counts = {}
        
        # Load notification history if config manager provided
        self._load_history()
    
    def _load_history(self):
        """Load notification history from config"""
        if not self.config:
            return
            
        try:
            history = self.config.get('notification_history', [])
            if isinstance(history, list) and len(history) > 0:
                self.notifications = history[:self.max_history]
                
                # Update counters
                self._update_notification_counters()
                
        except Exception as e:
            self.logger.error(f"Error loading notification history: {e}")
    
    def _save_history(self):
        """Save notification history to config"""
        if not self.config:
            return
            
        try:
            self.config.set('notification_history', self.notifications[:self.max_history])
        except Exception as e:
            self.logger.error(f"Error saving notification history: {e}")
    
    def _update_notification_counters(self):
        """Update notification counters by category"""
        self.notification_counts = {}
        
        for notification in self.notifications:
            category = notification.get('category', 'general')
            if not notification.get('read', False):
                self.notification_counts[category] = self.notification_counts.get(category, 0) + 1
    
    def send_notification(self, title, message, category='general', data=None, icon=None, notify_system=True, timeout=10000):
        """
        Send a notification
        
        Args:
            title: Notification title
            message: Notification message
            category: Notification category (e.g., 'maintenance', 'sync')
            data: Optional data associated with the notification
            icon: Optional icon path or QIcon
            notify_system: Whether to show a system notification
            timeout: Notification timeout in milliseconds
            
        Returns:
            Notification ID
        """
        try:
            # Generate notification ID
            notification_id = f"{category}_{datetime.now().isoformat()}"
            
            # Create notification data
            notification = {
                'id': notification_id,
                'title': title,
                'message': message,
                'category': category,
                'timestamp': datetime.now().isoformat(),
                'read': False,
                'data': data or {}
            }
            
            # Add to history
            self.notifications.insert(0, notification)
            
            # Trim history if needed
            if len(self.notifications) > self.max_history:
                self.notifications = self.notifications[:self.max_history]
                
            # Save history
            self._save_history()
            
            # Update counters
            self._update_notification_counters()
            
            # Emit signal
            self.notification_received.emit(notification)
            
            # Show system notification if requested
            if notify_system:
                self._show_system_notification(notification, icon, timeout)
                
            return notification_id
            
        except Exception as e:
            self.logger.error(f"Error sending notification: {e}", exc_info=True)
            return None
    
    def _show_system_notification(self, notification, icon=None, timeout=10000):
        """Show a system notification"""
        try:
            # Use system tray if available
            if self.tray_icon and isinstance(self.tray_icon, QSystemTrayIcon) and self.tray_icon.isVisible():
                if icon is None:
                    # Use default icon
                    self.tray_icon.showMessage(
                        notification['title'],
                        notification['message'],
                        QSystemTrayIcon.MessageIcon.Information,
                        timeout
                    )
                else:
                    # Use provided icon
                    if isinstance(icon, str) and os.path.exists(icon):
                        icon = QIcon(icon)
                        
                    if isinstance(icon, QIcon):
                        self.tray_icon.showMessage(
                            notification['title'],
                            notification['message'],
                            icon,
                            timeout
                        )
                    else:
                        # Fall back to default
                        self.tray_icon.showMessage(
                            notification['title'],
                            notification['message'],
                            QSystemTrayIcon.MessageIcon.Information,
                            timeout
                        )
                return
                
            # Fall back to plyer if available
            if PLYER_AVAILABLE:
                system_notification.notify(
                    title=notification['title'],
                    message=notification['message'],
                    app_name="AMRS Maintenance Tracker",
                    timeout=timeout // 1000  # Convert to seconds
                )
                return
                
            # Last resort: log the notification
            self.logger.info(
                f"NOTIFICATION: {notification['title']} - {notification['message']}"
            )
            
        except Exception as e:
            self.logger.error(f"Error showing system notification: {e}", exc_info=True)
    
    def mark_notification_read(self, notification_id):
        """
        Mark a notification as read
        
        Args:
            notification_id: ID of the notification to mark as read
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Find notification
            for notification in self.notifications:
                if notification.get('id') == notification_id:
                    notification['read'] = True
                    
                    # Save history
                    self._save_history()
                    
                    # Update counters
                    self._update_notification_counters()
                    
                    return True
                    
            return False
            
        except Exception as e:
            self.logger.error(f"Error marking notification as read: {e}")
            return False
    
    def mark_all_read(self, category=None):
        """
        Mark all notifications as read, optionally filtered by category
        
        Args:
            category: Optional category to filter by
            
        Returns:
            Number of notifications marked as read
        """
        try:
            count = 0
            
            for notification in self.notifications:
                if category is None or notification.get('category') == category:
                    if not notification.get('read', False):
                        notification['read'] = True
                        count += 1
                        
            if count > 0:
                # Save history
                self._save_history()
                
                # Update counters
                self._update_notification_counters()
                
            return count
            
        except Exception as e:
            self.logger.error(f"Error marking all notifications as read: {e}")
            return 0
    
    def get_notifications(self, category=None, max_count=None, include_read=False):
        """
        Get notifications, optionally filtered by category
        
        Args:
            category: Optional category to filter by
            max_count: Maximum number of notifications to return
            include_read: Whether to include read notifications
            
        Returns:
            List of notification dictionaries
        """
        try:
            result = []
            
            for notification in self.notifications:
                if category is None or notification.get('category') == category:
                    if include_read or not notification.get('read', False):
                        result.append(notification)
                        
                        if max_count is not None and len(result) >= max_count:
                            break
                            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting notifications: {e}")
            return []
    
    def get_unread_count(self, category=None):
        """
        Get count of unread notifications
        
        Args:
            category: Optional category to filter by
            
        Returns:
            Count of unread notifications
        """
        if category:
            return self.notification_counts.get(category, 0)
            
        return sum(self.notification_counts.values())
    
    def clear_notifications(self, category=None, older_than_days=None):
        """
        Clear notifications, optionally filtered by category and age
        
        Args:
            category: Optional category to filter by
            older_than_days: Optional age filter in days
            
        Returns:
            Number of notifications cleared
        """
        try:
            if not self.notifications:
                return 0
                
            initial_count = len(self.notifications)
            
            # Filter notifications to keep
            if category or older_than_days:
                cutoff_date = None
                if older_than_days:
                    cutoff_date = datetime.now() - timedelta(days=older_than_days)
                    
                keep_notifications = []
                for notification in self.notifications:
                    # Check category if specified
                    if category and notification.get('category') != category:
                        keep_notifications.append(notification)
                        continue
                        
                    # Check age if specified
                    if cutoff_date:
                        try:
                            timestamp = datetime.fromisoformat(notification.get('timestamp'))
                            if timestamp > cutoff_date:
                                keep_notifications.append(notification)
                                continue
                        except (ValueError, TypeError):
                            # If timestamp parsing fails, keep the notification
                            keep_notifications.append(notification)
                            continue
                
                self.notifications = keep_notifications
            else:
                # Clear all
                self.notifications = []
                
            # Calculate cleared count
            cleared_count = initial_count - len(self.notifications)
            
            if cleared_count > 0:
                # Save history
                self._save_history()
                
                # Update counters
                self._update_notification_counters()
                
            return cleared_count
            
        except Exception as e:
            self.logger.error(f"Error clearing notifications: {e}")
            return 0
