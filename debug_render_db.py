"""
Utility script to debug database connection issues on Render
"""
import os
import sys
import subprocess

def check_render_environment():
    """Check the Render environment variables and database configuration"""
    print("\n=== Render Environment Diagnostic ===")
    
    # Check if we're running on Render
    is_render = os.environ.get('RENDER', '') == 'true'
    print(f"Running on Render: {is_render}")
    
    # Check for DATABASE_URL
    database_url = os.environ.get('DATABASE_URL', 'Not set')
    masked_url = database_url
    if database_url != 'Not set' and '@' in database_url:
        # Mask the password in the URL for security
        parts = database_url.split('@')
        credentials = parts[0].split(':')
        if len(credentials) > 2:
            masked_url = f"{credentials[0]}:****@{parts[1]}"
    
    print(f"DATABASE_URL: {masked_url}")
    
    # Check if PostgreSQL client is available
    try:
        result = subprocess.run(['which', 'psql'], capture_output=True, text=True)
        print(f"PostgreSQL client available: {result.stdout.strip() != ''}")
    except:
        print("PostgreSQL client check failed")
    
    # Check database connection with psql if DATABASE_URL is set
    if database_url != 'Not set' and 'postgres' in database_url:
        try:
            print("\nTesting database connection with psql...")
            # Use psql to check the connection
            result = subprocess.run(
                ['psql', database_url, '-c', 'SELECT version()'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✓ Connection successful!")
                print(result.stdout)
            else:
                print("✗ Connection failed!")
                print(result.stderr)
        except Exception as e:
            print(f"Error testing connection: {e}")
    
    print("\n=== Database Environment Variables ===")
    for key, value in os.environ.items():
        if 'DB' in key.upper() or 'SQL' in key.upper() or 'DATABASE' in key.upper():
            masked_value = value
            if '@' in value and ':' in value:
                # Mask potential passwords in connection strings
                masked_value = '****'
            print(f"{key}: {masked_value}")
    
    print("\n=== End of Diagnostic ===")

if __name__ == "__main__":
    check_render_environment()
