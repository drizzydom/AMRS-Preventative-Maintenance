from models import db
from flask import Flask
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    db.session.execute('ALTER TABLE users ALTER COLUMN username TYPE VARCHAR(256);')
    db.session.execute('ALTER TABLE users ALTER COLUMN email TYPE VARCHAR(256);')
    db.session.commit()
    print("Username and email columns updated to VARCHAR(256)")
