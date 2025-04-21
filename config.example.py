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
