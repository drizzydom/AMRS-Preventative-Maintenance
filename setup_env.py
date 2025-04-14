#!/usr/bin/env python3
"""
Environment setup script for AMRS-Preventative-Maintenance
Installs the appropriate requirements based on the target environment
"""

import os
import sys
import subprocess
import argparse

def setup_environment(env_type="local"):
    """
    Set up the environment based on specified type
    
    Args:
        env_type (str): The environment type to set up
                        - "local": Local development environment
                        - "render": Render.com deployment environment
                        - "windows": Windows app build environment
    """
    print(f"Setting up {env_type} environment...")
    
    req_file = "requirements.txt"
    if env_type == "render":
        req_file = "requirements-render.txt"
    elif env_type == "windows":
        req_file = "requirements-windows.txt"
    
    if not os.path.exists(req_file):
        print(f"Error: {req_file} not found!")
        return False
    
    try:
        print(f"Installing dependencies from {req_file}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_file])
        print("Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set up the environment for AMRS-Preventative-Maintenance")
    parser.add_argument(
        "--env", 
        choices=["local", "render", "windows"], 
        default="local",
        help="The environment type to set up"
    )
    args = parser.parse_args()
    
    setup_environment(args.env)
