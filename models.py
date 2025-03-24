from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

user_site = db.Table('user_site',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('site_id', db.Integer, db.ForeignKey('sites.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    full_name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    reset_token = db.Column(db.String(100))
    reset_token_expiry = db.Column(db.DateTime)
    notification_preferences = db.Column(db.JSON)

    # Define the many-to-many relationship with sites
    sites = db.relationship('Site', secondary=user_site, backref='users')
    role = db.relationship('Role', backref='users')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def has_permission(self, permission):
        if self.is_admin:
            return True
        if self.role:
            return permission in self.role.get_permissions_list()
        return False
    
    def get_notification_preferences(self):
        """Get user notification preferences with defaults if not set"""
        if not self.notification_preferences:
            # Create default preferences
            default_prefs = {
                'enable_email': True,
                'email_frequency': 'weekly',
                'notification_types': ['overdue', 'due_soon']
            }
            # Save these defaults to the database
            self.notification_preferences = default_prefs
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
            return default_prefs
        return self.notification_preferences
