"""
Debug utilities for database connection issues
"""
import os
import sys
import importlib
import pkg_resources

def print_db_debug_info():
    """
    Print debug information about database configuration and SQLAlchemy
    """
    print("\n===== DATABASE DEBUG INFORMATION =====")
    
    # SQLAlchemy version
    try:
        import sqlalchemy
        print(f"SQLAlchemy version: {sqlalchemy.__version__}")
    except ImportError:
        print("SQLAlchemy not found")
    
    # Flask-SQLAlchemy version
    try:
        import flask_sqlalchemy
        print(f"Flask-SQLAlchemy version: {flask_sqlalchemy.__version__}")
    except ImportError:
        print("Flask-SQLAlchemy not found")
    
    # Database URL
    database_url = os.environ.get('DATABASE_URL', 'Not set')
    print(f"DATABASE_URL environment variable: {database_url}")
    
    # Modified URL (for Postgres)
    if database_url.startswith("postgres://"):
        modified_url = database_url.replace("postgres://", "postgresql://", 1)
        print(f"Modified URL for SQLAlchemy: {modified_url}")
    
    # Python version
    print(f"Python version: {sys.version}")
    
    # List all installed packages
    print("\nInstalled packages:")
    installed_packages = pkg_resources.working_set
    for package in sorted(installed_packages, key=lambda p: p.key):
        print(f"  {package.key} {package.version}")
    
    print("======================================\n")

# If this file is run directly, print debug info
if __name__ == "__main__":
    print_db_debug_info()
