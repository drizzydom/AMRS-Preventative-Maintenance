from app import db
from models import User
from sqlalchemy import text

def add_notification_preferences():
    try:
        # Add notification_preferences column if it doesn't exist
        with db.engine.connect() as conn:
            conn.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS notification_preferences JSON'))
            conn.commit()
            
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
    add_notification_preferences()
