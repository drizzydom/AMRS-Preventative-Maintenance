#!/usr/bin/env python3
"""
Test script to demonstrate the maintenance date calculation logic
"""
from datetime import datetime, timedelta

def calculate_next_maintenance(last_maintenance_date, frequency, unit):
    """Calculate the next maintenance date based on frequency and unit"""
    if unit == 'week':
        delta = timedelta(weeks=frequency)
    elif unit == 'month':
        delta = timedelta(days=frequency * 30)
    elif unit == 'year':
        delta = timedelta(days=frequency * 365)
    else:
        delta = timedelta(days=frequency)
    
    return last_maintenance_date + delta

def test_maintenance_calculations():
    """Test maintenance date calculations"""
    print("Testing Maintenance Date Calculations:")
    print("=" * 50)
    
    # Test data: (last_maintenance, frequency, unit, expected_description)
    test_cases = [
        (datetime(2025, 1, 16), 1, 'year', "Annual maintenance - should be 2026-01-16"),
        (datetime(2025, 1, 16), 6, 'month', "6-month maintenance - should be 2025-07-16"),
        (datetime(2025, 1, 16), 3, 'month', "Quarterly maintenance - should be 2025-04-16"),
        (datetime(2025, 1, 16), 30, 'day', "Monthly maintenance - should be 2025-02-15"),
        (datetime(2025, 1, 16), 90, 'day', "90-day maintenance - should be 2025-04-16"),
        (datetime(2025, 1, 16), 2, 'week', "Bi-weekly maintenance - should be 2025-01-30"),
    ]
    
    for last_maintenance, frequency, unit, description in test_cases:
        next_maintenance = calculate_next_maintenance(last_maintenance, frequency, unit)
        days_from_now = (next_maintenance - datetime.now()).days
        
        print(f"\nTest: {description}")
        print(f"Last maintenance: {last_maintenance.date()}")
        print(f"Frequency: {frequency} {unit}(s)")
        print(f"Next maintenance: {next_maintenance.date()}")
        print(f"Days from now: {days_from_now}")
        
        if days_from_now < 0:
            print("⚠ OVERDUE!")
        elif days_from_now <= 7:
            print("⚠ DUE SOON!")
        else:
            print("✓ On schedule")

if __name__ == "__main__":
    test_maintenance_calculations()
