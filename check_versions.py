import importlib
import sys

def check_compatibility():
    """Verify that installed package versions are compatible with the application"""
    
    required_versions = {
        'flask': '2.2.5',
        'werkzeug': '2.2.3',
        'sqlalchemy': '2.0.12',
    }
    
    problems = []
    
    for package, version in required_versions.items():
        try:
            module = importlib.import_module(package)
            actual_version = getattr(module, '__version__', 'unknown')
            print(f"Checking {package}: required={version}, installed={actual_version}")
            
            # Simple version check - in production you might want a more sophisticated check
            if actual_version != version and actual_version != 'unknown':
                problems.append(f"{package}: expected {version}, got {actual_version}")
        except ImportError:
            problems.append(f"{package}: not installed")
    
    if problems:
        print("WARNING: The following packages have version mismatches:")
        for problem in problems:
            print(f"  - {problem}")
        print("This may cause functionality issues.")
    else:
        print("All package versions are compatible.")

if __name__ == "__main__":
    check_compatibility()
