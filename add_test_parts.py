#!/usr/bin/env python3
"""
Script to add test parts with specific maintenance schedules for testing the "Due Soon" status.
Creates parts with 60-day maintenance frequencies but due within 30 days.
"""

from app import app, db, Machine, Part, Site
from datetime import datetime, timedelta

def add_test_parts():
    """Add test parts to the database for testing due soon status."""
    
    with app.app_context():
        # Get current datetime for reference
        now = datetime.utcnow()
        
        # Find all sites to add parts to each site
        sites = Site.query.all()
        if not sites:
            print("No sites found in database. Please initialize database first.")
            return False
        
        # Create test parts for each site
        parts_added = 0
        for site in sites:
            print(f"Adding test parts for site: {site.name}")
            
            # Get machines for this site
            machines = Machine.query.filter_by(site_id=site.id).all()
            if not machines:
                print(f"No machines found for site {site.name}. Skipping.")
                continue
            
            # For each machine, add test parts with specific due dates
            for i, machine in enumerate(machines):
                # Create parts with 60-day frequency but next maintenance due within site threshold
                days_until_due = [5, 10, 15, 20, 25]  # Various days until due
                
                for j, days in enumerate(days_until_due):
                    if days <= site.notification_threshold:
                        status = "due soon"
                    else:
                        status = "ok"
                        
                    # Calculate last maintenance date to achieve the desired next maintenance date
                    last_maintenance_date = now - timedelta(days=60-days)
                    
                    # Create the part
                    part_name = f"Test-{site.name}-{i+1}-{j+1}"
                    new_part = Part(
                        name=part_name,
                        description=f"Test part with 60-day frequency, due in {days} days ({status})",
                        machine_id=machine.id,
                        maintenance_frequency=60,
                        maintenance_unit='day',
                        last_maintenance=last_maintenance_date
                    )
                    
                    # Manually set next maintenance
                    new_part.next_maintenance = last_maintenance_date + timedelta(days=60)
                    
                    db.session.add(new_part)
                    parts_added += 1
        
        # Commit all changes
        if parts_added > 0:
            db.session.commit()
            print(f"Added {parts_added} test parts successfully!")
            return True
        else:
            print("No parts were added.")
            return False

if __name__ == "__main__":
    add_test_parts()
