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
    for user in users:
        # Re-assign to trigger encryption property setters
        user.username = user.username  # This will encrypt and store in _username
        user.email = user.email        # This will encrypt and store in _email
        updated += 1
    db.session.commit()
    print(f"[MIGRATION] Encrypted username and email for {updated} users.")
