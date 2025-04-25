from app import db
from models import User
from sqlalchemy import text
from db_utils import execute_sql

def add_notification_preferences():
    """Add notification_preferences column to users table"""
    try:
        execute_sql('ALTER TABLE users ADD COLUMN IF NOT EXISTS notification_preferences JSON')
        print("Added notification_preferences column to users table")
        return True
    except Exception as e:
        print(f"Error adding notification_preferences column: {e}")
        return False

def set_default_notification_preferences():
    try:
        # Set default notification preferences for users who don't have them
        users = User.query.all()
        default_preferences = {
            'enable_email': True,
            'email_frequency': 'weekly',
            'notification_types': ['overdue', 'due_soon']
        }
        
        for user in users:
            if not hasattr(user, 'notification_preferences') or user.notification_preferences is None:
                user.notification_preferences = default_preferences
        
        db.session.commit()
        print("Successfully added notification preferences to all users.")
        
    except Exception as e:
        print(f"Error adding notification preferences: {str(e)}")
        db.session.rollback()

if __name__ == '__main__':
    if add_notification_preferences():
        set_default_notification_preferences()
