"""
Enhanced sync utilities for real-time synchronization between offline and online systems.
This module provides:
1. Real-time sync triggers for database changes
2. Auto-sync on page loads
3. Timezone-aware datetime handling
4. Comprehensive sync queue management
"""

import os
import time
import threading
import requests
import json as _json
from datetime import datetime, timedelta
from sqlalchemy import text as sa_text
from timezone_utils import get_timezone_aware_now, get_eastern_date, is_online_server

# Global sync event for triggering immediate uploads
sync_event = threading.Event()

def should_trigger_sync():
    """
    Determine if sync should be triggered based on current environment.
    Only offline clients should trigger sync uploads.
    """
    return not is_online_server()

def add_to_sync_queue_enhanced(table_name, record_id, operation, payload_dict, immediate_sync=True, force_add=False):
    """
    Enhanced version of add_to_sync_queue with real-time sync triggering.
    
    Args:
        table_name (str): Name of the table changed
        record_id (str|int): Primary key of the record changed
        operation (str): 'insert', 'update', or 'delete'
        payload_dict (dict): The record data (as dict, will be JSON-encoded)
        immediate_sync (bool): Whether to trigger immediate sync (default: True)
        force_add (bool): Force adding to sync queue even on online server (for imports)
    """
    try:
        # Import here to avoid circular imports
        from app import db
        
        # Skip sync queue if this is the online server, unless force_add is True (for imports)
        if is_online_server() and not force_add:
            print(f"[SYNC_QUEUE] Skipping sync queue for {table_name}:{record_id} - this is the online server")
            return
            
        # Use timezone-aware datetime
        now = get_timezone_aware_now()
        payload_json = _json.dumps(payload_dict, default=str)  # default=str handles datetime serialization
        
        # Insert into sync_queue
        db.session.execute(sa_text("""
            INSERT INTO sync_queue (table_name, record_id, operation, payload, created_at, status)
            VALUES (:table_name, :record_id, :operation, :payload, :created_at, 'pending')
        """), {
            "table_name": table_name,
            "record_id": str(record_id),
            "operation": operation,
            "payload": payload_json,
            "created_at": now
        })
        db.session.commit()
        
        print(f"[SYNC_QUEUE] Added {operation} for {table_name}:{record_id} to sync_queue (immediate_sync={immediate_sync})")
        
        # Trigger immediate sync if requested and we're offline
        if immediate_sync and should_trigger_sync():
            trigger_immediate_sync()
            
    except Exception as e:
        print(f"[SYNC_QUEUE] Error adding to sync_queue: {e}")
        try:
            from app import db
            db.session.rollback()
        except:
            pass

def trigger_immediate_sync():
    """
    Trigger immediate sync by signaling the background worker.
    Only works for offline clients.
    """
    if should_trigger_sync():
        sync_event.set()
        print("[SYNC] Immediate sync triggered")
    else:
        print("[SYNC] Skipping immediate sync - this is the online server")

def trigger_manual_sync():
    """
    Manually trigger a sync operation (e.g., on page load).
    This checks for pending items and uploads them if network is available.
    """
    if not should_trigger_sync():
        print("[SYNC] Manual sync skipped - this is the online server")
        return {"status": "skipped", "reason": "online_server"}
    
    try:
        from app import db, app
        with app.app_context():
            # Check for pending sync items
            pending_count = db.session.execute(sa_text(
                "SELECT COUNT(*) FROM sync_queue WHERE status = 'pending'"
            )).scalar()
            
            if pending_count > 0:
                print(f"[SYNC] Manual sync: Found {pending_count} pending items, triggering upload")
                trigger_immediate_sync()
                return {"status": "triggered", "pending_count": pending_count}
            else:
                print("[SYNC] Manual sync: No pending items")
                return {"status": "no_pending", "pending_count": 0}
                
    except Exception as e:
        print(f"[SYNC] Manual sync error: {e}")
        return {"status": "error", "error": str(e)}

def enhanced_upload_pending_sync_queue():
    """
    Enhanced version of upload_pending_sync_queue with better error handling
    and timezone awareness.
    """
    try:
        from app import db, app
        with app.app_context():
            # Get pending items with timezone-aware queries
            pending_items = db.session.execute(sa_text("""
                SELECT id, table_name, record_id, operation, payload, created_at 
                FROM sync_queue 
                WHERE status = 'pending' 
                ORDER BY created_at ASC
            """)).fetchall()
            
            if not pending_items:
                print("[SYNC] No pending changes to upload.")
                return {"status": "no_pending", "uploaded": 0}
            
            print(f"[SYNC] Uploading {len(pending_items)} pending changes from sync_queue...")
            
            # Prepare upload payload grouped by table
            upload_payload = {}
            item_ids = []
            
            for item in pending_items:
                table = item[1]  # table_name
                item_ids.append(item[0])  # id
                
                if table not in upload_payload:
                    upload_payload[table] = []
                
                try:
                    record = _json.loads(item[4])  # payload
                    record['__operation__'] = item[3]  # operation
                    record['__sync_queue_id__'] = item[0]  # id
                    
                    # Handle created_at field - could be datetime object or string
                    created_at = item[5]
                    if created_at:
                        if hasattr(created_at, 'isoformat'):
                            record['__created_at__'] = created_at.isoformat()
                        else:
                            record['__created_at__'] = str(created_at)
                    else:
                        record['__created_at__'] = None
                        
                    upload_payload[table].append(record)
                except Exception as e:
                    print(f"[SYNC] Error parsing payload for sync_queue id {item[0]}: {e}")
                    continue
            
            # Upload to server
            success = upload_to_server(upload_payload)
            
            if success:
                # Mark items as synced with timezone-aware timestamp
                now = get_timezone_aware_now()
                if item_ids:
                    placeholders = ','.join([f':id_{i}' for i in range(len(item_ids))])
                    query = f"UPDATE sync_queue SET status = 'synced', synced_at = :now WHERE id IN ({placeholders})"
                    params = {'now': now}
                    for i, id_val in enumerate(item_ids):
                        params[f'id_{i}'] = id_val
                    
                    db.session.execute(sa_text(query), params)
                    db.session.commit()
                    
                print(f"[SYNC] Successfully uploaded and marked {len(item_ids)} sync_queue items as synced.")
                return {"status": "success", "uploaded": len(item_ids)}
            else:
                print("[SYNC] Upload failed, items remain pending for retry")
                return {"status": "failed", "uploaded": 0}
                
    except Exception as e:
        print(f"[SYNC] Enhanced upload error: {e}")
        return {"status": "error", "error": str(e), "uploaded": 0}

def upload_to_server(upload_payload):
    """
    Upload payload to the online server.
    Returns True if successful, False otherwise.
    """
    try:
        online_url = os.environ.get('AMRS_ONLINE_URL')
        admin_username = os.environ.get('AMRS_ADMIN_USERNAME')
        admin_password = os.environ.get('AMRS_ADMIN_PASSWORD')
        
        if not online_url or not admin_username or not admin_password:
            print("[SYNC] Missing AMRS_ONLINE_URL or AMRS_ADMIN_USERNAME/AMRS_ADMIN_PASSWORD; cannot upload changes.")
            return False
        
        clean_url = online_url.strip('"\'').rstrip('/')
        if clean_url.endswith('/api'):
            clean_url = clean_url[:-4]
        
        # Add timestamp for debugging
        upload_payload['__sync_timestamp__'] = get_timezone_aware_now().isoformat()
        upload_payload['__client_timezone__'] = 'America/New_York'
        
        resp = requests.post(
            f"{clean_url}/api/sync/data",
            json=upload_payload,
            headers={"Content-Type": "application/json"},
            auth=(admin_username, admin_password),
            timeout=30
        )
        
        if resp.status_code == 200:
            print(f"[SYNC] Upload successful: {resp.status_code}")
            return True
        else:
            print(f"[SYNC] Upload failed: {resp.status_code} {resp.text}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"[SYNC] Connection error during upload (desktop clients may be offline): {e}")
        return False
    except requests.exceptions.Timeout as e:
        print(f"[SYNC] Timeout during upload: {e}")
        return False
    except Exception as e:
        print(f"[SYNC] Exception during upload: {e}")
        return False

def enhanced_background_sync_worker():
    """
    Enhanced background sync worker with better scheduling and error handling.
    """
    last_periodic_check = time.time()
    consecutive_errors = 0
    max_consecutive_errors = 5
    
    print("[SYNC] Enhanced background sync worker started")
    
    while True:
        try:
            # Wait for sync event with timeout for periodic checks
            sync_event.wait(timeout=300)  # Check every 5 minutes
            
            current_time = time.time()
            should_do_periodic = (current_time - last_periodic_check) >= 300  # 5 minutes
            
            if should_do_periodic or sync_event.is_set():
                print(f"[SYNC] Worker triggered: periodic={should_do_periodic}, event={sync_event.is_set()}")
                
                result = enhanced_upload_pending_sync_queue()
                
                if result["status"] == "success":
                    consecutive_errors = 0  # Reset error counter on success
                elif result["status"] == "error":
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        print(f"[SYNC] Too many consecutive errors ({consecutive_errors}), backing off...")
                        time.sleep(60)  # Wait 1 minute before retrying
                
                if should_do_periodic:
                    last_periodic_check = current_time
                    
        except Exception as e:
            print(f"[SYNC] Background sync worker error: {e}")
            consecutive_errors += 1
            time.sleep(30)  # Wait 30 seconds on error
            
        finally:
            if sync_event.is_set():
                sync_event.clear()  # Reset event

def start_enhanced_sync_worker():
    """
    Start the enhanced background sync worker for offline clients only.
    """
    if should_trigger_sync():
        sync_thread = threading.Thread(target=enhanced_background_sync_worker, daemon=True)
        sync_thread.start()
        print("[SYNC] Enhanced background sync worker started for offline client")
        
        # Signal sync worker on startup to process any existing pending changes
        trigger_immediate_sync()
    else:
        print("[SYNC] Skipping enhanced sync worker - this appears to be the online server")

# Sync queue cleanup with timezone awareness
def cleanup_expired_sync_queue_enhanced():
    """
    Enhanced cleanup of expired sync_queue records with timezone awareness.
    """
    try:
        from app import db
        
        # Use timezone-aware cutoff time
        cutoff = get_timezone_aware_now() - timedelta(hours=144)  # 6 days
        
        deleted_count = db.session.execute(sa_text("""
            DELETE FROM sync_queue WHERE created_at < :cutoff AND status = 'synced'
        """), {"cutoff": cutoff}).rowcount
        
        db.session.commit()
        print(f"[SYNC_QUEUE] Cleaned up {deleted_count} expired sync_queue records older than {cutoff}.")
        return deleted_count
        
    except Exception as e:
        print(f"[SYNC_QUEUE] Error cleaning up expired sync_queue records: {e}")
        return 0
