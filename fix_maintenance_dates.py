#!/usr/bin/env python3
"""
Fix Maintenance Dates Script
============================
This script recalculates and fixes the stored next_maintenance and last_maintenance
values on all Part records by using the actual latest maintenance record for each part.

This is necessary because bulk imports may have created parts with placeholder dates
(like dates from 1900) that incorrectly show as overdue.

The script will:
1. Find all parts in the database
2. For each part, find the latest valid maintenance record (after 2010)
3. Recalculate and update last_maintenance and next_maintenance based on actual data
4. Parts without valid maintenance records will have their dates cleared

Run this script once to fix the database after bulk imports.
"""

import os
import sys
from datetime import datetime, timedelta

# Add the current directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def fix_maintenance_dates():
    """Fix all part maintenance dates based on actual maintenance records."""
    
    # Import Flask app to get database context
    from app import app, db
    from models import Part, MaintenanceRecord
    
    MIN_VALID_DATE = datetime(2010, 1, 1)
    
    with app.app_context():
        print("=" * 60)
        print("Fix Maintenance Dates Script")
        print("=" * 60)
        print()
        
        # Get all parts
        all_parts = Part.query.all()
        total_parts = len(all_parts)
        
        print(f"Found {total_parts} parts in database")
        print()
        
        fixed_count = 0
        cleared_count = 0
        unchanged_count = 0
        
        for i, part in enumerate(all_parts, 1):
            # Find the latest valid maintenance record
            valid_records = [r for r in part.maintenance_records 
                           if r.date and r.date >= MIN_VALID_DATE]
            
            old_last = part.last_maintenance
            old_next = part.next_maintenance
            
            if valid_records:
                # Has valid maintenance history
                latest_record = max(valid_records, key=lambda r: r.date)
                
                # Get maintenance interval in days
                interval_days = 30  # Default
                if hasattr(part, 'maintenance_interval_days'):
                    try:
                        interval_days = part.maintenance_interval_days()
                    except:
                        pass
                
                # Calculate new dates
                if isinstance(latest_record.date, datetime):
                    new_last = latest_record.date
                else:
                    new_last = datetime.combine(latest_record.date, datetime.min.time())
                
                new_next = new_last + timedelta(days=interval_days)
                
                # Update if different
                if part.last_maintenance != new_last or part.next_maintenance != new_next:
                    part.last_maintenance = new_last
                    part.next_maintenance = new_next
                    fixed_count += 1
                    
                    if i <= 10 or fixed_count <= 10:  # Show first 10 fixes
                        print(f"  Fixed Part #{part.id} '{part.name}':")
                        print(f"    Old: last={old_last}, next={old_next}")
                        print(f"    New: last={new_last}, next={new_next}")
                else:
                    unchanged_count += 1
            else:
                # No valid maintenance history - clear dates
                if part.last_maintenance or part.next_maintenance:
                    part.last_maintenance = None
                    part.next_maintenance = None
                    cleared_count += 1
                    
                    if cleared_count <= 5:  # Show first 5 clears
                        print(f"  Cleared Part #{part.id} '{part.name}' (no valid maintenance records)")
                else:
                    unchanged_count += 1
            
            # Progress update every 100 parts
            if i % 100 == 0:
                print(f"Progress: {i}/{total_parts} parts processed...")
        
        # Commit all changes
        try:
            db.session.commit()
            print()
            print("=" * 60)
            print("Summary:")
            print(f"  Total parts: {total_parts}")
            print(f"  Fixed (recalculated dates): {fixed_count}")
            print(f"  Cleared (no valid history): {cleared_count}")
            print(f"  Unchanged: {unchanged_count}")
            print("=" * 60)
            print()
            print("✅ All changes committed successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error committing changes: {e}")
            return False
        
        return True

if __name__ == '__main__':
    print()
    print("This script will recalculate maintenance dates for all parts")
    print("based on their actual maintenance records.")
    print()
    print("Parts with maintenance records before 2010 will be treated as")
    print("having no valid maintenance history (bulk import placeholders).")
    print()
    
    response = input("Do you want to continue? (yes/no): ").strip().lower()
    
    if response in ('yes', 'y'):
        success = fix_maintenance_dates()
        sys.exit(0 if success else 1)
    else:
        print("Operation cancelled.")
        sys.exit(0)
