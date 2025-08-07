"""
Comprehensive datetime utilities for consistent datetime handling across the entire application.
This ensures datetime consistency in:
1. Database storage (SQLite)
2. JSON serialization/deserialization (sync)
3. SQLAlchemy model operations
4. API endpoints
"""

import re
from datetime import datetime
from typing import Optional, Union


def normalize_datetime_string(dt_string: str) -> str:
    """
    Normalize datetime strings to a consistent format that SQLAlchemy/SQLite can handle.
    
    Converts:
    - '2025-04-28T18:17:52.547667' -> '2025-04-28 18:17:52'
    - '2025-04-28T18:17:52' -> '2025-04-28 18:17:52'
    - '2025-04-28 18:17:52.547667' -> '2025-04-28 18:17:52'
    
    Returns standard SQLite datetime format: 'YYYY-MM-DD HH:MM:SS'
    """
    if not dt_string:
        return dt_string
    
    # Remove microseconds (everything after the dot)
    if '.' in dt_string:
        dt_string = dt_string.split('.')[0]
    
    # Replace 'T' separator with space
    if 'T' in dt_string:
        dt_string = dt_string.replace('T', ' ')
    
    # Ensure proper format
    # Match YYYY-MM-DD HH:MM:SS pattern
    pattern = r'(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})'
    match = re.match(pattern, dt_string)
    
    if match:
        return f"{match.group(1)} {match.group(2)}"
    
    # If no match, try to parse and reformat
    try:
        # Try various datetime formats
        for fmt in [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S.%f'
        ]:
            try:
                dt = datetime.strptime(dt_string, fmt)
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                continue
    except Exception:
        pass
    
    # If all else fails, return original
    return dt_string


def safe_parse_datetime(dt_value: Union[str, datetime, None]) -> Optional[datetime]:
    """
    Safely parse datetime from various input types.
    
    Args:
        dt_value: String, datetime object, or None
        
    Returns:
        datetime object or None if parsing fails
    """
    if dt_value is None:
        return None
    
    # If it's already a datetime object, return it
    if isinstance(dt_value, datetime):
        return dt_value
    
    # If it's a string, normalize and parse it
    if isinstance(dt_value, str):
        try:
            normalized = normalize_datetime_string(dt_value)
            return datetime.strptime(normalized, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                # Fallback: try fromisoformat after normalization
                return datetime.fromisoformat(normalized)
            except ValueError:
                print(f"[DATETIME_UTILS] Failed to parse datetime: {dt_value}")
                return None
    
    # If it's neither string nor datetime, return None
    return None


def datetime_to_json_string(dt: Optional[datetime]) -> Optional[str]:
    """
    Convert datetime to JSON-safe string format.
    
    Args:
        dt: datetime object or None
        
    Returns:
        ISO format string without microseconds, or None
    """
    if dt is None:
        return None
    
    if isinstance(dt, datetime):
        # Return in ISO format without microseconds
        return dt.strftime('%Y-%m-%dT%H:%M:%S')
    
    return None


def datetime_to_sqlite_string(dt: Optional[datetime]) -> Optional[str]:
    """
    Convert datetime to SQLite-compatible string format.
    
    Args:
        dt: datetime object or None
        
    Returns:
        SQLite format string, or None
    """
    if dt is None:
        return None
    
    if isinstance(dt, datetime):
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    
    return None


def ensure_datetime_compatibility(value: Union[str, datetime, None]) -> Union[datetime, None]:
    """
    Ensure a datetime value is compatible with SQLAlchemy operations.
    This is the main function to use throughout the application.
    
    Args:
        value: Any datetime-like value
        
    Returns:
        datetime object or None
    """
    return safe_parse_datetime(value)


# Utility function for fixing existing database datetime fields
def fix_datetime_field_in_db(db_path: str, table_name: str, field_name: str):
    """
    Fix datetime fields in an existing SQLite database.
    
    Args:
        db_path: Path to SQLite database
        table_name: Name of the table
        field_name: Name of the datetime field to fix
    """
    import sqlite3
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all records with non-null datetime values
        cursor.execute(f"SELECT id, {field_name} FROM {table_name} WHERE {field_name} IS NOT NULL")
        records = cursor.fetchall()
        
        fixed_count = 0
        for record_id, dt_value in records:
            if dt_value and isinstance(dt_value, str):
                normalized = normalize_datetime_string(dt_value)
                if normalized != dt_value:
                    cursor.execute(
                        f"UPDATE {table_name} SET {field_name} = ? WHERE id = ?",
                        (normalized, record_id)
                    )
                    fixed_count += 1
        
        conn.commit()
        conn.close()
        
        if fixed_count > 0:
            print(f"[DATETIME_UTILS] Fixed {fixed_count} datetime values in {table_name}.{field_name}")
        
        return fixed_count
        
    except Exception as e:
        print(f"[DATETIME_UTILS] Error fixing datetime field {table_name}.{field_name}: {e}")
        return 0
