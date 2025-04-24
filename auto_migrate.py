from models import db
from sqlalchemy import inspect, text

def add_column_if_not_exists(engine, table, column, coltype):
    inspector = inspect(engine)
    existing_columns = [col['name'] for col in inspector.get_columns(table)]
    if column not in existing_columns:
        with engine.connect() as conn:
            try:
                conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {column} {coltype}'))
                print(f"[AUTO_MIGRATE] Added column {column} to {table}")
            except Exception as e:
                print(f"[AUTO_MIGRATE] Error adding column {column} to {table}: {e}")

def run_auto_migration():
    from app import app  # Import here to avoid circular import
    with app.app_context():
        db.create_all()
        engine = db.engine
        # Ensure audit_tasks columns
        add_column_if_not_exists(engine, 'audit_tasks', 'interval', "VARCHAR(20) DEFAULT 'daily'")
        add_column_if_not_exists(engine, 'audit_tasks', 'custom_interval_days', "INTEGER")
        # Add more columns/tables as needed here
        print("[AUTO_MIGRATE] Auto-migration complete.")

if __name__ == "__main__":
    run_auto_migration()
