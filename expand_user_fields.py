import os
from models import db
from flask import Flask
from config import Config
from sqlalchemy import text

# Set the Fernet key for migration context
os.environ['USER_FIELD_ENCRYPTION_KEY'] = '_CY9_bO9vrX2CEUNmFqD1ETx-CluNejbidXFGMYapis='

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    db.session.execute(text('ALTER TABLE users ALTER COLUMN username TYPE VARCHAR(256);'))
    db.session.execute(text('ALTER TABLE users ALTER COLUMN email TYPE VARCHAR(256);'))
    db.session.commit()
    print("Username and email columns updated to VARCHAR(256)")
