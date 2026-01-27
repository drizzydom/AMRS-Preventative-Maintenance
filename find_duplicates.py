#!/usr/bin/env python3
"""Find duplicate parts on the same machine"""
import sys
from app import app, db
from models import Machine, Part
from sqlalchemy import func

with app.app_context():
    # Find parts with the same name on the same machine
    duplicates = db.session.query(
        Part.machine_id,
        Part.name,
        func.count(Part.id).label('count')
    ).group_by(Part.machine_id, Part.name).having(func.count(Part.id) > 1).all()
    
    sys.stdout.write("\n" + "="*60 + "\n")
    sys.stdout.write("=== DUPLICATE PARTS (same name on same machine) ===\n")
    sys.stdout.write("="*60 + "\n\n")
    
    sys.stdout.write(f"Found {len(duplicates)} duplicate part groups\n\n")
    
    for machine_id, part_name, count in duplicates[:20]:
        machine = db.session.get(Machine, machine_id)
        parts = Part.query.filter_by(machine_id=machine_id, name=part_name).all()
        
        sys.stdout.write(f"Machine: {machine.name if machine else 'Unknown'} (ID: {machine_id})\n")
        sys.stdout.write(f"Part Name: '{part_name}' - {count} duplicates\n")
        
        for p in parts:
            sys.stdout.write(f"  Part ID {p.id}: next={p.next_maintenance}, last={p.last_maintenance}\n")
        sys.stdout.write("\n")
    
    sys.stdout.flush()
