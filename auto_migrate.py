from models import db
from sqlalchemy import inspect, text
from app import app

EXPECTED_SCHEMA = {
    'audit_tasks': {
        'interval': 'VARCHAR(20)',
        'custom_interval_days': 'INTEGER'
    },
    # Add other tables/columns as needed
}

def add_missing_columns(engine, table, columns):
    inspector = inspect(engine)
    existing_columns = [col['name'] for col in inspector.get_columns(table)]
    with engine.connect() as conn:
        for col, col_type in columns.items():
            if col not in existing_columns:
                print(f"Adding missing column {col} to {table}...")
                try:
                    conn.execute(text(f'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {col_type}'))
                except Exception as e:
                    print(f"Error adding column {col} to {table}: {e}")

def run_auto_migration():
    with app.app_context():
        db.create_all()
        for table, columns in EXPECTED_SCHEMA.items():
            add_missing_columns(db.engine, table, columns)
        print("Auto-migration complete.")

if __name__ == "__main__":
    run_auto_migration()
