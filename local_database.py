import logging
import threading
from pathlib import Path
import uuid
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

try:
    from pysqlcipher3 import dbapi2 as sqlite3
    logger.info("Using pysqlcipher3 for local database.")
except ImportError:
    logger.warning("pysqlcipher3 not found. Falling back to standard sqlite3. ENCRYPTION WILL NOT WORK.")
    import sqlite3 # Standard library

# Thread-local storage for database connections
local_data = threading.local()

def get_db_connection(db_path: Path, encryption_key: str):
    """
    Establishes a connection to the encrypted SQLite database.
    Uses thread-local storage to reuse connections within the same thread.
    """
    if not hasattr(local_data, 'connection') or local_data.connection is None:
        try:
            conn = sqlite3.connect(str(db_path), check_same_thread=False)
            conn.execute(f"PRAGMA key = '{encryption_key}';")
            conn.execute("SELECT count(*) FROM sqlite_master;")
            conn.row_factory = sqlite3.Row
            local_data.connection = conn
            logger.info(f"Successfully connected to encrypted database: {db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to or decrypt database {db_path}: {e}")
            local_data.connection = None
            raise
    return local_data.connection

def close_db_connection():
    """Closes the thread-local database connection if it exists."""
    if hasattr(local_data, 'connection') and local_data.connection is not None:
        local_data.connection.close()
        local_data.connection = None
        logger.info("Closed thread-local database connection.")

def execute_query(db_path: Path, encryption_key: str, query: str, params=()):
    conn = get_db_connection(db_path, encryption_key)
    if not conn: return None
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        conn.commit()
        return cursor
    except Exception as e:
        logger.error(f"Error executing query: {query} with params {params} - {e}")
        conn.rollback()
        return None

def fetch_all(db_path: Path, encryption_key: str, query: str, params=()):
    cursor = execute_query(db_path, encryption_key, query, params)
    return [dict(row) for row in cursor.fetchall()] if cursor else []

def fetch_one(db_path: Path, encryption_key: str, query: str, params=()):
    cursor = execute_query(db_path, encryption_key, query, params)
    row = cursor.fetchone()
    return dict(row) if row else None

def create_tables(db_path: Path, encryption_key: str):
    conn = get_db_connection(db_path, encryption_key)
    if not conn:
        logger.error("Cannot create tables, database connection failed.")
        return

    cursor = conn.cursor()

    tables_sql = [
        """
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id INTEGER UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            permissions TEXT,
            is_synced INTEGER DEFAULT 1,
            last_modified TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT UNIQUE,
            server_id INTEGER UNIQUE,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            full_name TEXT,
            role_id INTEGER,
            is_synced INTEGER DEFAULT 0,
            last_modified TEXT,
            FOREIGN KEY (role_id) REFERENCES roles (id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT UNIQUE,
            server_id INTEGER UNIQUE,
            name TEXT NOT NULL,
            location TEXT,
            contact_email TEXT,
            enable_notifications INTEGER DEFAULT 1,
            notification_threshold INTEGER DEFAULT 30,
            is_synced INTEGER DEFAULT 0,
            last_modified TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS machines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT UNIQUE,
            server_id INTEGER UNIQUE,
            name TEXT NOT NULL,
            model TEXT,
            machine_number TEXT,
            serial_number TEXT,
            site_id INTEGER NOT NULL,
            is_synced INTEGER DEFAULT 0,
            last_modified TEXT,
            FOREIGN KEY (site_id) REFERENCES sites (id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT UNIQUE,
            server_id INTEGER UNIQUE,
            name TEXT NOT NULL,
            description TEXT,
            machine_id INTEGER NOT NULL,
            maintenance_frequency INTEGER DEFAULT 30,
            maintenance_unit TEXT DEFAULT 'day',
            maintenance_days INTEGER DEFAULT 30,
            last_maintenance TEXT,
            next_maintenance TEXT,
            is_synced INTEGER DEFAULT 0,
            last_modified TEXT,
            FOREIGN KEY (machine_id) REFERENCES machines (id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS maintenance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id INTEGER UNIQUE,
            part_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            machine_id INTEGER,
            date TEXT NOT NULL,
            comments TEXT,
            maintenance_type TEXT,
            description TEXT,
            performed_by TEXT,
            status TEXT,
            notes TEXT,
            client_id TEXT UNIQUE NOT NULL,
            is_synced INTEGER DEFAULT 0,
            last_modified TEXT,
            FOREIGN KEY (part_id) REFERENCES parts (id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (machine_id) REFERENCES machines (id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS audit_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT UNIQUE,
            server_id INTEGER UNIQUE,
            name TEXT NOT NULL,
            description TEXT,
            site_id INTEGER NOT NULL,
            created_by INTEGER,
            interval TEXT DEFAULT 'daily',
            custom_interval_days INTEGER,
            color TEXT,
            is_synced INTEGER DEFAULT 0,
            last_modified TEXT,
            FOREIGN KEY (site_id) REFERENCES sites (id),
            FOREIGN KEY (created_by) REFERENCES users (id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS audit_task_completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT UNIQUE,
            server_id INTEGER UNIQUE,
            audit_task_id INTEGER NOT NULL,
            machine_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            completed_by INTEGER,
            completed_at TEXT,
            is_synced INTEGER DEFAULT 0,
            last_modified TEXT,
            FOREIGN KEY (audit_task_id) REFERENCES audit_tasks (id),
            FOREIGN KEY (machine_id) REFERENCES machines (id),
            FOREIGN KEY (completed_by) REFERENCES users (id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS sync_metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """
    ]

    try:
        for table_sql in tables_sql:
            cursor.execute(table_sql)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_roles_server_id ON roles(server_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_server_id ON users(server_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_client_id ON users(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_role_id ON users(role_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sites_server_id ON sites(server_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sites_client_id ON sites(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_machines_server_id ON machines(server_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_machines_client_id ON machines(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_machines_site_id ON machines(site_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_parts_server_id ON parts(server_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_parts_client_id ON parts(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_parts_machine_id ON parts(machine_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_maintenance_records_server_id ON maintenance_records(server_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_maintenance_records_client_id ON maintenance_records(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_maintenance_records_part_id ON maintenance_records(part_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_maintenance_records_user_id ON maintenance_records(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_maintenance_records_machine_id ON maintenance_records(machine_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_maintenance_records_is_synced ON maintenance_records(is_synced)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_tasks_server_id ON audit_tasks(server_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_tasks_client_id ON audit_tasks(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_tasks_site_id ON audit_tasks(site_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_tasks_created_by ON audit_tasks(created_by)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_task_completions_server_id ON audit_task_completions(server_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_task_completions_client_id ON audit_task_completions(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_task_completions_audit_task_id ON audit_task_completions(audit_task_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_task_completions_machine_id ON audit_task_completions(machine_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_task_completions_completed_by ON audit_task_completions(completed_by)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_task_completions_is_synced ON audit_task_completions(is_synced)")

        conn.commit()
        logger.info("Local database tables created/ensured successfully with sync columns and indexes.")
    except Exception as e:
        logger.error(f"Error creating local database tables: {e}")
        conn.rollback()

# --- Functions for creating client-originated records ---

def create_local_maintenance_record(db_path: Path, encryption_key: str, data: dict) -> str | None:
    """Creates a new maintenance record locally, originating from the client.
    Expects FKs (part_id, user_id, machine_id) to be local IDs already.
    Returns the client_id of the newly created record or None on failure.
    """
    conn = get_db_connection(db_path, encryption_key)
    cursor = conn.cursor()
    client_id = _generate_client_id()
    current_ts = _get_current_timestamp_iso()

    insert_query = """
    INSERT INTO maintenance_records 
        (part_id, user_id, machine_id, date, comments, maintenance_type, description, 
         performed_by, status, notes, client_id, is_synced, last_modified)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?);
    """
    try:
        cursor.execute(insert_query, (
            data.get('part_id'), data.get('user_id'), data.get('machine_id'), data.get('date'),
            data.get('comments'), data.get('maintenance_type'), data.get('description'),
            data.get('performed_by'), data.get('status'), data.get('notes'),
            client_id, current_ts
        ))
        conn.commit()
        logger.info(f"Created new local maintenance record with client_id: {client_id}")
        return client_id
    except Exception as e:
        logger.error(f"Error creating local maintenance record: {e}")
        conn.rollback()
        return None

def update_local_maintenance_record(db_path: Path, encryption_key: str, client_id: str, update_data: dict) -> bool:
    """Updates an existing local maintenance record identified by its client_id.
    Sets is_synced to 0 and updates last_modified.
    Returns True on success, False on failure.
    """
    conn = get_db_connection(db_path, encryption_key)
    cursor = conn.cursor()
    current_ts = _get_current_timestamp_iso()

    allowed_fields = ['part_id', 'user_id', 'machine_id', 'date', 'comments', 
                      'maintenance_type', 'description', 'performed_by', 'status', 'notes']
    
    set_clauses = []
    params = []

    for field in allowed_fields:
        if field in update_data:
            set_clauses.append(f"{field} = ?")
            params.append(update_data[field])
    
    if not set_clauses:
        logger.warning(f"No valid fields provided for updating maintenance record with client_id: {client_id}")
        return False

    set_clauses.append("is_synced = 0")
    set_clauses.append("last_modified = ?")
    params.append(current_ts)
    params.append(client_id)

    update_query = f"UPDATE maintenance_records SET {', '.join(set_clauses)} WHERE client_id = ?"

    try:
        cursor.execute(update_query, tuple(params))
        conn.commit()
        if cursor.rowcount > 0:
            logger.info(f"Updated local maintenance record with client_id: {client_id}")
            return True
        else:
            logger.warning(f"No maintenance record found with client_id: {client_id} to update.")
            return False
    except Exception as e:
        logger.error(f"Error updating local maintenance record (client_id: {client_id}): {e}")
        conn.rollback()
        return False

def create_local_audit_task_completion(db_path: Path, encryption_key: str, data: dict) -> str | None:
    """Creates a new audit task completion locally, originating from the client.
    Expects FKs (audit_task_id, machine_id, completed_by) to be local IDs already.
    Returns the client_id of the newly created record or None on failure.
    """
    conn = get_db_connection(db_path, encryption_key)
    cursor = conn.cursor()
    client_id = _generate_client_id()
    current_ts = _get_current_timestamp_iso()

    insert_query = """
    INSERT INTO audit_task_completions
        (audit_task_id, machine_id, date, completed, completed_by, completed_at, 
         client_id, is_synced, last_modified)
    VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?);
    """
    try:
        cursor.execute(insert_query, (
            data.get('audit_task_id'), data.get('machine_id'), data.get('date'),
            data.get('completed', 0), data.get('completed_by'), data.get('completed_at'),
            client_id, current_ts
        ))
        conn.commit()
        logger.info(f"Created new local audit task completion with client_id: {client_id}")
        return client_id
    except Exception as e:
        logger.error(f"Error creating local audit task completion: {e}")
        conn.rollback()
        return None

def update_local_audit_task_completion(db_path: Path, encryption_key: str, client_id: str, update_data: dict) -> bool:
    """Updates an existing local audit task completion identified by its client_id.
    Sets is_synced to 0 and updates last_modified.
    Returns True on success, False on failure.
    """
    conn = get_db_connection(db_path, encryption_key)
    cursor = conn.cursor()
    current_ts = _get_current_timestamp_iso()

    allowed_fields = ['audit_task_id', 'machine_id', 'date', 'completed', 
                      'completed_by', 'completed_at'] # 'notes' is not in local schema yet

    set_clauses = []
    params = []

    for field in allowed_fields:
        if field in update_data:
            set_clauses.append(f"{field} = ?")
            params.append(update_data[field])

    if not set_clauses:
        logger.warning(f"No valid fields provided for updating audit task completion with client_id: {client_id}")
        return False

    set_clauses.append("is_synced = 0")
    set_clauses.append("last_modified = ?")
    params.append(current_ts)
    params.append(client_id)

    update_query = f"UPDATE audit_task_completions SET {', '.join(set_clauses)} WHERE client_id = ?"

    try:
        cursor.execute(update_query, tuple(params))
        conn.commit()
        if cursor.rowcount > 0:
            logger.info(f"Updated local audit task completion with client_id: {client_id}")
            return True
        else:
            logger.warning(f"No audit task completion found with client_id: {client_id} to update.")
            return False
    except Exception as e:
        logger.error(f"Error updating local audit task completion (client_id: {client_id}): {e}")
        conn.rollback()
        return False

# --- Functions for reading local data for UI --- 

def get_all_local_records(db_path: Path, encryption_key: str, table_name: str, order_by: str | None = None) -> list[dict]:
    """Fetches all records from a specified local table."""
    query = f"SELECT * FROM {table_name}"
    if order_by:
        query += f" ORDER BY {order_by}"
    return fetch_all(db_path, encryption_key, query)

def get_local_records_by_fk(db_path: Path, encryption_key: str, table_name: str, fk_column: str, fk_value: int, order_by: str | None = None) -> list[dict]:
    """Fetches records from a local table based on a foreign key value."""
    query = f"SELECT * FROM {table_name} WHERE {fk_column} = ?"
    if order_by:
        query += f" ORDER BY {order_by}"
    return fetch_all(db_path, encryption_key, query, (fk_value,))

def get_last_sync_timestamp(db_path: Path, encryption_key: str):
    conn = get_db_connection(db_path, encryption_key)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM sync_metadata WHERE key = 'last_sync_timestamp'")
    row = cursor.fetchone()
    return row[0] if row else None

def update_last_sync_timestamp(db_path: Path, encryption_key: str, timestamp_str: str):
    conn = get_db_connection(db_path, encryption_key)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO sync_metadata (key, value) VALUES ('last_sync_timestamp', ?)", (timestamp_str,))
    conn.commit()
    logger.info(f"Last sync timestamp updated to: {timestamp_str}")

def _generate_client_id():
    return str(uuid.uuid4())

def _get_current_timestamp_iso():
    return datetime.now(timezone.utc).isoformat()

def get_local_id_from_server_id(db_path: Path, encryption_key: str, table_name: str, server_id_value: int):
    """Helper function to get local ID from server ID."""
    if server_id_value is None:
        return None
    query = f"SELECT id FROM {table_name} WHERE server_id = ?"
    conn = get_db_connection(db_path, encryption_key)
    if not conn: return None
    cursor = conn.cursor()
    try:
        cursor.execute(query, (server_id_value,))
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
        logger.error(f"Error fetching local id for server_id {server_id_value} from {table_name}: {e}")
        return None

def upsert_role_from_server(db_path: Path, encryption_key: str, role_data: dict):
    conn = get_db_connection(db_path, encryption_key)
    cursor = conn.cursor()
    server_id = role_data.get('id')
    if not server_id:
        logger.warning(f"Skipping role data, missing server_id (id field): {role_data}")
        return

    current_ts = _get_current_timestamp_iso()
    
    local_role_id = get_local_id_from_server_id(db_path, encryption_key, 'roles', server_id)

    if local_role_id:
        update_query = """
        UPDATE roles SET name=?, description=?, permissions=?, is_synced=1, last_modified=?
        WHERE id=?
        """
        cursor.execute(update_query, (
            role_data.get('name'), role_data.get('description'), role_data.get('permissions'),
            current_ts, local_role_id
        ))
        logger.info(f"Updated role with server_id: {server_id} (local_id: {local_role_id})")
    else:
        insert_query = """
        INSERT INTO roles (server_id, name, description, permissions, is_synced, last_modified)
        VALUES (?, ?, ?, ?, 1, ?)
        """
        cursor.execute(insert_query, (
            server_id, role_data.get('name'), role_data.get('description'),
            role_data.get('permissions'), current_ts
        ))
        logger.info(f"Inserted new role with server_id: {server_id}")
    conn.commit()

def upsert_user_from_server(db_path: Path, encryption_key: str, user_data: dict):
    conn = get_db_connection(db_path, encryption_key)
    cursor = conn.cursor()
    server_id = user_data.get('id')
    if not server_id:
        logger.warning(f"Skipping user data, missing server_id (id field): {user_data}")
        return

    server_role_id = user_data.get('role_id')
    local_role_id = None
    if server_role_id is not None:
        local_role_id = get_local_id_from_server_id(db_path, encryption_key, 'roles', server_role_id)
        if local_role_id is None:
            logger.warning(f"Could not find local role for server_role_id: {server_role_id}. User server_id: {server_id} will have NULL role_id.")

    local_user_id = get_local_id_from_server_id(db_path, encryption_key, 'users', server_id)
    current_ts = _get_current_timestamp_iso()

    if local_user_id:
        update_query = """
        UPDATE users SET username=?, email=?, full_name=?, role_id=?, is_synced=1, last_modified=?
        WHERE id=?
        """
        cursor.execute(update_query, (
            user_data.get('username'), user_data.get('email'), user_data.get('full_name'),
            local_role_id, current_ts, local_user_id
        ))
        logger.info(f"Updated user with server_id: {server_id} (local_id: {local_user_id})")
    else:
        client_id = _generate_client_id()
        insert_query = """
        INSERT INTO users (client_id, server_id, username, email, full_name, role_id, is_synced, last_modified)
        VALUES (?, ?, ?, ?, ?, ?, 1, ?)
        """
        cursor.execute(insert_query, (
            client_id, server_id, user_data.get('username'), user_data.get('email'),
            user_data.get('full_name'), local_role_id, current_ts
        ))
        logger.info(f"Inserted new user with server_id: {server_id}")
    conn.commit()

def upsert_site_from_server(db_path: Path, encryption_key: str, site_data: dict):
    conn = get_db_connection(db_path, encryption_key)
    cursor = conn.cursor()
    server_id = site_data.get('id')
    if not server_id:
        logger.warning(f"Skipping site data, missing server_id: {site_data}")
        return

    local_site_id = get_local_id_from_server_id(db_path, encryption_key, 'sites', server_id)
    current_ts = _get_current_timestamp_iso()

    if local_site_id:
        update_query = """
        UPDATE sites SET name=?, location=?, contact_email=?, enable_notifications=?, notification_threshold=?, is_synced=1, last_modified=?
        WHERE id=?
        """
        cursor.execute(update_query, (
            site_data.get('name'), site_data.get('location'), site_data.get('contact_email'),
            site_data.get('enable_notifications', 1), site_data.get('notification_threshold', 30),
            current_ts, local_site_id
        ))
        logger.info(f"Updated site with server_id: {server_id}")
    else:
        client_id = _generate_client_id()
        insert_query = """
        INSERT INTO sites (client_id, server_id, name, location, contact_email, enable_notifications, notification_threshold, is_synced, last_modified)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
        """
        cursor.execute(insert_query, (
            client_id, server_id, site_data.get('name'), site_data.get('location'), site_data.get('contact_email'),
            site_data.get('enable_notifications', 1), site_data.get('notification_threshold', 30), current_ts
        ))
        logger.info(f"Inserted new site with server_id: {server_id}")
    conn.commit()

def upsert_machine_from_server(db_path: Path, encryption_key: str, machine_data: dict):
    conn = get_db_connection(db_path, encryption_key)
    cursor = conn.cursor()
    server_id = machine_data.get('id') # Server's Machine ID
    if not server_id:
        logger.warning(f"Skipping machine data, missing server_id (id field): {machine_data}")
        return

    server_site_id = machine_data.get('site_id')
    local_site_id = None
    if server_site_id is not None:
        local_site_id = get_local_id_from_server_id(db_path, encryption_key, 'sites', server_site_id)
        if local_site_id is None:
            logger.warning(f"Could not find local site for server_site_id: {server_site_id}. Machine server_id: {server_id} will have NULL site_id or fail if site_id is NOT NULL.")

    local_machine_id = get_local_id_from_server_id(db_path, encryption_key, 'machines', server_id)
    current_ts = _get_current_timestamp_iso()

    if local_machine_id:
        update_query = """
        UPDATE machines SET name=?, model=?, machine_number=?, serial_number=?, site_id=?, 
                       is_synced=1, last_modified=?
        WHERE id=?
        """
        cursor.execute(update_query, (
            machine_data.get('name'), machine_data.get('model'), machine_data.get('machine_number'),
            machine_data.get('serial_number'), local_site_id,
            current_ts, local_machine_id
        ))
        logger.info(f"Updated machine with server_id: {server_id} (local_id: {local_machine_id})")
    else:
        client_id = _generate_client_id()
        insert_query = """
        INSERT INTO machines (client_id, server_id, name, model, machine_number, serial_number, site_id, 
                              is_synced, last_modified)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
        """
        cursor.execute(insert_query, (
            client_id, server_id, machine_data.get('name'), machine_data.get('model'), 
            machine_data.get('machine_number'), machine_data.get('serial_number'), local_site_id,
            current_ts
        ))
        logger.info(f"Inserted new machine with server_id: {server_id}")
    conn.commit()

def upsert_part_from_server(db_path: Path, encryption_key: str, part_data: dict):
    conn = get_db_connection(db_path, encryption_key)
    cursor = conn.cursor()
    server_id = part_data.get('id') # Server's Part ID
    if not server_id:
        logger.warning(f"Skipping part data, missing server_id (id field): {part_data}")
        return

    server_machine_id = part_data.get('machine_id')
    local_machine_id = None
    if server_machine_id is not None:
        local_machine_id = get_local_id_from_server_id(db_path, encryption_key, 'machines', server_machine_id)
        if local_machine_id is None:
            logger.warning(f"Could not find local machine for server_machine_id: {server_machine_id}. Part server_id: {server_id} will have NULL machine_id or fail.")

    local_part_id = get_local_id_from_server_id(db_path, encryption_key, 'parts', server_id)
    current_ts = _get_current_timestamp_iso()

    if local_part_id:
        update_query = """
        UPDATE parts SET name=?, description=?, machine_id=?, maintenance_frequency=?, 
                       maintenance_unit=?, maintenance_days=?, last_maintenance=?, next_maintenance=?, 
                       is_synced=1, last_modified=?
        WHERE id=?
        """
        cursor.execute(update_query, (
            part_data.get('name'), part_data.get('description'), local_machine_id,
            part_data.get('maintenance_frequency'), part_data.get('maintenance_unit'),
            part_data.get('maintenance_days'), part_data.get('last_maintenance'),
            part_data.get('next_maintenance'), current_ts, local_part_id
        ))
        logger.info(f"Updated part with server_id: {server_id} (local_id: {local_part_id})")
    else:
        client_id = _generate_client_id()
        insert_query = """
        INSERT INTO parts (client_id, server_id, name, description, machine_id, maintenance_frequency, 
                           maintenance_unit, maintenance_days, last_maintenance, next_maintenance, 
                           is_synced, last_modified)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        """
        cursor.execute(insert_query, (
            client_id, server_id, part_data.get('name'), part_data.get('description'), 
            local_machine_id, part_data.get('maintenance_frequency'),
            part_data.get('maintenance_unit'), part_data.get('maintenance_days'),
            part_data.get('last_maintenance'), part_data.get('next_maintenance'), current_ts
        ))
        logger.info(f"Inserted new part with server_id: {server_id}")
    conn.commit()

def upsert_audit_task_from_server(db_path: Path, encryption_key: str, audit_task_data: dict):
    conn = get_db_connection(db_path, encryption_key)
    cursor = conn.cursor()
    server_id = audit_task_data.get('id') # Server's AuditTask ID
    if not server_id:
        logger.warning(f"Skipping audit_task data, missing server_id (id field): {audit_task_data}")
        return

    server_site_id = audit_task_data.get('site_id')
    local_site_id = None
    if server_site_id is not None:
        local_site_id = get_local_id_from_server_id(db_path, encryption_key, 'sites', server_site_id)
        if local_site_id is None:
            logger.warning(f"Could not find local site for server_site_id: {server_site_id}. AuditTask server_id: {server_id} will have NULL site_id or fail.")

    server_created_by_id = audit_task_data.get('created_by')
    local_created_by_id = None
    if server_created_by_id is not None:
        local_created_by_id = get_local_id_from_server_id(db_path, encryption_key, 'users', server_created_by_id)
        if local_created_by_id is None:
            logger.warning(f"Could not find local user for server_created_by_id: {server_created_by_id}. AuditTask server_id: {server_id} may have NULL created_by.")

    local_audit_task_id = get_local_id_from_server_id(db_path, encryption_key, 'audit_tasks', server_id)
    current_ts = _get_current_timestamp_iso()

    if local_audit_task_id:
        update_query = """
        UPDATE audit_tasks SET name=?, description=?, site_id=?, created_by=?, interval=?, 
                              custom_interval_days=?, color=?, is_synced=1, last_modified=?
        WHERE id=?
        """
        cursor.execute(update_query, (
            audit_task_data.get('name'), audit_task_data.get('description'), local_site_id,
            local_created_by_id, audit_task_data.get('interval'), 
            audit_task_data.get('custom_interval_days'), audit_task_data.get('color'),
            current_ts, local_audit_task_id
        ))
        logger.info(f"Updated audit_task with server_id: {server_id} (local_id: {local_audit_task_id})")
    else:
        client_id = _generate_client_id()
        insert_query = """
        INSERT INTO audit_tasks (client_id, server_id, name, description, site_id, created_by, 
                                 interval, custom_interval_days, color, is_synced, last_modified)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        """
        cursor.execute(insert_query, (
            client_id, server_id, audit_task_data.get('name'), audit_task_data.get('description'),
            local_site_id, local_created_by_id, audit_task_data.get('interval'),
            audit_task_data.get('custom_interval_days'), audit_task_data.get('color'), current_ts
        ))
        logger.info(f"Inserted new audit_task with server_id: {server_id}")
    conn.commit()

def upsert_maintenance_record_from_server(db_path: Path, encryption_key: str, record_data: dict):
    conn = get_db_connection(db_path, encryption_key)
    cursor = conn.cursor()
    
    server_id = record_data.get('server_id') # Pulled from server, so it should have server_id
    client_id = record_data.get('client_id') # Server should echo back client_id if it was a client push

    if not server_id:
        logger.warning(f"Skipping maintenance_record data, missing server_id: {record_data}")
        return

    # Resolve FKs to local IDs
    server_part_id = record_data.get('part_id')
    local_part_id = get_local_id_from_server_id(db_path, encryption_key, 'parts', server_part_id) if server_part_id else None
    
    server_user_id = record_data.get('user_id')
    local_user_id = get_local_id_from_server_id(db_path, encryption_key, 'users', server_user_id) if server_user_id else None

    server_machine_id = record_data.get('machine_id')
    local_machine_id = get_local_id_from_server_id(db_path, encryption_key, 'machines', server_machine_id) if server_machine_id else None

    if server_part_id and local_part_id is None:
        logger.error(f"Cannot upsert maintenance_record (server_id: {server_id}). Missing local part for server_part_id: {server_part_id}. Skipping.")
        return
    if server_user_id and local_user_id is None:
        logger.error(f"Cannot upsert maintenance_record (server_id: {server_id}). Missing local user for server_user_id: {server_user_id}. Skipping.")
        return

    current_ts = _get_current_timestamp_iso()
    
    # Try to find existing record by server_id first, then by client_id if server_id match fails (e.g. first sync after push)
    existing_record_row = None
    if server_id:
        cursor.execute("SELECT id FROM maintenance_records WHERE server_id = ?", (server_id,))
        existing_record_row = cursor.fetchone()
    
    if not existing_record_row and client_id:
        cursor.execute("SELECT id FROM maintenance_records WHERE client_id = ?", (client_id,))
        existing_record_row = cursor.fetchone()

    if existing_record_row:
        local_record_id = existing_record_row[0]
        update_query = """
        UPDATE maintenance_records 
        SET part_id=?, user_id=?, machine_id=?, date=?, comments=?, maintenance_type=?, 
            description=?, performed_by=?, status=?, notes=?, 
            server_id=?, client_id=?, is_synced=1, last_modified=?
        WHERE id=?
        """
        final_client_id = client_id if client_id else _generate_client_id()
        cursor.execute(update_query, (
            local_part_id, local_user_id, local_machine_id, record_data.get('date'), record_data.get('comments'),
            record_data.get('maintenance_type'), record_data.get('description'), record_data.get('performed_by'),
            record_data.get('status'), record_data.get('notes'), 
            server_id, final_client_id, 
            current_ts, local_record_id
        ))
        logger.info(f"Updated maintenance_record with server_id: {server_id} (local_id: {local_record_id})")
    else:
        final_client_id = client_id or _generate_client_id()
        insert_query = """
        INSERT INTO maintenance_records (part_id, user_id, machine_id, date, comments, maintenance_type, 
                                     description, performed_by, status, notes, 
                                     client_id, server_id, is_synced, last_modified)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        """
        cursor.execute(insert_query, (
            local_part_id, local_user_id, local_machine_id, record_data.get('date'), record_data.get('comments'),
            record_data.get('maintenance_type'), record_data.get('description'), record_data.get('performed_by'),
            record_data.get('status'), record_data.get('notes'),
            final_client_id, server_id, current_ts
        ))
        logger.info(f"Inserted new maintenance_record with server_id: {server_id}")
    conn.commit()

def upsert_audit_task_completion_from_server(db_path: Path, encryption_key: str, completion_data: dict):
    conn = get_db_connection(db_path, encryption_key)
    cursor = conn.cursor()

    server_id = completion_data.get('server_id')
    client_id = completion_data.get('client_id')

    if not server_id:
        logger.warning(f"Skipping audit_task_completion data, missing server_id: {completion_data}")
        return

    # Resolve FKs
    server_audit_task_id = completion_data.get('audit_task_id')
    local_audit_task_id = get_local_id_from_server_id(db_path, encryption_key, 'audit_tasks', server_audit_task_id) if server_audit_task_id else None

    server_machine_id = completion_data.get('machine_id')
    local_machine_id = get_local_id_from_server_id(db_path, encryption_key, 'machines', server_machine_id) if server_machine_id else None

    server_completed_by_id = completion_data.get('completed_by')
    local_completed_by_id = get_local_id_from_server_id(db_path, encryption_key, 'users', server_completed_by_id) if server_completed_by_id else None

    if server_audit_task_id and local_audit_task_id is None:
        logger.error(f"Cannot upsert audit_task_completion (server_id: {server_id}). Missing local audit_task for server_audit_task_id: {server_audit_task_id}. Skipping.")
        return
    if server_machine_id and local_machine_id is None:
        logger.error(f"Cannot upsert audit_task_completion (server_id: {server_id}). Missing local machine for server_machine_id: {server_machine_id}. Skipping.")
        return

    current_ts = _get_current_timestamp_iso()
    existing_completion_row = None
    if server_id:
        cursor.execute("SELECT id FROM audit_task_completions WHERE server_id = ?", (server_id,))
        existing_completion_row = cursor.fetchone()

    if not existing_completion_row and client_id:
        cursor.execute("SELECT id FROM audit_task_completions WHERE client_id = ?", (client_id,))
        existing_completion_row = cursor.fetchone()

    if existing_completion_row:
        local_completion_id = existing_completion_row[0]
        update_query = """
        UPDATE audit_task_completions 
        SET audit_task_id=?, machine_id=?, date=?, completed=?, completed_by=?, completed_at=?, 
            server_id=?, client_id=?, is_synced=1, last_modified=?
        WHERE id=?
        """
        final_client_id = client_id or _generate_client_id()
        cursor.execute(update_query, (
            local_audit_task_id, local_machine_id, completion_data.get('date'), 
            completion_data.get('completed', 0), local_completed_by_id, completion_data.get('completed_at'),
            server_id, final_client_id,
            current_ts, local_completion_id
        ))
        logger.info(f"Updated audit_task_completion with server_id: {server_id} (local_id: {local_completion_id})")
    else:
        final_client_id = client_id or _generate_client_id()
        insert_query = """
        INSERT INTO audit_task_completions (audit_task_id, machine_id, date, completed, completed_by, completed_at, 
                                          client_id, server_id, is_synced, last_modified)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        """
        cursor.execute(insert_query, (
            local_audit_task_id, local_machine_id, completion_data.get('date'),
            completion_data.get('completed', 0), local_completed_by_id, completion_data.get('completed_at'),
            final_client_id, server_id, current_ts
        ))
        logger.info(f"Inserted new audit_task_completion with server_id: {server_id}")
    conn.commit()

def get_unsynced_maintenance_records(db_path: Path, encryption_key: str) -> list[dict]:
    """Retrieves all maintenance records that are not yet synced with the server."""
    query = """
    SELECT id, server_id, part_id, user_id, machine_id, date, comments, 
           maintenance_type, description, performed_by, status, notes, client_id, 
           last_modified 
    FROM maintenance_records 
    WHERE is_synced = 0;
    """
    records = fetch_all(db_path, encryption_key, query)
    
    # We need to convert local FKs (part_id, user_id, machine_id) to server_ids before sending to server
    # The server expects server_ids for these entities.
    processed_records = []
    for record in records:
        local_part_id = record.get('part_id')
        server_part_id = get_server_id_from_local_id(db_path, encryption_key, 'parts', local_part_id) if local_part_id else None
        
        local_user_id = record.get('user_id')
        server_user_id = get_server_id_from_local_id(db_path, encryption_key, 'users', local_user_id) if local_user_id else None

        local_machine_id = record.get('machine_id')
        server_machine_id = get_server_id_from_local_id(db_path, encryption_key, 'machines', local_machine_id) if local_machine_id else None

        if local_part_id and server_part_id is None:
            logger.error(f"Cannot prepare unsynced maintenance record (client_id: {record.get('client_id')}) for push. Missing server_id for local part_id: {local_part_id}. Skipping.")
            continue
        if local_user_id and server_user_id is None:
            logger.error(f"Cannot prepare unsynced maintenance record (client_id: {record.get('client_id')}) for push. Missing server_id for local user_id: {local_user_id}. Skipping.")
            continue
        # Machine can be optional, so proceed even if server_machine_id is None

        processed_record = record.copy()
        processed_record['part_id'] = server_part_id
        processed_record['user_id'] = server_user_id
        processed_record['machine_id'] = server_machine_id
        # The server_id field in the payload should be null for new records being pushed.
        # If it has a server_id already, it implies it was synced before, which contradicts is_synced = 0.
        # However, the server /api/sync/push expects 'server_id' to be the existing server_id if it's an update.
        # For purely new records (is_synced=0), server_id should be None or not present in the payload to server.
        # The current server push endpoint is for NEW records, so server_id is not expected in payload.
        # Let's remove it from the payload to avoid confusion, server will assign one.
        if 'server_id' in processed_record:
            del processed_record['server_id']
        
        # also remove local id
        if 'id' in processed_record:
            del processed_record['id']

        processed_records.append(processed_record)
    return processed_records

def get_unsynced_audit_task_completions(db_path: Path, encryption_key: str) -> list[dict]:
    """Retrieves all audit task completions that are not yet synced with the server."""
    query = """
    SELECT id, server_id, audit_task_id, machine_id, date, completed, completed_by, 
           completed_at, client_id, last_modified
    FROM audit_task_completions 
    WHERE is_synced = 0;
    """
    completions = fetch_all(db_path, encryption_key, query)
    processed_completions = []

    for completion in completions:
        local_audit_task_id = completion.get('audit_task_id')
        server_audit_task_id = get_server_id_from_local_id(db_path, encryption_key, 'audit_tasks', local_audit_task_id) if local_audit_task_id else None

        local_machine_id = completion.get('machine_id')
        server_machine_id = get_server_id_from_local_id(db_path, encryption_key, 'machines', local_machine_id) if local_machine_id else None

        local_completed_by_id = completion.get('completed_by')
        server_completed_by_id = get_server_id_from_local_id(db_path, encryption_key, 'users', local_completed_by_id) if local_completed_by_id else None

        if local_audit_task_id and server_audit_task_id is None:
            logger.error(f"Cannot prepare unsynced audit task completion (client_id: {completion.get('client_id')}) for push. Missing server_id for local audit_task_id: {local_audit_task_id}. Skipping.")
            continue
        if local_machine_id and server_machine_id is None:
            logger.error(f"Cannot prepare unsynced audit task completion (client_id: {completion.get('client_id')}) for push. Missing server_id for local machine_id: {local_machine_id}. Skipping.")
            continue
        # completed_by can be optional

        processed_completion = completion.copy()
        processed_completion['audit_task_id'] = server_audit_task_id
        processed_completion['machine_id'] = server_machine_id
        processed_completion['completed_by'] = server_completed_by_id
        
        if 'server_id' in processed_completion:
            del processed_completion['server_id']
        if 'id' in processed_completion:
            del processed_completion['id']
            
        processed_completions.append(processed_completion)
    return processed_completions

def get_server_id_from_local_id(db_path: Path, encryption_key: str, table_name: str, local_id_value: int):
    """Helper function to get server ID from a local ID for a given table."""
    if local_id_value is None:
        return None
    conn = get_db_connection(db_path, encryption_key)
    if not conn: return None
    cursor = conn.cursor()
    query = f"SELECT server_id FROM {table_name} WHERE id = ?"
    try:
        cursor.execute(query, (local_id_value,))
        row = cursor.fetchone()
        return row[0] if row and row[0] is not None else None
    except Exception as e:
        logger.error(f"Error fetching server_id for local_id {local_id_value} from {table_name}: {e}")
        return None

def update_sync_status(db_path: Path, encryption_key: str, table_name: str, client_id: str, server_id: int, last_modified_timestamp: str):
    """Updates the sync status of a local record after successful push to server."""
    conn = get_db_connection(db_path, encryption_key)
    cursor = conn.cursor()
    query = f"""
    UPDATE {table_name} 
    SET server_id = ?, is_synced = 1, last_modified = ? 
    WHERE client_id = ?;
    """
    try:
        cursor.execute(query, (server_id, last_modified_timestamp, client_id))
        conn.commit()
        if cursor.rowcount > 0:
            logger.info(f"Updated sync status for {table_name} with client_id: {client_id} to server_id: {server_id}")
        else:
            logger.warning(f"No record found in {table_name} with client_id: {client_id} to update sync status.")
    except Exception as e:
        logger.error(f"Error updating sync status for {table_name} client_id {client_id}: {e}")
        conn.rollback()

def soft_delete_local_maintenance_record(db_path: Path, encryption_key: str, client_id: str) -> bool:
    """Marks a maintenance record as deleted locally by setting a 'deleted' flag.
    This allows the deletion to be synchronized with the server.
    Returns True on success, False on failure.
    """
    conn = get_db_connection(db_path, encryption_key)
    cursor = conn.cursor()
    current_ts = _get_current_timestamp_iso()

    # First, check if the table has the 'deleted' column, add it if it doesn't
    try:
        cursor.execute("PRAGMA table_info(maintenance_records)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'deleted' not in columns:
            logger.info("Adding 'deleted' column to maintenance_records table")
            cursor.execute("ALTER TABLE maintenance_records ADD COLUMN deleted INTEGER DEFAULT 0")
        
        # Mark the record as deleted and set is_synced to 0 to push the deletion to server
        update_query = """
        UPDATE maintenance_records
        SET deleted = 1, is_synced = 0, last_modified = ?
        WHERE client_id = ?
        """
        
        cursor.execute(update_query, (current_ts, client_id))
        conn.commit()
        
        if cursor.rowcount > 0:
            logger.info(f"Soft deleted maintenance record with client_id: {client_id}")
            return True
        else:
            logger.warning(f"No maintenance record found with client_id: {client_id} to delete.")
            return False
    except Exception as e:
        logger.error(f"Error soft deleting maintenance record (client_id: {client_id}): {e}")
        conn.rollback()
        return False


def hard_delete_local_maintenance_record(db_path: Path, encryption_key: str, client_id: str) -> bool:
    """Permanently deletes a maintenance record from the local database.
    This should only be used when the record doesn't need to be synced with the server
    (e.g., it was never synced, or the deletion has been confirmed by the server).
    Returns True on success, False on failure.
    """
    conn = get_db_connection(db_path, encryption_key)
    cursor = conn.cursor()

    try:
        delete_query = "DELETE FROM maintenance_records WHERE client_id = ?"
        cursor.execute(delete_query, (client_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            logger.info(f"Hard deleted maintenance record with client_id: {client_id}")
            return True
        else:
            logger.warning(f"No maintenance record found with client_id: {client_id} to hard delete.")
            return False
    except Exception as e:
        logger.error(f"Error hard deleting maintenance record (client_id: {client_id}): {e}")
        conn.rollback()
        return False


def soft_delete_local_audit_task_completion(db_path: Path, encryption_key: str, client_id: str) -> bool:
    """Marks an audit task completion as deleted locally by setting a 'deleted' flag.
    This allows the deletion to be synchronized with the server.
    Returns True on success, False on failure.
    """
    conn = get_db_connection(db_path, encryption_key)
    cursor = conn.cursor()
    current_ts = _get_current_timestamp_iso()

    # First, check if the table has the 'deleted' column, add it if it doesn't
    try:
        cursor.execute("PRAGMA table_info(audit_task_completions)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'deleted' not in columns:
            logger.info("Adding 'deleted' column to audit_task_completions table")
            cursor.execute("ALTER TABLE audit_task_completions ADD COLUMN deleted INTEGER DEFAULT 0")
        
        # Mark the record as deleted and set is_synced to 0 to push the deletion to server
        update_query = """
        UPDATE audit_task_completions
        SET deleted = 1, is_synced = 0, last_modified = ?
        WHERE client_id = ?
        """
        
        cursor.execute(update_query, (current_ts, client_id))
        conn.commit()
        
        if cursor.rowcount > 0:
            logger.info(f"Soft deleted audit task completion with client_id: {client_id}")
            return True
        else:
            logger.warning(f"No audit task completion found with client_id: {client_id} to delete.")
            return False
    except Exception as e:
        logger.error(f"Error soft deleting audit task completion (client_id: {client_id}): {e}")
        conn.rollback()
        return False


def hard_delete_local_audit_task_completion(db_path: Path, encryption_key: str, client_id: str) -> bool:
    """Permanently deletes an audit task completion from the local database.
    This should only be used when the record doesn't need to be synced with the server
    (e.g., it was never synced, or the deletion has been confirmed by the server).
    Returns True on success, False on failure.
    """
    conn = get_db_connection(db_path, encryption_key)
    cursor = conn.cursor()

    try:
        delete_query = "DELETE FROM audit_task_completions WHERE client_id = ?"
        cursor.execute(delete_query, (client_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            logger.info(f"Hard deleted audit task completion with client_id: {client_id}")
            return True
        else:
            logger.warning(f"No audit task completion found with client_id: {client_id} to hard delete.")
            return False
    except Exception as e:
        logger.error(f"Error hard deleting audit task completion (client_id: {client_id}): {e}")
        conn.rollback()
        return False

def get_deleted_maintenance_records(db_path: Path, encryption_key: str) -> list:
    """Retrieves maintenance records that have been marked as deleted but not yet synced.
    This is used during syncing to inform the server about deletions.
    Returns a list of dictionaries with client_id and server_id for deletion synchronization.
    """
    conn = get_db_connection(db_path, encryption_key)
    if not conn:
        logger.error("Cannot get deleted maintenance records, database connection failed.")
        return []

    query = """
    SELECT client_id, server_id FROM maintenance_records
    WHERE deleted = 1 AND is_synced = 0 AND server_id IS NOT NULL
    """
    
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        results = [dict(row) for row in cursor.fetchall()]
        logger.info(f"Retrieved {len(results)} deleted maintenance records for syncing.")
        return results
    except Exception as e:
        logger.error(f"Error retrieving deleted maintenance records: {e}")
        return []


def get_deleted_audit_task_completions(db_path: Path, encryption_key: str) -> list:
    """Retrieves audit task completions that have been marked as deleted but not yet synced.
    This is used during syncing to inform the server about deletions.
    Returns a list of dictionaries with client_id and server_id for deletion synchronization.
    """
    conn = get_db_connection(db_path, encryption_key)
    if not conn:
        logger.error("Cannot get deleted audit task completions, database connection failed.")
        return []

    query = """
    SELECT client_id, server_id FROM audit_task_completions
    WHERE deleted = 1 AND is_synced = 0 AND server_id IS NOT NULL
    """
    
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        results = [dict(row) for row in cursor.fetchall()]
        logger.info(f"Retrieved {len(results)} deleted audit task completions for syncing.")
        return results
    except Exception as e:
        logger.error(f"Error retrieving deleted audit task completions: {e}")
        return []


def clean_up_synced_deletions(db_path: Path, encryption_key: str, table_name: str, client_ids: list) -> int:
    """Permanently removes records that have been marked as deleted and
    successfully synced with the server.
    
    Args:
        db_path: Path to the database file
        encryption_key: Encryption key for the database
        table_name: Name of the table to clean up (maintenance_records or audit_task_completions)
        client_ids: List of client_ids whose deletion has been confirmed by the server
        
    Returns:
        Number of records permanently removed
    """
    if not client_ids:
        return 0
        
    conn = get_db_connection(db_path, encryption_key)
    if not conn:
        logger.error(f"Cannot clean up synced deletions, database connection failed.")
        return 0
        
    placeholders = ','.join(['?'] * len(client_ids))
    delete_query = f"DELETE FROM {table_name} WHERE client_id IN ({placeholders})"
    
    try:
        cursor = conn.cursor()
        cursor.execute(delete_query, tuple(client_ids))
        conn.commit()
        deleted_count = cursor.rowcount
        logger.info(f"Permanently removed {deleted_count} synced deletions from {table_name}.")
        return deleted_count
    except Exception as e:
        logger.error(f"Error cleaning up synced deletions from {table_name}: {e}")
        conn.rollback()
        return 0

if __name__ == '__main__':
    example_db_path = Path.home() / ".amrs_test_data/instance/test_local_app.db"
    example_db_path.parent.mkdir(parents=True, exist_ok=True)
    example_key = "testkey1234567890123456789012345678901234567890123456789012345"

    logger.info(f"Using database: {example_db_path}")
    logger.info(f"Using key (example only): {example_key[:10]}...")

    try:
        conn = get_db_connection(example_db_path, example_key)
        if conn:
            create_tables(example_db_path, example_key)
            close_db_connection()
        else:
            logger.error("Failed to establish database connection for testing.")
    except Exception as e:
        logger.error(f"An error occurred during direct testing: {e}")

