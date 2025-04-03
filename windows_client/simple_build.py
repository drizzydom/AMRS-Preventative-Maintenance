#!/usr/bin/env python3
"""
Simplified build script for Windows that avoids common issues
"""
import os
import sys
import subprocess
import platform

def main():
    # Get the server URL from command line args
    server_url = None
    if len(sys.argv) > 1:
        server_url = sys.argv[1]
    
    # Check if required modules are installed
    print("Checking and installing required dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                       check=True)
    except:
        print("Warning: Could not install dependencies automatically.")
    
    # Create server config if provided
    if server_url:
        import json
        print(f"Configuring for server: {server_url}")
        with open("server_config.json", "w") as f:
            json.dump({"server_url": server_url, "preconfigured": True}, f)
    
    # Build command
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name", "MaintenanceTracker",
        # Include hidden imports
        "--hidden-import=keyring",
        "--hidden-import=keyring.backends",
    ]
    
    # Add data files
    if os.path.exists("LICENSE"):
        cmd.extend(["--add-data", "LICENSE;."])
    
    if server_url and os.path.exists("server_config.json"):
        cmd.extend(["--add-data", "server_config.json;."])
    
    # Add main script
    cmd.append("main.py")
    
    # Run PyInstaller
    print("Running PyInstaller with command:")
    print(" ".join(cmd))
    
    try:
        subprocess.run(cmd, check=True)
        print("\nBuild successful! Executable created in dist folder.")
    except subprocess.CalledProcessError:
        print("\nBuild failed. See output above for details.")
        sys.exit(1)
    
    # Clean up
    if server_url and os.path.exists("server_config.json"):
        os.remove("server_config.json")

if __name__ == "__main__":
    main()
