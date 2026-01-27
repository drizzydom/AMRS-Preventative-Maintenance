#!/usr/bin/env python3
"""
Consolidate duplicate parts on the same machine.

For each set of duplicates:
1. Keep the part with the most recent next_maintenance date
2. Move all maintenance records from duplicates to the kept part
3. Delete the duplicate parts
4. Queue all changes for sync to online server

Run with --dry-run first to see what would be changed.
"""
import sys
import argparse
from datetime import datetime

from app import app, db
from models import Machine, Part, MaintenanceRecord
from sqlalchemy import func

def find_duplicates():
    """Find all parts with same name on same machine."""
    return db.session.query(
        Part.machine_id,
        Part.name,
        func.count(Part.id).label('count')
    ).group_by(Part.machine_id, Part.name).having(func.count(Part.id) > 1).all()

def consolidate_duplicates(dry_run=True):
    """Consolidate duplicate parts."""
    from sync_utils_enhanced import add_to_sync_queue_enhanced
    
    duplicates = find_duplicates()
    
    print(f"\n{'='*60}")
    print(f"DUPLICATE PARTS CONSOLIDATION {'(DRY RUN)' if dry_run else '(LIVE)'}")
    print(f"{'='*60}\n")
    print(f"Found {len(duplicates)} duplicate groups to consolidate\n")
    
    total_records_moved = 0
    total_parts_deleted = 0
    sync_queue_additions = 0
    
    for machine_id, part_name, count in duplicates:
        # Get all parts with this name on this machine
        parts = Part.query.filter_by(machine_id=machine_id, name=part_name).all()
        machine = db.session.get(Machine, machine_id)
        
        # Determine which part to keep (most recent next_maintenance, or most recent last_maintenance)
        # This keeps the one that's been most recently updated
        parts_sorted = sorted(parts, key=lambda p: (
            p.next_maintenance or datetime.min,
            p.last_maintenance or datetime.min,
            p.id  # Fallback to highest ID (newest)
        ), reverse=True)
        
        keep_part = parts_sorted[0]
        delete_parts = parts_sorted[1:]
        
        print(f"Machine: {machine.name if machine else 'Unknown'}")
        print(f"Part: '{part_name}'")
        print(f"  KEEP Part ID {keep_part.id}: next={keep_part.next_maintenance}")
        
        for dup in delete_parts:
            # Count maintenance records on this duplicate
            records = MaintenanceRecord.query.filter_by(part_id=dup.id).all()
            record_count = len(records)
            
            print(f"  DELETE Part ID {dup.id}: next={dup.next_maintenance}, {record_count} records to move")
            
            if not dry_run:
                # Move maintenance records to the kept part
                for record in records:
                    old_part_id = record.part_id
                    record.part_id = keep_part.id
                    total_records_moved += 1
                    
                    # Queue the updated maintenance record for sync
                    add_to_sync_queue_enhanced(
                        'maintenance_records',
                        record.id,
                        'update',
                        {
                            'id': record.id,
                            'machine_id': record.machine_id,
                            'part_id': record.part_id,
                            'user_id': record.user_id,
                            'maintenance_type': record.maintenance_type,
                            'description': record.description,
                            'date': record.date.isoformat() if record.date else None,
                            'performed_by': record.performed_by,
                            'status': record.status,
                            'notes': record.notes,
                        },
                        immediate_sync=False  # Batch all changes
                    )
                    sync_queue_additions += 1
                
                # ========== SYNC: Queue the part deletion ==========
                # Add to sync queue BEFORE deleting so we have the data
                add_to_sync_queue_enhanced(
                    'parts',
                    dup.id,
                    'delete',  # This will trigger the delete handler on the server
                    {
                        'id': dup.id,
                        '__operation__': 'delete'  # Explicit operation marker
                    },
                    immediate_sync=False
                )
                sync_queue_additions += 1
                
                # Delete the duplicate part
                db.session.delete(dup)
                total_parts_deleted += 1
            else:
                total_records_moved += record_count
                total_parts_deleted += 1
        
        # ========== Update the kept part's next_maintenance from its records ==========
        if not dry_run:
            keep_part.update_next_maintenance()
            add_to_sync_queue_enhanced(
                'parts',
                keep_part.id,
                'update',
                {
                    'id': keep_part.id,
                    'name': keep_part.name,
                    'description': keep_part.description,
                    'machine_id': keep_part.machine_id,
                    'maintenance_frequency': keep_part.maintenance_frequency,
                    'maintenance_unit': keep_part.maintenance_unit,
                    'last_maintenance': keep_part.last_maintenance.isoformat() if keep_part.last_maintenance else None,
                    'next_maintenance': keep_part.next_maintenance.isoformat() if keep_part.next_maintenance else None,
                },
                immediate_sync=False
            )
            sync_queue_additions += 1
        
        print()
    
    if not dry_run:
        db.session.commit()
        print(f"\n{'='*60}")
        print("CONSOLIDATION COMPLETE")
        print(f"{'='*60}")
        print(f"Records moved: {total_records_moved}")
        print(f"Duplicate parts deleted: {total_parts_deleted}")
        print(f"Sync queue entries added: {sync_queue_additions}")
        print("\n*** Changes have been queued for sync to the online server ***")
        print("The next sync cycle will propagate these changes.")
    else:
        print(f"\n{'='*60}")
        print("DRY RUN SUMMARY (no changes made)")
        print(f"{'='*60}")
        print(f"Records that would be moved: {total_records_moved}")
        print(f"Duplicate parts that would be deleted: {total_parts_deleted}")
        print("\nRun with --apply to make these changes.")

def main():
    parser = argparse.ArgumentParser(description='Consolidate duplicate parts')
    parser.add_argument('--apply', action='store_true', help='Actually apply changes (default is dry-run)')
    args = parser.parse_args()
    
    with app.app_context():
        consolidate_duplicates(dry_run=not args.apply)

if __name__ == '__main__':
    main()
