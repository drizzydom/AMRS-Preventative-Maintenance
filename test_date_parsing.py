#!/usr/bin/env python3
"""
Test script to verify the bulk import date parsing fixes.
This will test the date parsing logic to ensure it correctly handles various date formats.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta

def test_date_parsing():
    """Test the improved date parsing logic"""
    
    def parse_maintenance_date(date_str):
        """Mimic the improved date parsing from the bulk import"""
        date_obj = None
        
        if date_str:
            try:
                # Clean the date string - remove time part and extra whitespace
                date_str = str(date_str).strip().split(' ')[0]
                
                # Try different date formats
                date_formats = [
                    '%Y-%m-%d',      # 2025-01-16
                    '%m/%d/%Y',      # 01/16/2025
                    '%d/%m/%Y',      # 16/01/2025
                    '%Y/%m/%d',      # 2025/01/16
                    '%m-%d-%Y',      # 01-16-2025
                    '%d-%m-%Y'       # 16-01-2025
                ]
                
                for date_format in date_formats:
                    try:
                        date_obj = datetime.strptime(date_str, date_format)
                        print(f"✓ Successfully parsed '{date_str}' using format '{date_format}' -> {date_obj.date()}")
                        break
                    except ValueError:
                        continue
                        
            except Exception as e:
                print(f"✗ Failed to parse date '{date_str}': {e}")
        
        # If we couldn't parse the date, use a reasonable default (30 days ago)
        if date_obj is None:
            if date_str:
                print(f"⚠ Could not parse maintenance date '{date_str}', using 30 days ago as fallback")
            date_obj = datetime.now() - timedelta(days=30)
            
        return date_obj
    
    # Test various date formats
    test_dates = [
        "2025-01-16 00:00:00",  # JSON format with time
        "2025-01-16",           # ISO format
        "01/16/2025",           # US format
        "16/01/2025",           # European format
        "2025/01/16",           # Alternative format
        "01-16-2025",           # Dash format
        "16-01-2025",           # European dash format
        "",                     # Empty string
        "invalid-date",         # Invalid format
        None                    # None value
    ]
    
    print("Testing Date Parsing Logic:")
    print("=" * 50)
    
    for test_date in test_dates:
        print(f"\nTesting: '{test_date}'")
        result = parse_maintenance_date(test_date)
        print(f"Result: {result}")
        
        # Check if result is reasonable (not today's date unless it's supposed to be)
        today = datetime.now().date()
        if result.date() == today and test_date and test_date != "invalid-date":
            print("⚠ WARNING: This date parsed to today - might be incorrect!")

if __name__ == "__main__":
    test_date_parsing()
