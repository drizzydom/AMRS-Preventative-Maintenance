#!/usr/bin/env python3
"""Deep investigation of HCN Robot maintenance records"""
import sys
import os

# Suppress startup noise
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from app import app, db
from models import Machine, Part, MaintenanceRecord
from datetime import datetime, timedelta

with app.app_context():
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    two_weeks_ago = today - timedelta(days=14)
    
    sys.stdout.write("\n" + "="*60 + "\n")
    sys.stdout.write("=== SEARCHING FOR ALL HCN/Robot MACHINES ===\n")
    sys.stdout.write("="*60 + "\n\n")
    
    machines = Machine.query.filter(
        db.or_(
            Machine.name.ilike('%HCN%'),
            Machine.name.ilike('%Robot%')
        )
    ).all()
    
    for m in machines:
        sys.stdout.write(f"Machine ID {m.id}: '{m.name}' (Site ID: {m.site_id})\n")
    
    sys.stdout.write("\n" + "="*60 + "\n")
    sys.stdout.write("=== RECENT RECORDS (last 2 weeks) ===\n")
    sys.stdout.write("="*60 + "\n\n")
    
    recent_records = MaintenanceRecord.query.filter(
        MaintenanceRecord.date >= two_weeks_ago
    ).order_by(MaintenanceRecord.date.desc()).all()
    
    sys.stdout.write(f"Total records in last 2 weeks: {len(recent_records)}\n\n")
    
    for r in recent_records[:30]:
        part = db.session.get(Part, r.part_id)
        machine = db.session.get(Machine, r.machine_id) if r.machine_id else None
        part_machine = db.session.get(Machine, part.machine_id) if part else None
        
        sys.stdout.write(f"Record ID {r.id}:\n")
        sys.stdout.write(f"  Date: {r.date}\n")
        sys.stdout.write(f"  Part: {r.part_id} - {part.name if part else 'UNKNOWN'}\n")
        sys.stdout.write(f"  Record machine: {machine.name if machine else 'NONE'}\n")
        sys.stdout.write(f"  Part's machine: {part_machine.name if part_machine else 'N/A'}\n")
        if part:
            sys.stdout.write(f"  Part next_maintenance: {part.next_maintenance}\n")
        sys.stdout.write("\n")
    
    sys.stdout.write("\n" + "="*60 + "\n")
    sys.stdout.write("=== PARTS WITH 'Loading Station' IN NAME ===\n")
    sys.stdout.write("="*60 + "\n\n")
    
    loading_parts = Part.query.filter(Part.name.ilike('%Loading Station%')).all()
    
    for p in loading_parts:
        machine = db.session.get(Machine, p.machine_id)
        records = MaintenanceRecord.query.filter_by(part_id=p.id).order_by(MaintenanceRecord.date.desc()).all()
        
        sys.stdout.write(f"Part ID {p.id}: '{p.name}'\n")
        sys.stdout.write(f"  Machine: {machine.name if machine else 'UNKNOWN'} (ID: {p.machine_id})\n")
        sys.stdout.write(f"  next_maintenance: {p.next_maintenance}\n")
        sys.stdout.write(f"  last_maintenance: {p.last_maintenance}\n")
        sys.stdout.write(f"  Total records: {len(records)}\n")
        if records:
            sys.stdout.write(f"  Most recent record: {records[0].date}\n")
        sys.stdout.write("\n")
    
    sys.stdout.flush()
