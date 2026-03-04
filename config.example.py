"""
Configuration example file
Copy this file to config.py and update with your actual settings
Keep config.py out of version control (add to .gitignore)

RECOMMENDED: Use environment variables or a .env file for all secrets and email configuration.
Do NOT store real credentials in this file or in version control.

For Flask, use python-dotenv or os.environ.get() to load these values securely.
"""
import os

# Security settings
SECRET_KEY = os.environ.get('SECRET_KEY', 'generate-a-secure-key-here')  # Use os.urandom(24).hex() to generate

# Email settings (use environment variables in production)
MAIL_SERVER = os.environ.get('MAIL_SERVER', 'your-smtp-server.example.com')
MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'your-username')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'your-password')
MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'sender@example.com')

# Database settings
DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///maintenance.db')  # Default SQLite config

# Other settings
DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 'yes')

# Bootstrap hardening feature flags (staged migration)
ALLOW_LEGACY_BOOTSTRAP_TOKEN = os.environ.get('ALLOW_LEGACY_BOOTSTRAP_TOKEN', 'true').lower() in ('true', '1', 'yes')
ENABLE_DEVICE_BOOTSTRAP_TOKEN = os.environ.get('ENABLE_DEVICE_BOOTSTRAP_TOKEN', 'false').lower() in ('true', '1', 'yes')
BOOTSTRAP_REQUIRE_DEVICE_ID = os.environ.get('BOOTSTRAP_REQUIRE_DEVICE_ID', 'false').lower() in ('true', '1', 'yes')
BOOTSTRAP_INCLUDE_ADMIN_SYNC_CREDS = os.environ.get('BOOTSTRAP_INCLUDE_ADMIN_SYNC_CREDS', 'true').lower() in ('true', '1', 'yes')

# User-scoped sync token rollout flags
ENABLE_USER_SCOPED_SYNC_TOKEN = os.environ.get('ENABLE_USER_SCOPED_SYNC_TOKEN', 'false').lower() in ('true', '1', 'yes')
ALLOW_LEGACY_SYNC_AUTH = os.environ.get('ALLOW_LEGACY_SYNC_AUTH', 'true').lower() in ('true', '1', 'yes')
SYNC_TOKEN_REQUIRE_DEVICE_MATCH = os.environ.get('SYNC_TOKEN_REQUIRE_DEVICE_MATCH', 'false').lower() in ('true', '1', 'yes')
SYNC_ACCESS_TOKEN_TTL_SECONDS = int(os.environ.get('SYNC_ACCESS_TOKEN_TTL_SECONDS', 43200))

# Phase 4 prep: user-scoped sync data filtering rollout flags
ENABLE_USER_SCOPED_SYNC_DATA = os.environ.get('ENABLE_USER_SCOPED_SYNC_DATA', 'false').lower() in ('true', '1', 'yes')
ALLOW_LEGACY_FULL_SYNC_DATA = os.environ.get('ALLOW_LEGACY_FULL_SYNC_DATA', 'true').lower() in ('true', '1', 'yes')
