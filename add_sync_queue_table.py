"""
Migration script to add a sync_queue table for offline/online sync tracking.
"""
from models import db
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app import app

class SyncQueue(db.Model):
    __tablename__ = 'sync_queue'
    id = Column(Integer, primary_key=True)
    table_name = Column(String(64), nullable=False)
    record_id = Column(String(64), nullable=False)
    operation = Column(String(16), nullable=False)  # 'insert', 'update', 'delete'
    payload = Column(Text, nullable=False)  # JSON string of the record data
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(16), default='pending')  # 'pending', 'synced', 'error'
    error_message = Column(Text, default=None)

def upgrade():
    with app.app_context():
        SyncQueue.__table__.create(db.engine, checkfirst=True)

def downgrade():
    with app.app_context():
        SyncQueue.__table__.drop(db.engine, checkfirst=True)

if __name__ == '__main__':
    upgrade()
    print('sync_queue table created.')
