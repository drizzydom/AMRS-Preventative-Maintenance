
import os
from sqlalchemy import create_engine, text
import sys

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable is not set.")
    sys.exit(1)

def fix_schema():
    print("Connecting to online database...")
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            print("Connected.")
            
            # Check parts table
            print("Checking parts table...")
            try:
                conn.execute(text("SELECT maintenance_cycle_frequency FROM parts LIMIT 1"))
                print("parts.maintenance_cycle_frequency exists.")
            except Exception:
                conn.rollback()
                print("Adding maintenance_cycle_frequency to parts...")
                conn.execute(text("ALTER TABLE parts ADD COLUMN maintenance_cycle_frequency INTEGER"))
                conn.commit()

            try:
                conn.execute(text("SELECT last_maintenance_cycle FROM parts LIMIT 1"))
                print("parts.last_maintenance_cycle exists.")
            except Exception:
                conn.rollback()
                print("Adding last_maintenance_cycle to parts...")
                conn.execute(text("ALTER TABLE parts ADD COLUMN last_maintenance_cycle INTEGER DEFAULT 0"))
                conn.commit()

            try:
                conn.execute(text("SELECT next_maintenance_cycle FROM parts LIMIT 1"))
                print("parts.next_maintenance_cycle exists.")
            except Exception:
                conn.rollback()
                print("Adding next_maintenance_cycle to parts...")
                conn.execute(text("ALTER TABLE parts ADD COLUMN next_maintenance_cycle INTEGER"))
                conn.commit()

            # Check machines table
            print("Checking machines table...")
            try:
                conn.execute(text("SELECT cycle_count FROM machines LIMIT 1"))
                print("machines.cycle_count exists.")
            except Exception:
                conn.rollback()
                print("Adding cycle_count to machines...")
                conn.execute(text("ALTER TABLE machines ADD COLUMN cycle_count INTEGER DEFAULT 0"))
                conn.commit()

            try:
                conn.execute(text("SELECT last_cycle_update FROM machines LIMIT 1"))
                print("machines.last_cycle_update exists.")
            except Exception:
                conn.rollback()
                print("Adding last_cycle_update to machines...")
                conn.execute(text("ALTER TABLE machines ADD COLUMN last_cycle_update TIMESTAMP"))
                conn.commit()

            # Check maintenance_records table
            print("Checking maintenance_records table...")
            try:
                conn.execute(text("SELECT po_number FROM maintenance_records LIMIT 1"))
                print("maintenance_records.po_number exists.")
            except Exception:
                conn.rollback()
                print("Adding po_number to maintenance_records...")
                conn.execute(text("ALTER TABLE maintenance_records ADD COLUMN po_number VARCHAR(32)"))
                conn.commit()

            try:
                conn.execute(text("SELECT work_order_number FROM maintenance_records LIMIT 1"))
                print("maintenance_records.work_order_number exists.")
            except Exception:
                conn.rollback()
                print("Adding work_order_number to maintenance_records...")
                conn.execute(text("ALTER TABLE maintenance_records ADD COLUMN work_order_number VARCHAR(128)"))
                conn.commit()

            try:
                conn.execute(text("SELECT client_id FROM maintenance_records LIMIT 1"))
                print("maintenance_records.client_id exists.")
            except Exception:
                conn.rollback()
                print("Adding client_id to maintenance_records...")
                conn.execute(text("ALTER TABLE maintenance_records ADD COLUMN client_id VARCHAR(36)"))
                conn.commit()

            try:
                conn.execute(text("SELECT created_at FROM maintenance_records LIMIT 1"))
                print("maintenance_records.created_at exists.")
            except Exception:
                conn.rollback()
                print("Adding created_at to maintenance_records...")
                conn.execute(text("ALTER TABLE maintenance_records ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
                conn.commit()

            try:
                conn.execute(text("SELECT updated_at FROM maintenance_records LIMIT 1"))
                print("maintenance_records.updated_at exists.")
            except Exception:
                conn.rollback()
                print("Adding updated_at to maintenance_records...")
                conn.execute(text("ALTER TABLE maintenance_records ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
                conn.commit()

            print("Schema fix complete.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_schema()
