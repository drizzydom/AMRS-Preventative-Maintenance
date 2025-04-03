#!/usr/bin/env python3
"""
Update existing machines with default values for machine_number and serial_number.
Run this to populate empty fields for existing machines.
"""
from app import app, db, Machine

def update_existing_machines():
    with app.app_context():
        machines = Machine.query.all()
        updated_count = 0
        
        for machine in machines:
            updated = False
            
            if machine.machine_number is None:
                machine.machine_number = f"M{machine.id:04d}"
                updated = True
                
            if machine.serial_number is None:
                machine.serial_number = f"SN{machine.id}-{machine.name.replace(' ', '').upper()}"
                updated = True
                
            if updated:
                updated_count += 1
        
        if updated_count > 0:
            db.session.commit()
            print(f"Updated {updated_count} machines with default values")
        else:
            print("No machines needed updates")

if __name__ == "__main__":
    update_existing_machines()
