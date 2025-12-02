import os
import base64
from flask import Flask
from flask_login import LoginManager
from sqlalchemy.pool import StaticPool

from models import db, User, Role, Site, Machine, Part, AuditTask
from api_v1 import api_v1
from remember_session_manager import apply_cookie_payload


TEST_ENCRYPTION_KEY = base64.urlsafe_b64encode(b"0123456789ABCDEF0123456789ABCDEF")


def ensure_encryption_key():
    if not os.environ.get('USER_FIELD_ENCRYPTION_KEY'):
        os.environ['USER_FIELD_ENCRYPTION_KEY'] = TEST_ENCRYPTION_KEY.decode()


def create_user(username, email, password, role, *, is_admin=False, sites=None):
    user = User()
    user.is_admin = is_admin
    user.role = role
    user.username = username
    user.email = email
    user.set_password(password)
    if sites:
        user.sites.extend(sites)
    db.session.add(user)
    return user


def seed_data():
    site_a = Site(name='Alpha Plant', location='East Wing')
    site_b = Site(name='Beta Plant', location='West Wing')

    role_admin = Role(name='Admin', permissions='admin.full')
    role_limited = Role(
        name='LimitedTech',
        permissions='machines.view,maintenance.view,audits.view'
    )
    role_site_manager = Role(
        name='SiteManager',
        permissions='machines.view,maintenance.view,audits.view,sites.view'
    )
    role_basic = Role(name='Basic', permissions='machines.view')

    db.session.add_all([site_a, site_b, role_admin, role_limited, role_site_manager, role_basic])
    db.session.flush()

    admin = create_user('admin', 'admin@example.com', 'password', role_admin, is_admin=True, sites=[site_a, site_b])
    limited = create_user('limited', 'limited@example.com', 'password', role_limited, sites=[site_a])
    site_manager = create_user('manager', 'manager@example.com', 'password', role_site_manager, sites=[site_a])
    basic = create_user('basic', 'basic@example.com', 'password', role_basic, sites=[site_a])

    machine_a = Machine(name='Machine A', model='X100', serial_number='A-001', site=site_a)
    machine_b = Machine(name='Machine B', model='Z900', serial_number='B-001', site=site_b)
    db.session.add_all([machine_a, machine_b])

    part_a = Part(name='Filter', description='Primary filter', machine=machine_a)
    part_b = Part(name='Valve', description='Relief valve', machine=machine_b)
    db.session.add_all([part_a, part_b])

    audit_a = AuditTask(name='Daily Alpha Audit', description='Alpha site audit', site_id=site_a.id)
    audit_a.site = site_a
    audit_a.machines.append(machine_a)
    audit_b = AuditTask(name='Daily Beta Audit', description='Beta site audit', site_id=site_b.id)
    audit_b.site = site_b
    audit_b.machines.append(machine_b)
    db.session.add_all([audit_a, audit_b])

    db.session.commit()

    return {
        'sites': {'a': site_a, 'b': site_b},
        'users': {
            'admin': admin,
            'limited': limited,
            'manager': site_manager,
            'basic': basic,
        },
        'machines': {'a': machine_a, 'b': machine_b},
        'audits': {'a': audit_a, 'b': audit_b},
    }


def create_seeded_app():
    ensure_encryption_key()

    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        SECRET_KEY='rbac-test-secret',
        SQLALCHEMY_DATABASE_URI='sqlite://',
        SQLALCHEMY_ENGINE_OPTIONS={
            'connect_args': {'check_same_thread': False},
            'poolclass': StaticPool,
        },
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    app.register_blueprint(api_v1)

    @app.after_request
    def _apply_remember_cookies(response):
        return apply_cookie_payload(response)

    with app.app_context():
        db.create_all()
        seed_info = seed_data()

    return app, seed_info


def teardown_app(app):
    with app.app_context():
        db.session.remove()
        db.drop_all()
        # Clear the SQLAlchemy engine dispose to release connections
        db.engine.dispose()