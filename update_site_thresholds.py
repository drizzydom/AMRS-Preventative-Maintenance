#!/usr/bin/env python3
"""
Script to update all sites to have a notification threshold of 30 days.
This ensures consistent behavior across the maintenance tracking system.
"""

from app import app, db, Site

def update_site_thresholds(days=30):
    """Update notification_threshold for all sites to the specified number of days."""
    with app.app_context():
        # Get current sites and their thresholds
        sites = Site.query.all()
        if not sites:
            print("No sites found in database.")
            return False
            
        print("Current site thresholds:")
        for site in sites:
            print(f"  - {site.name}: {site.notification_threshold} days")
            
        # Update all sites to the new threshold
        updated_count = 0
        for site in sites:
            if site.notification_threshold != days:
                site.notification_threshold = days
                updated_count += 1
                
        if updated_count > 0:
            db.session.commit()
            print(f"\nUpdated {updated_count} site(s) to {days} days notification threshold.")
        else:
            print("\nAll sites already had the specified threshold. No updates needed.")
            
        # Verify the changes
        print("\nVerified site thresholds:")
        for site in Site.query.all():
            print(f"  - {site.name}: {site.notification_threshold} days")
            
        return True

if __name__ == "__main__":
    update_site_thresholds(30)
    print("\nDone. All sites now have a 30-day notification threshold.")
