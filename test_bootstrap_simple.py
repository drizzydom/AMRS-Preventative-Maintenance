#!/usr/bin/env python3
"""
Manual bootstrap test - simplified version without external dependencies
"""

import os
import subprocess
import sys

def load_env_file():
    """Load environment variables from .env file."""
    try:
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # Remove quotes if present
                        value = value.strip('"\'')
                        os.environ[key] = value
            print("✅ Loaded environment variables from .env file")
            return True
        else:
            print("❌ .env file not found")
            return False
    except Exception as e:
        print(f"❌ Error loading .env file: {e}")
        return False

def test_bootstrap_flow():
    """Test the full bootstrap flow locally."""
    
    print("🚀 Testing Bootstrap Flow")
    print("=" * 40)
    
    # Load .env file first
    print("\n0. Loading Environment Variables:")
    if not load_env_file():
        return False
    
    # Check environment variables
    print("\n1. Checking Environment Variables:")
    bootstrap_url = os.environ.get('BOOTSTRAP_URL')
    bootstrap_token = os.environ.get('BOOTSTRAP_SECRET_TOKEN')
    admin_username = os.environ.get('AMRS_ADMIN_USERNAME')
    admin_password = os.environ.get('AMRS_ADMIN_PASSWORD')
    online_url = os.environ.get('AMRS_ONLINE_URL')
    
    env_vars = {
        'BOOTSTRAP_URL': bootstrap_url,
        'BOOTSTRAP_SECRET_TOKEN': bootstrap_token[:20] + "..." if bootstrap_token and len(bootstrap_token) > 20 else bootstrap_token,
        'AMRS_ADMIN_USERNAME': admin_username,
        'AMRS_ADMIN_PASSWORD': "SET" if admin_password else "NOT SET",
        'AMRS_ONLINE_URL': online_url
    }
    
    all_set = True
    for key, value in env_vars.items():
        status = "✅" if value else "❌"
        print(f"   {status} {key}: {value if value else 'NOT SET'}")
        if not value:
            all_set = False
    
    if not all_set:
        print("\n❌ Missing required environment variables!")
        return False
    
    # Check if we're in offline mode
    print("\n2. Checking Database Mode:")
    database_url = os.environ.get('DATABASE_URL', '')
    is_offline = (
        database_url.startswith('sqlite://') or 
        not database_url or
        database_url == 'sqlite:///maintenance.db'
    )
    mode = "🏠 Offline (SQLite)" if is_offline else "🌐 Online (PostgreSQL)"
    print(f"   Database Mode: {mode}")
    print(f"   DATABASE_URL: {database_url if database_url else 'Not set (defaults to SQLite)'}")
    
    # Check for required files
    print("\n3. Checking Required Files:")
    required_files = ['app.py', 'sync_db.py', '.env']
    for file in required_files:
        exists = os.path.exists(file)
        status = "✅" if exists else "❌"
        print(f"   {status} {file}")
        if not exists and file != '.env':  # .env might not exist in some setups
            print(f"❌ Missing required file: {file}")
            return False
    
    print("\n4. Testing Bootstrap Function:")
    print("   To test the actual bootstrap, run the application with:")
    print(f"   python app.py")
    print("   \n   Look for these log messages:")
    print("   - '[APP] Attempting bootstrap from: <URL>'")
    print("   - '[APP] Successfully bootstrapped and stored X secrets from remote.'")
    print("   - '[APP] Bootstrap successful - will trigger initial sync after app initialization'")
    print("   - '[APP] Running sync_db.py for initial data sync...'")
    print("   - '[APP] Initial database sync completed successfully'")
    
    print("\n5. Manual Tests You Can Run:")
    print("   Test bootstrap endpoint:")
    print(f"   curl -X POST '{bootstrap_url}' -H 'Authorization: Bearer {bootstrap_token[:20]}...' -v")
    print("   \n   Test manual sync:")
    print(f"   python sync_db.py --url '{online_url}' --username '{admin_username}' --password '<password>'")
    
    print("\n✅ Environment setup looks good for bootstrap testing!")
    print("\n🔧 Next Steps:")
    print("   1. Run 'python app.py' to test the bootstrap process")
    print("   2. Check the console logs for bootstrap success/failure")
    print("   3. If bootstrap succeeds, try logging in with existing user credentials")
    print("   4. If login works, the full bootstrap->sync->login flow is working!")
    
    return True

if __name__ == "__main__":
    test_bootstrap_flow()
