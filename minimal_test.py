#!/usr/bin/env python3

print("Starting minimal test...")

try:
    # First just check if the module exists
    import os
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'token_manager.py')
    print(f"Token manager file exists: {os.path.exists(file_path)}")
    
    # Try to debug parse errors
    with open(file_path, 'r') as f:
        content = f.read()
        print(f"File length: {len(content)} bytes")
        
    # Try to compile the file
    print("Compiling token_manager.py...")
    compile(content, file_path, 'exec')
    print("Compilation successful")
    
    # Try to import the module
    print("Importing token_manager...")
    import token_manager
    print(f"Module imported. Available names: {dir(token_manager)}")
    
    # Try to import the class
    from token_manager import TokenManager
    print("TokenManager class imported successfully")
    
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
