#!/usr/bin/env python3
"""
Utility script to fix maintenance dates for all parts in the database.
This should be run after bulk imports to ensure all parts have correct last/next maintenance dates.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Flask app context
os.environ['FLASK_ENV'] = 'development'

from app import app, db, Part, MaintenanceRecord
from datetime import datetime, timedelta

def fix_all_part_maintenance_dates():
    """Fix maintenance dates for all parts in the database"""
    
    def update_part_maintenance_dates(part):
        """Update part's last_maintenance and next_maintenance based on actual maintenance records"""
        
        # Find the most recent maintenance record for this part
        latest_maintenance = MaintenanceRecord.query.filter_by(
            part_id=part.id
        ).order_by(MaintenanceRecord.date.desc()).first()
        
        old_last = part.last_maintenance
        old_next = part.next_maintenance
        
        if latest_maintenance:
            # Update last_maintenance to the actual latest date
            part.last_maintenance = latest_maintenance.date
            
            # Calculate next maintenance date based on frequency
            freq = part.maintenance_frequency or 30
            unit = part.maintenance_unit or 'day'
            
            if unit == 'week':
                delta = timedelta(weeks=freq)
            elif unit == 'month':
                delta = timedelta(days=freq * 30)
            elif unit == 'year':
                delta = timedelta(days=freq * 365)
            else:
                delta = timedelta(days=freq)
                
            part.next_maintenance = part.last_maintenance + delta
            
            return True, old_last, old_next
        else:
            # No maintenance records found, clear the dates
            part.last_maintenance = None
            part.next_maintenance = None
            return False, old_last, old_next
    
    with app.app_context():
        print("Fixing Maintenance Dates for All Parts:")
        print("=" * 60)
        
        # Get all parts
        all_parts = Part.query.all()
        total_parts = len(all_parts)
        
        print(f"Found {total_parts} parts to process...")
        
        updated_count = 0
        fixed_count = 0
        
        for i, part in enumerate(all_parts, 1):
            print(f"\nProcessing {i}/{total_parts}: {part.machine.name} - {part.name}")
            
            has_maintenance, old_last, old_next = update_part_maintenance_dates(part)
            
            if has_maintenance:
                updated_count += 1
                
                # Check if we actually fixed something
                if (old_last != part.last_maintenance or old_next != part.next_maintenance):
                    fixed_count += 1
                    print(f"  🔧 FIXED:")
                    print(f"    Old last maintenance: {old_last}")
                    print(f"    New last maintenance: {part.last_maintenance}")
                    print(f"    Old next maintenance: {old_next}")
                    print(f"    New next maintenance: {part.next_maintenance}")
                    
                    # Check status
                    if part.next_maintenance:
                        days_until = (part.next_maintenance - datetime.now()).days
                        if days_until < 0:
                            print(f"    📅 Status: OVERDUE by {abs(days_until)} days")
                        elif days_until <= 7:
                            print(f"    📅 Status: DUE SOON ({days_until} days)")
                        else:
                            print(f"    📅 Status: ON SCHEDULE ({days_until} days)")
                else:
                    print(f"  ✅ Already correct")
            else:
                print(f"  ⚠️  No maintenance records found")
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"\n" + "=" * 60)
            print(f"✅ Successfully processed {total_parts} parts:")
            print(f"   - {updated_count} parts had maintenance records")
            print(f"   - {fixed_count} parts had incorrect dates that were fixed")
            print(f"   - {total_parts - updated_count} parts had no maintenance records")
            print("\nAll changes have been saved to the database.")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error saving changes: {str(e)}")
            return False
        
        return True

if __name__ == "__main__":
    print("AMRS Maintenance Date Fix Utility")
    print("This will update all parts' last_maintenance and next_maintenance dates")
    print("based on their actual maintenance records.\n")
    
    response = input("Do you want to proceed? (y/N): ").strip().lower()
    if response == 'y':
        success = fix_all_part_maintenance_dates()
        if success:
            print("\n🎉 Maintenance date fix completed successfully!")
        else:
            print("\n💥 Maintenance date fix failed!")
    else:
        print("Operation cancelled.")
