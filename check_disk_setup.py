import os
import sys

def ensure_directories():
    """Ensure all required persistent directories exist"""
    if not os.environ.get('RENDER', '').lower() == 'true':
        print("Not running on Render, skipping disk setup")
        return
    
    data_dir = os.environ.get('DATA_DIR', '/var/data')
    
    if not os.path.exists(data_dir):
        print(f"ERROR: Main data directory {data_dir} doesn't exist!")
        print("This suggests persistent disk is not mounted correctly")
        sys.exit(1)
    
    # Required subdirectories
    subdirs = [
        'db',
        'backups',
        'uploads',
        'logs',
        'exports',
        'temp'
    ]
    
    for subdir in subdirs:
        path = os.path.join(data_dir, subdir)
        if not os.path.exists(path):
            print(f"Creating directory: {path}")
            try:
                os.makedirs(path, exist_ok=True)
            except Exception as e:
                print(f"Failed to create {path}: {str(e)}")
    
    print("Directory check completed successfully")

if __name__ == "__main__":
    ensure_directories()
