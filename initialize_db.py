import os
import sys
from app import app, db, User, Role, Site
import secrets

def initialize_database():
    """
    Initialize the database by creating all tables and adding a default admin user
    if no users exist.
    """
    print("Initializing database...")
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created.")

        # Check if any users exist
        user_count = User.query.count()
        if user_count == 0:
            print("No users found. Creating admin user...")
            
            # Create admin role if it doesn't exist
            admin_role = Role.query.filter_by(name="Administrator").first()
            if not admin_role:
                admin_role = Role(name="Administrator", 
                                 description="Full system access",
                                 permissions="admin.full")
                db.session.add(admin_role)
                db.session.commit()
                print("Created Administrator role.")
            
            # Generate a secure random password
            password = secrets.token_urlsafe(8)  # 8-character random password
            
            # Create admin user
            admin_user = User(username="admin", 
                             email="admin@example.com", 
                             full_name="System Administrator",
                             is_admin=True,
                             role_id=admin_role.id if admin_role else None)
            admin_user.set_password(password)
            db.session.add(admin_user)
            db.session.commit()
            
            print(f"""
            ----------------------------------------------------------------
            Admin user created successfully!
            
            Username: admin
            Password: {password}
            
            Please log in and change this password immediately.
            ----------------------------------------------------------------
            """)
        else:
            print(f"Database already contains {user_count} user(s). Skipping admin creation.")

if __name__ == "__main__":
    initialize_database()
    print("Database initialization complete.")
