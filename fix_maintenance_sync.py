from app import app
from models import db, Part, MaintenanceRecord
from datetime import datetime, date

def fix_maintenance_dates():
    with app.app_context():
        print("Starting maintenance date verification...")
        
        parts = Part.query.all()
        updated_count = 0
        
        for part in parts:
            # Get latest completion date from records
            latest_record = MaintenanceRecord.query.filter_by(
                part_id=part.id, 
                status='completed'
            ).order_by(MaintenanceRecord.date.desc()).first()
            
            if latest_record:
                # We have a record. Let's see if the part is in sync.
                # Re-calculate what the next_maintenance SHOULD be
                
                # Logic from Part.update_next_maintenance simulation
                completion_dt = latest_record.date
                if isinstance(completion_dt, date) and not isinstance(completion_dt, datetime):
                    completion_dt = datetime.combine(completion_dt, datetime.min.time())
                
                # We simply call the update method to force a re-calc based on this record
                # This respects cycle-based logic if implemented in the model
                old_next = part.next_maintenance
                
                part.update_next_maintenance(completed_at=completion_dt)
                
                if part.next_maintenance != old_next:
                    print(f"Fixed Part {part.id} ('{part.name}'): {old_next} -> {part.next_maintenance} (Based on record from {completion_dt})")
                    updated_count += 1
            else:
                # No maintenance records. 
                # Should we reset it? Or leave it? 
                # If it's overdue but has no records, it's genuinely overdue (never done).
                pass
        
        if updated_count > 0:
            db.session.commit()
            print(f"Successfully updated {updated_count} parts.")
        else:
            print("All parts appear to be in sync.")

if __name__ == "__main__":
    fix_maintenance_dates()
