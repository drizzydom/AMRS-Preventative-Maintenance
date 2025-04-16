"""
Database check utility for diagnosing issues
"""
import sys
import os

def print_info():
    """Print version information about database libraries"""
    print("=== Database Library Information ===")
    
    try:
        import sqlalchemy
        print(f"SQLAlchemy version: {sqlalchemy.__version__}")
    except ImportError:
        print("SQLAlchemy not installed")
    
    try:
        import flask_sqlalchemy
        print(f"Flask-SQLAlchemy version: {flask_sqlalchemy.__version__}")
    except ImportError:
        print("Flask-SQLAlchemy not installed")
    
    # Check DATABASE_URL environment variable
    db_url = os.environ.get('DATABASE_URL', 'Not set')
    print(f"DATABASE_URL: {db_url}")
    
    if db_url and db_url.startswith('postgres://'):
        print("Warning: DATABASE_URL uses 'postgres://' scheme which may need conversion to 'postgresql://'")
    
    print("=== End of Database Information ===")

if __name__ == "__main__":
    print_info()
