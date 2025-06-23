#!/usr/bin/env python3
"""
Test the bulk import maintenance date fixes by creating a test import and verifying results
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Flask app context for testing
os.environ['FLASK_ENV'] = 'development'

from app import app, db, Site, Machine, Part, MaintenanceRecord, User
from datetime import datetime, timedelta
import json

def test_bulk_import_dates():
    """Test that bulk import correctly sets maintenance dates"""
    
    with app.app_context():
        print("Testing Bulk Import Date Handling:")
        print("=" * 50)
        
        # Get or create a test site
        test_site = Site.query.filter_by(name='Test Site').first()
        if not test_site:
            print("No 'Test Site' found. Please create one through the web interface first.")
            return
        
        # Get a test machine from the site
        test_machine = Machine.query.filter_by(site_id=test_site.id).first()
        if not test_machine:
            print("No machines found in Test Site. Please add a machine first.")
            return
        
        print(f"Using Site: {test_site.name}")
        print(f"Using Machine: {test_machine.name}")
        
        # Get a test part from the machine
        test_part = Part.query.filter_by(machine_id=test_machine.id).first()
        if not test_part:
            print("No parts found in machine. Please add a part first.")
            return
        
        print(f"Using Part: {test_part.name}")
        
        # Check current maintenance dates
        print(f"\nBEFORE UPDATE:")
        print(f"Part last_maintenance: {test_part.last_maintenance}")
        print(f"Part next_maintenance: {test_part.next_maintenance}")
        print(f"Part maintenance_frequency: {test_part.maintenance_frequency}")
        print(f"Part maintenance_unit: {test_part.maintenance_unit}")
        
        # Check maintenance records for this part
        maintenance_records = MaintenanceRecord.query.filter_by(part_id=test_part.id).order_by(MaintenanceRecord.date.desc()).all()
        print(f"\nMaintenance Records ({len(maintenance_records)} total):")
        for i, record in enumerate(maintenance_records[:5]):  # Show first 5
            print(f"  {i+1}. Date: {record.date}, Type: {record.maintenance_type}, Description: {record.description[:50]}...")
        
        # Now test our update function
        from app import update_part_maintenance_dates
        
        print(f"\nRunning update_part_maintenance_dates()...")
        update_part_maintenance_dates(test_part)
        db.session.commit()
        
        # Check updated maintenance dates
        print(f"\nAFTER UPDATE:")
        print(f"Part last_maintenance: {test_part.last_maintenance}")
        print(f"Part next_maintenance: {test_part.next_maintenance}")
        
        # Verify the calculation is correct
        if test_part.last_maintenance and maintenance_records:
            latest_record = maintenance_records[0]  # Already sorted by date desc
            print(f"\nVERIFICATION:")
            print(f"Latest maintenance record date: {latest_record.date}")
            print(f"Part's last_maintenance: {test_part.last_maintenance}")
            print(f"Dates match: {latest_record.date.date() == test_part.last_maintenance.date()}")
            
            # Check next maintenance calculation
            if test_part.next_maintenance:
                freq = test_part.maintenance_frequency or 30
                unit = test_part.maintenance_unit or 'day'
                
                if unit == 'week':
                    expected_delta = timedelta(weeks=freq)
                elif unit == 'month':
                    expected_delta = timedelta(days=freq * 30)
                elif unit == 'year':
                    expected_delta = timedelta(days=freq * 365)
                else:
                    expected_delta = timedelta(days=freq)
                
                expected_next = test_part.last_maintenance + expected_delta
                print(f"Expected next maintenance: {expected_next}")
                print(f"Actual next maintenance: {test_part.next_maintenance}")
                print(f"Calculation correct: {expected_next.date() == test_part.next_maintenance.date()}")
                
                # Check if overdue
                days_until_due = (test_part.next_maintenance - datetime.now()).days
                print(f"Days until due: {days_until_due}")
                if days_until_due < 0:
                    print("🔴 OVERDUE")
                elif days_until_due <= 7:
                    print("🟡 DUE SOON")
                else:
                    print("🟢 ON SCHEDULE")
        
        print("\n" + "=" * 50)
        print("Test completed!")

if __name__ == "__main__":
    test_bulk_import_dates()
