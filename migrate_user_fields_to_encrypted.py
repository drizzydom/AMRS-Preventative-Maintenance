import os
from models import db, User
from flask import Flask
from config import Config

# Set up Flask app and DB context
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    users = User.query.all()
    updated = 0
    skipped = 0
    for user in users:
        # Only migrate if username and email are not None
        if user.username and user.email:
            user.username = user.username  # triggers encryption
            user.email = user.email
            updated += 1
        else:
            print(f"[MIGRATION] Skipped user id={user.id} due to missing username or email.")
            skipped += 1
    db.session.commit()
    print(f"[MIGRATION] Encrypted username and email for {updated} users. Skipped {skipped} users with missing data.")
