#!/usr/bin/env python3
"""Investigate HCN Robot machine maintenance records"""

from app import app, db
from models import Machine, Part, MaintenanceRecord
from datetime import datetime

with app.app_context():
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Find the HCN Robot machine
    machine = Machine.query.filter(Machine.name.ilike('%HCN Robot%')).first()
    if not machine:
        print('Machine "HCN Robot" not found, searching for similar names...')
        machines = Machine.query.filter(Machine.name.ilike('%HCN%')).all()
        for m in machines:
            print(f'  Found: {m.id} - {m.name}')
        if machines:
            machine = machines[0]
            print(f'\nUsing first match: {machine.name}')
    
    if machine:
        print(f'\n=== Machine: {machine.id} - {machine.name} ===\n')
        
        # Get all parts for this machine
        parts = Part.query.filter_by(machine_id=machine.id).all()
        print(f'Total parts for this machine: {len(parts)}')
        
        overdue_parts = [p for p in parts if p.next_maintenance and p.next_maintenance < today]
        print(f'Parts showing as OVERDUE: {len(overdue_parts)}')
        print()
        
        # For each overdue part, check maintenance records
        print('=== OVERDUE PARTS ANALYSIS ===\n')
        for part in overdue_parts[:15]:
            print(f'Part {part.id}: {part.name}')
            print(f'  next_maintenance: {part.next_maintenance}')
            print(f'  last_maintenance: {part.last_maintenance}')
            
            # Get ALL maintenance records for this part
            records = MaintenanceRecord.query.filter_by(part_id=part.id).order_by(MaintenanceRecord.date.desc()).all()
            print(f'  Total maintenance records: {len(records)}')
            if records:
                latest = records[0]
                print(f'  Latest record: {latest.date} (status: {latest.status})')
                
                # Check if latest record is AFTER next_maintenance (meaning update didn't happen)
                if latest.date > part.next_maintenance:
                    print(f'  *** BUG: Latest record ({latest.date}) is NEWER than next_maintenance ({part.next_maintenance})! ***')
            print()
