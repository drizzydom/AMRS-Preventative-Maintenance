
"""
Migration script to add app_settings table for admin-configurable settings.
"""
from models import db
from sqlalchemy import Column, String, Table, MetaData

def upgrade():
    # Use SQLAlchemy MetaData to check and create the tables if missing
    engine = db.engine
    metadata = MetaData(bind=engine)
    metadata.reflect()
    # Create app_settings table if missing
    if 'app_settings' not in metadata.tables:
        app_settings = Table(
            'app_settings', metadata,
            Column('key', String(64), primary_key=True),
            Column('value', String(255), nullable=True)
        )
        app_settings.create(engine)
        print('[MIGRATION] Created app_settings table.')
    else:
        print('[MIGRATION] app_settings table already exists.')

    # Create offline_security_events table if missing
    if 'offline_security_events' not in metadata.tables:
        offline_security_events = Table(
            'offline_security_events', metadata,
            Column('id', db.Integer, primary_key=True),
            Column('timestamp', db.DateTime, nullable=False),
            Column('event_type', db.String(64), nullable=False),
            Column('user_id', db.Integer, nullable=True),
            Column('username', db.String(255), nullable=True),
            Column('ip_address', db.String(64), nullable=True),
            Column('location', db.String(255), nullable=True),
            Column('details', db.Text, nullable=True),
            Column('is_critical', db.Boolean, default=False),
            Column('synced', db.Boolean, default=False, index=True)
        )
        offline_security_events.create(engine)
        print('[MIGRATION] Created offline_security_events table.')
    else:
        print('[MIGRATION] offline_security_events table already exists.')

def downgrade():
    engine = db.engine
    metadata = MetaData(bind=engine)
    metadata.reflect()
    # Drop offline_security_events table if exists
    if 'offline_security_events' in metadata.tables:
        offline_security_events = metadata.tables['offline_security_events']
        offline_security_events.drop(engine)
        print('[MIGRATION] Dropped offline_security_events table.')
    else:
        print('[MIGRATION] offline_security_events table does not exist.')
    # Drop app_settings table if exists
    if 'app_settings' in metadata.tables:
        app_settings = metadata.tables['app_settings']
        app_settings.drop(engine)
        print('[MIGRATION] Dropped app_settings table.')
    else:
        print('[MIGRATION] app_settings table does not exist.')
