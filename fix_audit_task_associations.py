#!/usr/bin/env python3
"""
Fix audit task associations by linking tasks to machines at their respective sites
"""

from app import app
from models import db, AuditTask, Machine, Site
from sqlalchemy import text

def fix_audit_task_associations():
    """Associate all audit tasks with all machines at their respective sites"""
    
    print("=== Fixing Audit Task Associations ===")
    
    with app.app_context():
        # Get all audit tasks
        tasks = AuditTask.query.all()
        print(f"Found {len(tasks)} audit tasks")
        
        associations_added = 0
        
        for task in tasks:
            print(f"\nProcessing Task {task.id}: {task.name}")
            
            if not task.site_id:
                print(f"  ⚠️  Task has no site_id, skipping")
                continue
            
            # Get site info
            site = Site.query.get(task.site_id)
            site_name = site.name if site else "Unknown"
            print(f"  📍 Site: {site_name}")
            
            # Get all machines at this site
            machines_at_site = Machine.query.filter_by(site_id=task.site_id).all()
            print(f"  🏭 Found {len(machines_at_site)} machines at this site")
            
            # Get currently associated machines
            current_associations = len(task.machines)
            print(f"  🔗 Currently associated with {current_associations} machines")
            
            if current_associations == len(machines_at_site):
                print(f"  ✅ Already fully associated, skipping")
                continue
            
            # Associate with all machines at the site
            for machine in machines_at_site:
                if machine not in task.machines:
                    print(f"    ➕ Adding association: Task '{task.name}' -> Machine '{machine.name}'")
                    task.machines.append(machine)
                    associations_added += 1
                else:
                    print(f"    ✅ Already associated: Task '{task.name}' -> Machine '{machine.name}'")
        
        # Commit all changes
        if associations_added > 0:
            print(f"\n💾 Committing {associations_added} new associations...")
            db.session.commit()
            print("✅ Successfully committed all associations!")
        else:
            print("\n✅ No new associations needed")
        
        # Verify final state
        print("\n=== Final State Verification ===")
        result = db.session.execute(text('SELECT COUNT(*) FROM machine_audit_task'))
        total_associations = result.fetchone()[0]
        print(f"Total machine_audit_task associations: {total_associations}")
        
        # Show all associations
        result = db.session.execute(text('''
            SELECT at.name as task_name, m.name as machine_name, s.name as site_name
            FROM machine_audit_task mat
            JOIN audit_tasks at ON mat.audit_task_id = at.id
            JOIN machines m ON mat.machine_id = m.id
            JOIN sites s ON at.site_id = s.id
            ORDER BY at.name, m.name
        '''))
        
        associations = result.fetchall()
        print(f"\nAll associations:")
        current_task = None
        for assoc in associations:
            if assoc[0] != current_task:
                print(f"\n🔧 {assoc[0]} ({assoc[2]} site):")
                current_task = assoc[0]
            print(f"  └── {assoc[1]}")
        
        print(f"\n🎉 Process completed! Added {associations_added} new associations.")

if __name__ == "__main__":
    fix_audit_task_associations()
