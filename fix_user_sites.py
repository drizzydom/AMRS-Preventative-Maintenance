
from app import app, db
from models import User, Site, Role, user_site
from sqlalchemy import text

def fix_sites():
    with app.app_context():
        print("=== FIXING USER SITES ===")
        
        # Get all sites
        sites = Site.query.all()
        demo_site = Site.query.filter_by(name='Demo').first()
        if not demo_site:
            print("Error: Demo site not found!")
            return

        users = User.query.all()
        for user in users:
            role_name = user.role.name if user.role else "No Role"
            current_sites = user.sites
            
            print(f"User: {user.username} ({role_name}) - Current Sites: {len(current_sites)}")
            
            if role_name.lower() == 'admin' or (user.role and 'admin.full' in user.role.permissions):
                # Admins get all sites
                if len(current_sites) < len(sites):
                    print(f"  Assigning ALL {len(sites)} sites to admin.")
                    user.sites = sites
                    db.session.add(user)
            else:
                # Non-admins get Demo site if they have none
                if not current_sites:
                    print(f"  Assigning 'Demo' site to user.")
                    user.sites = [demo_site]
                    db.session.add(user)
        
        db.session.commit()
        print("=== DONE ===")

if __name__ == "__main__":
    fix_sites()
