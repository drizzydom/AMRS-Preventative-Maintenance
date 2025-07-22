#!/usr/bin/env python3
"""
Manual audit task association fixer for both online and offline databases
This script creates the missing machine_audit_task associations until the sync endpoint is fixed
"""

import os
import sqlite3
from sqlalchemy import create_engine, text

def fix_online_database():
    """Fix associations in the online PostgreSQL database"""
    print("=== Fixing Online Database (PostgreSQL) ===")
    
    DATABASE_URL = 'postgresql://maintenance_tracking_8sbx_user:E3EMwngxsgOAZWacbUPjZpcmwhouHIL4@dpg-d07sa0hr0fns73du2kfg-a.ohio-postgres.render.com/maintenance_tracking_8sbx'
    
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Check current state
            result = conn.execute(text('SELECT COUNT(*) FROM machine_audit_task'))
            current_count = result.fetchone()[0]
            print(f"Current online associations: {current_count}")
            
            if current_count >= 18:
                print("✅ Online database already has sufficient associations")
                return True
            
            # Get all audit tasks and machines at Demo site
            result = conn.execute(text('''
                SELECT at.id as task_id, m.id as machine_id, at.name as task_name, m.name as machine_name
                FROM audit_tasks at
                JOIN sites s ON at.site_id = s.id
                CROSS JOIN machines m 
                WHERE s.name = 'Demo' AND m.site_id = s.id
                AND NOT EXISTS (
                    SELECT 1 FROM machine_audit_task mat 
                    WHERE mat.audit_task_id = at.id AND mat.machine_id = m.id
                )
            '''))
            
            missing_associations = result.fetchall()
            print(f"Found {len(missing_associations)} missing associations to create")
            
            # Create the missing associations
            for assoc in missing_associations:
                conn.execute(text('''
                    INSERT INTO machine_audit_task (audit_task_id, machine_id) 
                    VALUES (:task_id, :machine_id)
                '''), {'task_id': assoc[0], 'machine_id': assoc[1]})
                print(f"  ➕ {assoc[2]} -> {assoc[3]}")
            
            conn.commit()
            
            # Verify final count
            result = conn.execute(text('SELECT COUNT(*) FROM machine_audit_task'))
            final_count = result.fetchone()[0]
            print(f"✅ Online database now has {final_count} associations")
            return True
            
    except Exception as e:
        print(f"❌ Error fixing online database: {e}")
        return False

def fix_offline_database():
    """Fix associations in the offline SQLite database"""
    print("\n=== Fixing Offline Database (SQLite) ===")
    
    db_path = 'maintenance.db'
    
    if not os.path.exists(db_path):
        print(f"❌ SQLite database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current state
        cursor.execute('SELECT COUNT(*) FROM machine_audit_task')
        current_count = cursor.fetchone()[0]
        print(f"Current offline associations: {current_count}")
        
        if current_count >= 18:
            print("✅ Offline database already has sufficient associations")
            return True
        
        # Clear existing associations to start fresh
        cursor.execute('DELETE FROM machine_audit_task')
        
        # Get all audit tasks and machines at Demo site  
        cursor.execute('''
            SELECT at.id as task_id, m.id as machine_id, at.name as task_name, m.name as machine_name
            FROM audit_tasks at
            JOIN sites s ON at.site_id = s.id
            CROSS JOIN machines m 
            WHERE s.name = 'Demo' AND m.site_id = s.id
            AND m.name IN ('Demo 1', 'Demo 2', 'Demo 3')
        ''')
        
        associations_to_create = cursor.fetchall()
        print(f"Creating {len(associations_to_create)} associations")
        
        # Create the associations
        for assoc in associations_to_create:
            cursor.execute('''
                INSERT INTO machine_audit_task (audit_task_id, machine_id) 
                VALUES (?, ?)
            ''', (assoc[0], assoc[1]))
            print(f"  ➕ {assoc[2]} -> {assoc[3]}")
        
        conn.commit()
        
        # Verify final count
        cursor.execute('SELECT COUNT(*) FROM machine_audit_task')
        final_count = cursor.fetchone()[0]
        print(f"✅ Offline database now has {final_count} associations")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error fixing offline database: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Manual Audit Task Association Fixer")
    print("This creates the missing associations until the sync endpoint is deployed\n")
    
    # Fix online database first
    online_success = fix_online_database()
    
    # Fix offline database
    offline_success = fix_offline_database()
    
    print(f"\n{'='*50}")
    print(f"Online Database: {'✅ Fixed' if online_success else '❌ Failed'}")
    print(f"Offline Database: {'✅ Fixed' if offline_success else '❌ Failed'}")
    
    if online_success and offline_success:
        print("\n🎉 Both databases fixed! Your audit tasks should now display correctly.")
        print("📝 Note: Once the sync endpoint is properly deployed, these manual fixes won't be needed.")
    else:
        print("\n⚠️  Some fixes failed. Check the errors above and try again.")
