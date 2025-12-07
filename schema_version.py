"""
Schema Version Management for AMRS Maintenance Tracker

This module handles schema versioning to ensure offline clients stay in sync
with the server's database schema. When a schema mismatch is detected, the
client will perform a full database refresh from the server.

Schema Version History:
- v1: Initial schema
- v2: Added cycle-based maintenance columns (machines.cycle_count, machines.last_cycle_update,
      parts.maintenance_cycle_frequency, parts.last_maintenance_cycle, parts.next_maintenance_cycle)
- v3: Added decommissioned fields to machines
- v4: Added remember_sessions table
- v5: Enhanced security events schema
"""

import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Current schema version - INCREMENT THIS when making schema changes
CURRENT_SCHEMA_VERSION = 5

# Schema version history for documentation
SCHEMA_VERSIONS = {
    1: "Initial schema",
    2: "Cycle-based maintenance (machines.cycle_count, parts.maintenance_cycle_frequency)",
    3: "Decommissioned fields on machines table",
    4: "Remember sessions table for persistent auth",
    5: "Enhanced security events with severity, source, correlation_id",
}


def get_local_schema_version():
    """
    Get the schema version stored in the local database.
    Returns 0 if no version is found (indicates fresh install or pre-versioning DB).
    """
    try:
        from app import db
        from sqlalchemy import text
        
        # Check if app_settings table exists and has schema_version
        result = db.session.execute(text(
            "SELECT value FROM app_settings WHERE key = 'schema_version'"
        )).fetchone()
        
        if result and result[0]:
            return int(result[0])
        return 0
        
    except Exception as e:
        logger.warning(f"[SCHEMA] Could not get local schema version: {e}")
        return 0


def set_local_schema_version(version):
    """
    Set the schema version in the local database.
    """
    try:
        from app import db
        from sqlalchemy import text
        
        # Use upsert pattern for SQLite
        db.session.execute(text("""
            INSERT INTO app_settings (key, value) VALUES ('schema_version', :version)
            ON CONFLICT(key) DO UPDATE SET value = :version
        """), {"version": str(version)})
        db.session.commit()
        
        logger.info(f"[SCHEMA] Set local schema version to {version}")
        return True
        
    except Exception as e:
        logger.error(f"[SCHEMA] Could not set local schema version: {e}")
        try:
            db.session.rollback()
        except:
            pass
        return False


def check_schema_needs_refresh():
    """
    Check if the local schema version is outdated and needs a full refresh.
    
    Returns:
        dict with keys:
        - needs_refresh (bool): True if schema is outdated
        - local_version (int): Current local schema version
        - required_version (int): Required schema version
        - reason (str): Human-readable reason
    """
    local_version = get_local_schema_version()
    
    if local_version == 0:
        # No version found - could be fresh install or old DB
        # Check if critical columns exist to determine if refresh is needed
        missing_columns = check_for_missing_critical_columns()
        
        if missing_columns:
            return {
                "needs_refresh": True,
                "local_version": 0,
                "required_version": CURRENT_SCHEMA_VERSION,
                "reason": f"Missing critical columns: {', '.join(missing_columns)}",
                "missing_columns": missing_columns
            }
        else:
            # Columns exist, just need to set version
            set_local_schema_version(CURRENT_SCHEMA_VERSION)
            return {
                "needs_refresh": False,
                "local_version": CURRENT_SCHEMA_VERSION,
                "required_version": CURRENT_SCHEMA_VERSION,
                "reason": "Schema up to date (version set)"
            }
    
    if local_version < CURRENT_SCHEMA_VERSION:
        return {
            "needs_refresh": True,
            "local_version": local_version,
            "required_version": CURRENT_SCHEMA_VERSION,
            "reason": f"Schema outdated: v{local_version} -> v{CURRENT_SCHEMA_VERSION}"
        }
    
    return {
        "needs_refresh": False,
        "local_version": local_version,
        "required_version": CURRENT_SCHEMA_VERSION,
        "reason": "Schema up to date"
    }


def check_for_missing_critical_columns():
    """
    Check if critical columns are missing from the database.
    Returns a list of missing column names.
    """
    missing = []
    
    try:
        from app import db
        from sqlalchemy import inspect, text
        
        engine = db.engine
        inspector = inspect(engine)
        
        # Define critical columns that must exist
        critical_columns = {
            'machines': ['cycle_count', 'last_cycle_update', 'decommissioned', 'decommissioned_date'],
            'parts': ['maintenance_cycle_frequency', 'last_maintenance_cycle', 'next_maintenance_cycle'],
            'users': ['username_hash', 'email_hash', 'remember_token', 'remember_enabled'],
        }
        
        for table_name, columns in critical_columns.items():
            try:
                existing_columns = [col['name'] for col in inspector.get_columns(table_name)]
                for col in columns:
                    if col not in existing_columns:
                        missing.append(f"{table_name}.{col}")
            except Exception as e:
                logger.warning(f"[SCHEMA] Could not check table {table_name}: {e}")
                
    except Exception as e:
        logger.error(f"[SCHEMA] Error checking for missing columns: {e}")
        
    return missing


def perform_schema_refresh():
    """
    Perform a full database refresh from the server.
    
    This function:
    1. Backs up any unsynced local changes
    2. Downloads fresh data from server
    3. Rebuilds local database with correct schema
    4. Restores unsynced changes to sync queue
    
    Returns:
        dict with status and details
    """
    logger.info("[SCHEMA] Starting full database refresh...")
    
    try:
        from app import db, app
        from sqlalchemy import text
        import json
        
        with app.app_context():
            # Step 1: Backup unsynced changes from sync_queue
            unsynced_changes = []
            try:
                result = db.session.execute(text(
                    "SELECT table_name, record_id, operation, payload FROM sync_queue WHERE status = 'pending'"
                )).fetchall()
                
                for row in result:
                    unsynced_changes.append({
                        'table_name': row[0],
                        'record_id': row[1],
                        'operation': row[2],
                        'payload': row[3]
                    })
                    
                if unsynced_changes:
                    logger.info(f"[SCHEMA] Backed up {len(unsynced_changes)} unsynced changes")
                    
            except Exception as e:
                logger.warning(f"[SCHEMA] Could not backup unsynced changes: {e}")
            
            # Step 2: Run auto-migration to add missing columns
            try:
                from auto_migrate import run_auto_migration
                run_auto_migration()
                logger.info("[SCHEMA] Auto-migration completed")
            except Exception as e:
                logger.error(f"[SCHEMA] Auto-migration failed: {e}")
                return {"status": "error", "error": f"Migration failed: {e}"}
            
            # Step 3: Download fresh data from server
            try:
                from sync_utils_enhanced import download_and_import_server_data
                download_result = download_and_import_server_data()
                logger.info(f"[SCHEMA] Download result: {download_result}")
            except Exception as e:
                logger.warning(f"[SCHEMA] Could not download server data: {e}")
                download_result = {"status": "error", "error": str(e)}
            
            # Step 4: Restore unsynced changes to sync queue
            if unsynced_changes:
                try:
                    for change in unsynced_changes:
                        db.session.execute(text("""
                            INSERT INTO sync_queue (table_name, record_id, operation, payload, status, created_at)
                            VALUES (:table_name, :record_id, :operation, :payload, 'pending', :now)
                        """), {
                            'table_name': change['table_name'],
                            'record_id': change['record_id'],
                            'operation': change['operation'],
                            'payload': change['payload'],
                            'now': datetime.utcnow()
                        })
                    db.session.commit()
                    logger.info(f"[SCHEMA] Restored {len(unsynced_changes)} unsynced changes")
                except Exception as e:
                    logger.warning(f"[SCHEMA] Could not restore unsynced changes: {e}")
            
            # Step 5: Update schema version
            set_local_schema_version(CURRENT_SCHEMA_VERSION)
            
            return {
                "status": "success",
                "schema_version": CURRENT_SCHEMA_VERSION,
                "unsynced_preserved": len(unsynced_changes),
                "download_result": download_result
            }
            
    except Exception as e:
        logger.error(f"[SCHEMA] Database refresh failed: {e}")
        return {"status": "error", "error": str(e)}


def ensure_schema_current():
    """
    Main entry point: Check schema and refresh if needed.
    Call this on app startup for offline clients.
    
    Returns:
        dict with schema status
    """
    from timezone_utils import is_offline_mode
    
    # Only check schema for offline clients
    if not is_offline_mode():
        logger.info("[SCHEMA] Online server - schema managed by migrations")
        return {"status": "online_server", "needs_refresh": False}
    
    logger.info("[SCHEMA] Checking local schema version...")
    
    check_result = check_schema_needs_refresh()
    
    if check_result["needs_refresh"]:
        logger.warning(f"[SCHEMA] Schema refresh needed: {check_result['reason']}")
        
        # Perform the refresh
        refresh_result = perform_schema_refresh()
        
        return {
            "status": "refreshed" if refresh_result["status"] == "success" else "refresh_failed",
            "check_result": check_result,
            "refresh_result": refresh_result
        }
    else:
        logger.info(f"[SCHEMA] Schema is current (v{check_result['local_version']})")
        return {
            "status": "current",
            "check_result": check_result
        }


def get_schema_info():
    """
    Get detailed schema information for diagnostics.
    """
    return {
        "current_version": CURRENT_SCHEMA_VERSION,
        "local_version": get_local_schema_version(),
        "version_history": SCHEMA_VERSIONS,
        "missing_columns": check_for_missing_critical_columns()
    }
