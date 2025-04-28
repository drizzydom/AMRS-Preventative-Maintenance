import os
import platform
from sqlalchemy import text

# Helper to check if using SQLite
from sqlalchemy.engine.url import make_url

def is_sqlite_db():
    uri = app.config.get('SQLALCHEMY_DATABASE_URI')
    if not uri:
        return False
    return make_url(uri).get_backend_name() == 'sqlite'

# --- Fix expand_user_fields.py to skip ALTER for SQLite and ensure db path exists ---
import os
from models import db
from flask import Flask
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    # Ensure SQLite db directory exists if using SQLite
    if is_sqlite_db():
        db_path = make_url(app.config['SQLALCHEMY_DATABASE_URI']).database
        if db_path and not os.path.isabs(db_path):
            db_path = os.path.abspath(db_path)
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        print(f"[MIGRATION] SQLite DB path: {db_path}")
    # Only run ALTER for non-SQLite
    if not is_sqlite_db():
        db.session.execute(text('ALTER TABLE users ALTER COLUMN username TYPE VARCHAR(256);'))
        db.session.execute(text('ALTER TABLE users ALTER COLUMN email TYPE VARCHAR(256);'))
        db.session.commit()
        print("Username and email columns updated to VARCHAR(256)")
    else:
        print("[MIGRATION] Skipping ALTER TABLE for SQLite (not supported). Ensure your model uses db.Text for username/email.")
