"""
Configuration example file
Copy this file to config.py and update with your actual settings
Keep config.py out of version control (add to .gitignore)
"""
import os

# Security settings
SECRET_KEY = 'generate-a-secure-key-here'  # Use os.urandom(24).hex() to generate

# Email settings
MAIL_SERVER = 'your-smtp-server.example.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'your-username'
MAIL_PASSWORD = 'your-password' 
MAIL_DEFAULT_SENDER = 'sender@example.com'

# Database settings
DATABASE_URI = 'sqlite:///maintenance.db'  # Default SQLite config

# Other settings
DEBUG = False  # Disable debug in production
