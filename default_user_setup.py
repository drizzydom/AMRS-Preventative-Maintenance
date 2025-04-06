#!/usr/bin/env python3
"""
Utility script to create a default admin user.
Run this script after deployment if you need to create an admin user manually.
"""

import os
import sys
import secrets
import string
from flask import Flask
from sqlalchemy import text

# Setup basic Flask app for database access
app = Flask(__name__)

# Configure database based on environment
if os.environ.get('RENDER'):
    db_path = os.path.join('/var/data', 'maintenance.db')
else:
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'maintenance.db')

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Import after app is created
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)

# Import or recreate your models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    email = db.Column(db.String(100))
    full_name = db.Column(db.String(100))
    
    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    permissions = db.Column(db.String(500), default="view")
    users = db.relationship('User', backref='role', lazy=True)

def create_admin_user():
    """Create an administrator user"""
    with app.app_context():
        # Check if any users already exist
        user_count = User.query.count()
        if user_count > 0:
            print(f"[INFO] Found {user_count} existing users. Not creating a default admin.")
            return
        
        # Get or create admin role
        admin_role = Role.query.filter_by(name="Administrator").first()
        if not admin_role:
            print("[INFO] Creating Administrator role...")
            admin_role = Role(
                name="Administrator",
                description="Full system access",
                permissions="admin.full"  # Full administrator access
            )
            db.session.add(admin_role)
            db.session.commit()
        
        # Generate a secure random password
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for _ in range(12))
        
        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@example.com",
            full_name="System Administrator",
            is_admin=True,
            role_id=admin_role.id
        )
        admin_user.set_password(password)
        
        db.session.add(admin_user)
        db.session.commit()
        
        print("\n========================================")
        print("Created default admin user:")
        print(f"Username: admin")
        print(f"Password: {password}")
        print("IMPORTANT: Please change this password immediately after first login!")
        print("========================================\n")

if __name__ == "__main__":
    try:
        create_admin_user()
    except Exception as e:
        print(f"[ERROR] Failed to create admin user: {str(e)}")
