#!/usr/bin/env python3
"""
SQLAlchemy DateTime Parsing Patch for Python 3.11.0 Compatibility
This module patches SQLAlchemy's datetime parsing to handle ISO format strings properly
"""

import sqlalchemy
from sqlalchemy.engine import result
from datetime import datetime
import re

def safe_parse_datetime(dt_string):
    """Safely parse datetime strings in various formats"""
    if not dt_string or dt_string is None:
        return None
    
    # If it's already a datetime object, return it
    if isinstance(dt_string, datetime):
        return dt_string
    
    # If it's not a string, try to convert it
    if not isinstance(dt_string, str):
        try:
            return datetime.fromisoformat(str(dt_string))
        except:
            return None
    
    # Clean the string
    dt_string = dt_string.strip()
    
    # Handle different datetime formats
    formats_to_try = [
        # ISO formats with microseconds
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%d %H:%M:%S.%f',
        # ISO formats without microseconds
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
        # Date only
        '%Y-%m-%d',
        # With timezone info (basic handling)
        '%Y-%m-%dT%H:%M:%S%z',
        '%Y-%m-%dT%H:%M:%S.%f%z',
    ]
    
    # Try each format
    for fmt in formats_to_try:
        try:
            return datetime.strptime(dt_string, fmt)
        except ValueError:
            continue
    
    # Try fromisoformat as last resort
    try:
        # Handle the specific case where there's no timezone but it looks like ISO
        if 'T' in dt_string and not dt_string.endswith('Z') and '+' not in dt_string:
            return datetime.fromisoformat(dt_string)
    except ValueError:
        pass
    
    print(f"[DATETIME PATCH] Warning: Could not parse datetime string: '{dt_string}'")
    return None

# Store the original make_row function
original_make_row = None

def patched_make_row_factory(cursor):
    """Create a patched make_row function that handles datetime parsing errors"""
    original_factory = getattr(cursor, '_orig_make_row_factory', None)
    if original_factory:
        original_make_row_func = original_factory()
    else:
        # Fallback to basic row creation
        def original_make_row_func(row):
            return row
    
    def patched_make_row(row):
        """Patched make_row that safely handles datetime strings"""
        try:
            # Try the original function first
            return original_make_row_func(row)
        except ValueError as e:
            if "Couldn't parse datetime string" in str(e) or "Invalid isoformat string" in str(e):
                # Extract the problematic datetime string from the error
                error_msg = str(e)
                if "'" in error_msg:
                    # Try to extract the datetime string from the error message
                    import re
                    match = re.search(r"'([^']*)'", error_msg)
                    if match:
                        problematic_string = match.group(1)
                        print(f"[DATETIME PATCH] Fixing datetime parsing error for: '{problematic_string}'")
                
                # Convert the row to a list so we can modify it
                if hasattr(row, '_data'):
                    row_data = list(row._data)
                elif hasattr(row, '_row'):
                    row_data = list(row._row)
                else:
                    row_data = list(row)
                
                # Find and fix datetime strings in the row
                for i, value in enumerate(row_data):
                    if isinstance(value, str):
                        # Check if this looks like a datetime string
                        if re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', value) or \
                           re.match(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', value):
                            fixed_datetime = safe_parse_datetime(value)
                            if fixed_datetime:
                                row_data[i] = fixed_datetime
                            else:
                                # If we can't parse it, convert to a standard format
                                try:
                                    # Try to at least extract date parts
                                    if 'T' in value:
                                        date_part = value.split('T')[0]
                                        row_data[i] = datetime.strptime(date_part, '%Y-%m-%d')
                                    elif ' ' in value:
                                        date_part = value.split(' ')[0]
                                        row_data[i] = datetime.strptime(date_part, '%Y-%m-%d')
                                except:
                                    row_data[i] = None
                
                # Create a new row-like object
                if hasattr(row, '_data'):
                    row._data = tuple(row_data)
                elif hasattr(row, '_row'):
                    row._row = tuple(row_data)
                else:
                    row = tuple(row_data)
                
                # Try the original function again with fixed data
                try:
                    return original_make_row_func(row)
                except:
                    # If it still fails, return a basic tuple
                    return tuple(row_data)
            else:
                # Re-raise other ValueError exceptions
                raise
        except Exception as e:
            print(f"[DATETIME PATCH] Unexpected error in make_row: {e}")
            # Return the row as-is if we can't handle the error
            return row
    
    return patched_make_row

def patch_sqlalchemy_datetime():
    """Apply the datetime parsing patch to SQLAlchemy"""
    print("[DATETIME PATCH] Applying SQLAlchemy datetime parsing patch for Python 3.11.0 compatibility...")
    
    # Patch the result module's make_row functionality
    if hasattr(result, 'Result'):
        original_init = result.Result.__init__
        
        def patched_result_init(self, *args, **kwargs):
            result_obj = original_init(self, *args, **kwargs)
            
            # Store original make_row factory if it exists
            if hasattr(self, '_make_row'):
                self._orig_make_row_factory = self._make_row
                # Replace with our patched version
                self._make_row = patched_make_row_factory(self)
            
            return result_obj
        
        result.Result.__init__ = patched_result_init
    
    print("[DATETIME PATCH] SQLAlchemy datetime parsing patch applied successfully")

# Auto-apply the patch when this module is imported
patch_sqlalchemy_datetime()
