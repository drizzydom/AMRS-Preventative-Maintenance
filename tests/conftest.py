import os
import pytest
from app import app as flask_app, db as _db, ensure_db_schema
from models import User, Role, Site, Machine, Part, MaintenanceRecord
from flask import template_rendered
from contextlib import contextmanager

@pytest.fixture(scope='session')
def app():
    # Always use in-memory SQLite for tests
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False
    with flask_app.app_context():
        _db.create_all()
        ensure_db_schema()  # Run migrations/auto-migrations
        yield flask_app
        _db.drop_all()

@pytest.fixture(scope='function')
def db(app):
    with app.app_context():
        yield _db
        _db.session.rollback()

@pytest.fixture(scope='function')
def client(app, db):
    return app.test_client()

@pytest.fixture
def login_admin(client, db):
    def do_login():
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin_role = Role.query.filter_by(name='admin').first()
            if not admin_role:
                admin_role = Role(name='admin', description='Administrator', permissions='admin.full')
                db.session.add(admin_role)
                db.session.commit()
            admin = User(username='admin', email='admin@example.com', password_hash='pbkdf2:sha256:dummy', role=admin_role)
            db.session.add(admin)
            db.session.commit()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin.id)
            sess['_fresh'] = True
    return do_login

@pytest.fixture
def create_part(db):
    def do_create():
        site = Site(name='Test Site')
        db.session.add(site)
        db.session.commit()
        machine = Machine(name='Test Machine', site_id=site.id)
        db.session.add(machine)
        db.session.commit()
        part = Part(name='Test Part', machine_id=machine.id)
        db.session.add(part)
        db.session.commit()
        return part
    return do_create

@pytest.fixture
def setup_test_data(db):
    # Create two sites
    site1 = Site(name='Site 1')
    site2 = Site(name='Site 2')
    db.session.add_all([site1, site2])
    db.session.commit()
    # Create a machine assigned to site1
    machine = Machine(name='Machine 1', site_id=site1.id)
    db.session.add(machine)
    db.session.commit()
    # Assign admin user to both sites
    admin = User.query.filter_by(username='admin').first()
    if admin:
        admin.sites = [site1, site2]
        db.session.commit()
    return {'site1': site1, 'site2': site2, 'machine': machine, 'admin': admin}
