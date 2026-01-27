#!/usr/bin/env python3
"""Diagnose overdue parts issue"""

from app import app, db
from models import Part, MaintenanceRecord
from datetime import datetime, timedelta

with app.app_context():
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    print(f'Today: {today}')
    print()
    
    # Get count of truly overdue vs correctly scheduled
    overdue_parts = Part.query.filter(Part.next_maintenance < today).all()
    print(f'Total parts with next_maintenance < today: {len(overdue_parts)}')
    print()
    
    # Check if these are LEGITIMATELY overdue (maintenance was done, but next due date passed)
    legit_overdue = 0
    needs_recalc = 0
    
    for part in overdue_parts[:10]:  # Sample first 10
        latest_record = MaintenanceRecord.query.filter_by(part_id=part.id).order_by(MaintenanceRecord.date.desc()).first()
        if latest_record:
            # Calculate what next_maintenance SHOULD be
            interval_days = part.maintenance_interval_days()
            expected_next = latest_record.date + timedelta(days=interval_days)
            
            print(f'Part {part.id}: {part.name}')
            print(f'  Interval: {interval_days} days ({part.maintenance_frequency} {part.maintenance_unit})')
            print(f'  Last record: {latest_record.date}')
            print(f'  Current next_maintenance: {part.next_maintenance}')
            print(f'  Expected next_maintenance: {expected_next}')
            print(f'  Expected is in future: {expected_next > today}')
            print()
            
            if expected_next > today:
                needs_recalc += 1
            else:
                legit_overdue += 1
    
    print(f'Sample results: {legit_overdue} legitimately overdue, {needs_recalc} need recalculation')
