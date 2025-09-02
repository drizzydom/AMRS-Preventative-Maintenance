#!/usr/bin/env python3
"""
Build with Server Selection
Choose test or production server be    # Confirmation
    platform_names = {
        '1': 'Windows 10+',
        '2': 'macOS',
        '3': 'Linux',
        '4': 'All platforms'
    }lding the Electron app
"""

import os
import sys
import subprocess
from pathlib import Path

def set_server_environment(server_type):
    """Set environment variables for the specified server"""
    if server_type == 'test':
        os.environ['AMRS_ONLINE_URL'] = 'https://test.accuratemachinerepair.com'
        os.environ['BOOTSTRAP_URL'] = 'https://test.accuratemachinerepair.com/bootstrap'
        os.environ['FLASK_ENV'] = 'development'
        print("🧪 Configured for TEST server")
    elif server_type == 'production':
        os.environ['AMRS_ONLINE_URL'] = 'https://api.accuratemachinerepair.com'
        os.environ['BOOTSTRAP_URL'] = 'https://api.accuratemachinerepair.com/bootstrap'
        os.environ['FLASK_ENV'] = 'production'
        print("🚀 Configured for PRODUCTION server")
    
    print(f"   Server URL: {os.environ['AMRS_ONLINE_URL']}")
    print(f"   Bootstrap URL: {os.environ['BOOTSTRAP_URL']}")

def run_build(build_command):
    """Run the npm build command with current environment"""
    print(f"\n🔨 Running build command: {build_command}")
    try:
        result = subprocess.run(['npm', 'run', build_command], 
                              env=os.environ.copy(), 
                              check=True)
        print(f"✅ Build completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed with error code {e.returncode}")
        return False

def main():
    """Main build script with server selection"""
    print("🏗️  AMRS Maintenance Tracker - Build with Server Selection")
    print("=" * 60)
    
    # Server selection
    print("\nSelect target server:")
    print("1. TEST server (test.accuratemachinerepair.com)")
    print("2. PRODUCTION server (api.accuratemachinerepair.com)")
    
    server_choice = input("\nEnter choice (1 or 2): ").strip()
    
    if server_choice == '1':
        server_type = 'test'
    elif server_choice == '2':
        print("\n⚠️  WARNING: Building for PRODUCTION server!")
        confirm = input("Are you sure? (yes/no): ").lower()
        if confirm != 'yes':
            print("Build cancelled.")
            sys.exit(0)
        server_type = 'production'
    else:
        print("Invalid choice. Exiting.")
        sys.exit(1)
    
    # Set server environment
    set_server_environment(server_type)
    
    # Platform selection
    print("\nSelect build target:")
    print("1. Windows 10+ (Electron 28.3.3)")
    print("2. macOS (Electron 28.3.3)")
    print("3. Linux (Electron 28.3.3)")
    print("4. All platforms")
    
    platform_choice = input("\nEnter choice (1-4): ").strip()
    
    build_commands = {
        '1': 'build:win10',
        '2': 'build:mac',
        '3': 'build:linux',
        '4': 'build:all'
    }
    
    if platform_choice not in build_commands:
        print("Invalid choice. Exiting.")
        sys.exit(1)
    
    build_command = build_commands[platform_choice]
    
    # Confirmation
    platform_names = {
        '1': 'Windows 10+',
        '2': 'macOS',
        '3': 'Linux',
        '4': 'All Platforms'
    }
    
    print(f"\n📋 Build Summary:")
    print(f"   Server: {server_type.upper()}")
    print(f"   Platform: {platform_names[platform_choice]}")
    print(f"   Command: npm run {build_command}")
    
    proceed = input("\nProceed with build? (yes/no): ").lower()
    if proceed != 'yes':
        print("Build cancelled.")
        sys.exit(0)
    
    # Run the build
    success = run_build(build_command)
    
    if success:
        print(f"\n🎉 SUCCESS! Built for {server_type.upper()} server")
        print(f"📦 Check the dist/ folder for your built application")
    else:
        print(f"\n❌ Build failed. Check the output above for errors.")
        sys.exit(1)

if __name__ == "__main__":
    main()
