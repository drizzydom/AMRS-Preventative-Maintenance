#!/bin/bash

echo "Fixing circular import directly inside the container..."

docker exec -it amrs-maintenance-tracker bash -c "
echo 'Checking models.py for circular import...'
grep -n 'from app.models import' /app/app/models.py
echo 'Fixing models.py...'
cat > /app/app/models.py << 'EOL'
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# Initialize database object - no circular imports
db = SQLAlchemy()

# Models defined below
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    active = db.Column(db.Boolean, nullable=False, default=True)

    def __repr__(self):
        return f\"<User {self.username}>\"
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
EOL

echo 'Restarting gunicorn inside container...'
pkill gunicorn
gunicorn --bind 0.0.0.0:9000 --workers 1 --threads 8 app_standalone:app &
echo 'Done!'
"
