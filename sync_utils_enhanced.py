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

# Global sync worker thread reference
sync_worker_thread = None
sync_worker_lock = threading.Lock()

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
        
        # Online servers should add local changes to sync queue for distribution to offline clients
        # The only time we skip is if this is an offline client trying to track already-downloaded data
        # But since we're always in the context of local changes or imports, we should proceed
            
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

def enhanced_bidirectional_sync():
    """
    Enhanced bidirectional sync: uploads pending changes AND downloads new data.
    Used by the periodic sync worker to keep offline clients in sync.
    """
    try:
        # First, upload any pending local changes
        upload_result = enhanced_upload_pending_sync_queue()
        print(f"[SYNC] Upload result: {upload_result}")
        
        # Then, download and import new data from server
        download_result = download_and_import_server_data()
        print(f"[SYNC] Download result: {download_result}")
        
        # Return combined results
        total_uploaded = upload_result.get("uploaded", 0)
        total_downloaded = download_result.get("imported", 0)
        
        # Update sync timestamp if download was successful
        if download_result.get("status") == "success" and total_downloaded > 0:
            update_last_sync_timestamp()
        
        if upload_result.get("status") == "success" or download_result.get("status") == "success":
            return {
                "status": "success", 
                "uploaded": total_uploaded,
                "downloaded": total_downloaded,
                "total_changes": total_uploaded + total_downloaded
            }
        elif upload_result.get("status") == "no_pending" and download_result.get("status") == "no_changes":
            return {
                "status": "no_changes",
                "uploaded": 0,
                "downloaded": 0, 
                "total_changes": 0
            }
        else:
            return {
                "status": "partial_success",
                "uploaded": total_uploaded,
                "downloaded": total_downloaded,
                "upload_status": upload_result.get("status"),
                "download_status": download_result.get("status")
            }
            
    except Exception as e:
        print(f"[SYNC] Bidirectional sync error: {e}")
        return {"status": "error", "error": str(e)}

def download_and_import_server_data():
    """
    Download latest data from server and import into local database.
    Returns status and count of imported records.
    """
    try:
        import requests
        from app import db, app
        
        with app.app_context():
            # Get server configuration
            online_url = os.environ.get('AMRS_ONLINE_URL')
            admin_username = os.environ.get('AMRS_ADMIN_USERNAME')
            admin_password = os.environ.get('AMRS_ADMIN_PASSWORD')
            
            if not all([online_url, admin_username, admin_password]):
                print("[SYNC] Missing server credentials for download")
                return {"status": "no_config", "imported": 0}
            
            # Clean URL
            clean_url = online_url.strip('"\'').rstrip('/')
            if clean_url.endswith('/api'):
                clean_url = clean_url[:-4]
            
            # Create session and authenticate
            session = requests.Session()
            
            # Try session-based login
            try:
                login_resp = session.post(f"{clean_url}/login", data={
                    'username': admin_username,
                    'password': admin_password
                })
                
                if login_resp.status_code != 200 or 'dashboard' not in login_resp.text.lower():
                    print("[SYNC] Session authentication failed for download")
                    return {"status": "auth_failed", "imported": 0}
                    
            except Exception as e:
                print(f"[SYNC] Authentication error: {e}")
                return {"status": "auth_error", "imported": 0}
            
            # Download data from server
            try:
                # Get the last successful sync timestamp for incremental sync
                last_sync_time = get_last_sync_timestamp()
                
                # Build download URL with timestamp parameter for incremental sync
                download_url = f"{clean_url}/api/sync/data"
                if last_sync_time:
                    download_url += f"?since={last_sync_time}"
                    print(f"[SYNC] Requesting incremental sync since: {last_sync_time}")
                else:
                    print(f"[SYNC] Requesting full sync (no previous sync timestamp)")
                
                download_resp = session.get(download_url, timeout=30)
                
                if download_resp.status_code != 200:
                    print(f"[SYNC] Download failed: {download_resp.status_code}")
                    return {"status": "download_failed", "imported": 0}
                    
                server_data = download_resp.json()
                
            except Exception as e:
                print(f"[SYNC] Download error: {e}")
                return {"status": "download_error", "imported": 0}
            
            # Import data into local database
            total_imported = 0
            
            # Import audit_task_completions (most important for real-time updates)
            if 'audit_task_completions' in server_data:
                try:
                    imported_count = import_audit_completions(server_data['audit_task_completions'])
                    total_imported += imported_count
                    print(f"[SYNC] Imported {imported_count} audit task completions")
                except Exception as e:
                    print(f"[SYNC] Error importing audit_task_completions: {e}")
                    # Rollback to clear any error state
                    try:
                        db.session.rollback()
                    except:
                        pass
            
            # Import other tables as needed
            for table_name in ['users', 'roles', 'sites', 'machines', 'parts', 'audit_tasks', 'maintenance_records']:
                if table_name in server_data:
                    try:
                        imported_count = import_table_data(table_name, server_data[table_name])
                        total_imported += imported_count
                        if imported_count > 0:
                            print(f"[SYNC] Imported {imported_count} {table_name} records")
                    except Exception as e:
                        print(f"[SYNC] Error importing table {table_name}: {e}")
                        # Rollback to clear any error state
                        try:
                            db.session.rollback()
                        except:
                            pass
                        continue
            
            if total_imported > 0:
                # Update the last sync timestamp for incremental sync
                update_last_sync_timestamp()
                return {"status": "success", "imported": total_imported}
            else:
                return {"status": "no_changes", "imported": 0}
                
    except Exception as e:
        print(f"[SYNC] Download and import error: {e}")
        return {"status": "error", "error": str(e), "imported": 0}

def import_audit_completions(completions_data):
    """Import audit task completions from server data."""
    try:
        from app import db
        from models import AuditTaskCompletion
        from datetime import datetime, date
        
        imported_count = 0
        
        for completion_data in completions_data:
            session_rollback_needed = False
            try:
                # Check if record already exists
                existing = AuditTaskCompletion.query.get(completion_data.get('id'))
                
                # Convert date/datetime strings to proper Python objects
                processed_data = {}
                for key, value in completion_data.items():
                    if value is None:
                        processed_data[key] = None
                    elif key == 'date' and isinstance(value, str):
                        # Convert date string to Python date object
                        try:
                            processed_data[key] = datetime.strptime(value, '%Y-%m-%d').date()
                        except ValueError:
                            processed_data[key] = value  # Keep original if conversion fails
                    elif key in ['completed_at', 'created_at', 'updated_at'] and isinstance(value, str):
                        # Convert datetime string to Python datetime object
                        try:
                            processed_data[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        except (ValueError, AttributeError):
                            try:
                                processed_data[key] = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
                            except ValueError:
                                processed_data[key] = value  # Keep original if conversion fails
                    else:
                        processed_data[key] = value
                
                if existing:
                    # Update existing record if data is newer
                    if processed_data.get('updated_at'):
                        server_updated = processed_data.get('updated_at')
                        local_updated = existing.updated_at
                        
                        # Compare timestamps (handle both datetime and string)
                        if isinstance(server_updated, str):
                            try:
                                server_updated = datetime.fromisoformat(server_updated.replace('Z', '+00:00'))
                            except:
                                pass
                        
                        if server_updated != local_updated:
                            # Update existing record with no_autoflush protection
                            with db.session.no_autoflush:
                                for key, value in processed_data.items():
                                    # Only set attributes that actually exist on the model
                                    if hasattr(existing, key) and key != 'id':
                                        # Check if it's a settable attribute (not a property without setter)
                                        attr = getattr(existing.__class__, key, None)
                                        if attr is None or not isinstance(attr, property) or attr.fset is not None:
                                            setattr(existing, key, value)
                            imported_count += 1
                else:
                    # Create new record with no_autoflush protection
                    with db.session.no_autoflush:
                        # Filter out fields that don't exist on the AuditTaskCompletion model
                        valid_fields = {}
                        for key, value in processed_data.items():
                            if hasattr(AuditTaskCompletion, key):
                                # Check if it's a settable attribute
                                attr = getattr(AuditTaskCompletion, key, None)
                                if attr is None or not isinstance(attr, property) or attr.fset is not None:
                                    valid_fields[key] = value
                        
                        completion = AuditTaskCompletion(**valid_fields)
                        db.session.add(completion)
                    imported_count += 1
                    
            except Exception as e:
                print(f"[SYNC] Error importing audit completion {completion_data.get('id')}: {e}")
                session_rollback_needed = True
                continue
            finally:
                # Handle session rollback if needed
                if session_rollback_needed:
                    try:
                        db.session.rollback()
                    except:
                        pass
        
        # Commit all successful imports
        if imported_count > 0:
            db.session.commit()
        
        return imported_count
        
    except Exception as e:
        print(f"[SYNC] Error in import_audit_completions: {e}")
        # Rollback the session to clear the error state
        try:
            db.session.rollback()
        except:
            pass
        return 0

def import_table_data(table_name, table_data):
    """Generic function to import table data with proper date/datetime conversion."""
    try:
        from app import db
        from models import User, Role, Site, Machine, Part, AuditTask, MaintenanceRecord
        from datetime import datetime, date
        
        model_map = {
            'users': User,
            'roles': Role, 
            'sites': Site,
            'machines': Machine,
            'parts': Part,
            'audit_tasks': AuditTask,
            'maintenance_records': MaintenanceRecord
        }
        
        if table_name not in model_map:
            return 0
            
        model_class = model_map[table_name]
        imported_count = 0
        
        for record_data in table_data:
            # Use a separate try-catch for each record with session management
            session_rollback_needed = False
            try:
                # Convert date/datetime strings to proper Python objects
                processed_data = {}
                for key, value in record_data.items():
                    if value is None:
                        processed_data[key] = None
                    elif isinstance(value, str) and key in ['date', 'start_date', 'end_date', 'last_maintenance_date', 'next_maintenance_date']:
                        # Convert date strings to Python date objects
                        try:
                            processed_data[key] = datetime.strptime(value, '%Y-%m-%d').date()
                        except ValueError:
                            try:
                                # Try with datetime format and extract date
                                processed_data[key] = datetime.fromisoformat(value.replace('Z', '+00:00')).date()
                            except:
                                processed_data[key] = value  # Keep original if conversion fails
                    elif isinstance(value, str) and key in ['created_at', 'updated_at', 'completed_at', 'last_login', 'password_reset_expires', 'last_maintenance', 'next_maintenance', 'decommissioned_date']:
                        # Convert datetime strings to Python datetime objects
                        try:
                            processed_data[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        except (ValueError, AttributeError):
                            # Try alternative datetime format for historical dates
                            try:
                                processed_data[key] = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
                            except ValueError:
                                processed_data[key] = value  # Keep original if conversion fails
                    else:
                        processed_data[key] = value
                
                existing = model_class.query.get(processed_data.get('id'))
                
                if existing:
                    # Update if newer (simplified check)
                    if processed_data.get('updated_at'):
                        # Update existing record with session.no_autoflush to prevent premature flushes
                        with db.session.no_autoflush:
                            for key, value in processed_data.items():
                                # Only set attributes that actually exist on the model
                                if hasattr(existing, key) and key != 'id':
                                    # Check if it's a settable attribute (not a property without setter)
                                    attr = getattr(existing.__class__, key, None)
                                    if attr is None or not isinstance(attr, property) or attr.fset is not None:
                                        setattr(existing, key, value)
                        imported_count += 1
                else:
                    # Create new record using merge to handle conflicts
                    try:
                        with db.session.no_autoflush:
                            # Filter out fields that don't exist on the model
                            valid_fields = {}
                            for key, value in processed_data.items():
                                if hasattr(model_class, key):
                                    # Check if it's a settable attribute
                                    attr = getattr(model_class, key, None)
                                    if attr is None or not isinstance(attr, property) or attr.fset is not None:
                                        valid_fields[key] = value
                            
                            new_record = model_class(**valid_fields)
                            db.session.merge(new_record)
                        imported_count += 1
                    except Exception as create_error:
                        print(f"[SYNC] Error creating {table_name} record {processed_data.get('id')}: {create_error}")
                        session_rollback_needed = True
                        continue
                    
            except Exception as e:
                print(f"[SYNC] Error importing {table_name} record {record_data.get('id')}: {e}")
                session_rollback_needed = True
                continue
            finally:
                # Handle session rollback if needed
                if session_rollback_needed:
                    try:
                        db.session.rollback()
                    except:
                        pass
        
        # Commit all successful imports
        if imported_count > 0:
            db.session.commit()
        
        return imported_count
        
    except Exception as e:
        print(f"[SYNC] Error importing {table_name}: {e}")
        # Rollback the session to clear the error state
        try:
            db.session.rollback()
        except:
            pass
        return 0

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
    Enhanced background sync worker with bidirectional sync capability.
    Uploads local changes AND downloads server updates automatically.
    Includes health monitoring and auto-recovery.
    """
    last_periodic_check = time.time()
    consecutive_errors = 0
    max_consecutive_errors = 5
    
    print("[SYNC] Enhanced bidirectional sync worker started")
    
    # Worker health monitoring
    worker_start_time = time.time()
    last_health_log = time.time()
    
    while True:
        try:
            # Wait for sync event with timeout for periodic checks
            sync_event.wait(timeout=300)  # Check every 5 minutes
            
            current_time = time.time()
            should_do_periodic = (current_time - last_periodic_check) >= 300  # 5 minutes
            
            # Log worker health every hour
            if (current_time - last_health_log) >= 3600:  # 1 hour
                uptime = current_time - worker_start_time
                print(f"[SYNC] Worker health: Running for {uptime/3600:.1f}h, {consecutive_errors} consecutive errors")
                last_health_log = current_time
            
            if should_do_periodic or sync_event.is_set():
                trigger_type = "periodic" if should_do_periodic else "event"
                print(f"[SYNC] Bidirectional sync triggered: {trigger_type}")
                
                # Perform bidirectional sync (upload + download)
                result = enhanced_bidirectional_sync()
                
                if result["status"] == "success":
                    consecutive_errors = 0  # Reset error counter on success
                    uploaded = result.get('uploaded', 0)
                    downloaded = result.get('downloaded', 0)
                    total = result.get('total_changes', 0)
                    
                    if total > 0:
                        print(f"[SYNC] Bidirectional sync complete: ↑{uploaded} ↓{downloaded} records")
                elif result["status"] == "no_changes":
                    consecutive_errors = 0  # Reset on successful no-changes
                elif result["status"] == "partial_success":
                    uploaded = result.get('uploaded', 0)
                    downloaded = result.get('downloaded', 0)
                    print(f"[SYNC] Partial sync: ↑{uploaded} ↓{downloaded} (some issues occurred)")
                elif result["status"] == "error":
                    consecutive_errors += 1
                    print(f"[SYNC] Sync error: {result.get('error', 'Unknown error')}")
                    if consecutive_errors >= max_consecutive_errors:
                        print(f"[SYNC] Too many consecutive errors ({consecutive_errors}), backing off...")
                        time.sleep(60)  # Wait 1 minute before retrying
                
                if should_do_periodic:
                    last_periodic_check = current_time
                    
        except Exception as e:
            print(f"[SYNC] Background sync worker error: {e}")
            consecutive_errors += 1
            
            # If too many errors, restart the worker
            if consecutive_errors >= max_consecutive_errors:
                print(f"[SYNC] Worker has {consecutive_errors} consecutive errors, will restart")
                break  # Exit the loop to allow restart
            
            time.sleep(30)  # Wait 30 seconds on error
            
        finally:
            if sync_event.is_set():
                sync_event.clear()  # Reset event
    
    print(f"[SYNC] Background sync worker exiting due to too many errors ({consecutive_errors})")
    # Mark worker as dead so it can be restarted
    global sync_worker_thread
    with sync_worker_lock:
        sync_worker_thread = None

def start_enhanced_sync_worker():
    """
    Start the enhanced background sync worker for offline clients only.
    """
    global sync_worker_thread
    
    if should_trigger_sync():
        with sync_worker_lock:
            sync_worker_thread = threading.Thread(target=enhanced_background_sync_worker, daemon=True)
            sync_worker_thread.start()
            print("[SYNC] Enhanced background sync worker started for offline client")
        
        # Signal sync worker on startup to process any existing pending changes
        trigger_immediate_sync()
    else:
        print("[SYNC] Skipping enhanced sync worker - this appears to be the online server")

def trigger_reconnection_sync():
    """
    Trigger sync after reconnection to catch up on missed changes.
    This performs a full bidirectional sync to ensure data consistency.
    """
    if not should_trigger_sync():
        return {"status": "skipped", "reason": "online_server"}
    
    try:
        print("[SYNC] Reconnection sync: Performing full bidirectional sync to catch up")
        
        # Ensure sync worker is running
        ensure_sync_worker_running()
        
        # Trigger immediate bidirectional sync
        result = enhanced_bidirectional_sync()
        
        if result.get("status") == "success":
            uploaded = result.get('uploaded', 0)
            downloaded = result.get('downloaded', 0)
            total = result.get('total_changes', 0)
            print(f"[SYNC] Reconnection sync complete: ↑{uploaded} ↓{downloaded} records")
        elif result.get("status") == "no_changes":
            print("[SYNC] Reconnection sync: No changes to sync")
        else:
            print(f"[SYNC] Reconnection sync result: {result}")
            
        return result
        
    except Exception as e:
        print(f"[SYNC] Reconnection sync error: {e}")
        return {"status": "error", "error": str(e)}

def ensure_sync_worker_running():
    """
    Ensure the sync worker is running for offline clients.
    If the worker thread has died or doesn't exist, restart it.
    Thread-safe with locking.
    """
    global sync_worker_thread
    
    if not should_trigger_sync():
        return  # Online server doesn't need sync worker
    
    with sync_worker_lock:
        # Check if worker thread exists and is alive
        if sync_worker_thread is None or not sync_worker_thread.is_alive():
            print("[SYNC] Sync worker not running, starting new worker thread")
            
            # Start new worker thread
            sync_worker_thread = threading.Thread(target=enhanced_background_sync_worker, daemon=True)
            sync_worker_thread.start()
            
            print("[SYNC] New sync worker thread started successfully")
        else:
            print("[SYNC] Sync worker already running and healthy")

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

def get_last_sync_timestamp():
    """
    Get the timestamp of the last successful sync for incremental downloads.
    Returns ISO format string or None if no previous sync.
    """
    try:
        from app import db
        
        # Get the most recent successful sync timestamp from sync_queue
        result = db.session.execute(sa_text("""
            SELECT MAX(synced_at) as last_sync 
            FROM sync_queue 
            WHERE status = 'synced' AND synced_at IS NOT NULL
        """)).fetchone()
        
        if result and result[0]:
            # Return timestamp as ISO string for URL parameter
            return result[0].isoformat()
        else:
            # No previous sync found, return None for full sync
            return None
            
    except Exception as e:
        print(f"[SYNC] Error getting last sync timestamp: {e}")
        return None

def update_last_sync_timestamp():
    """
    Update a marker to track when the last successful download sync completed.
    This helps with incremental sync requests.
    """
    try:
        from app import db
        
        # Insert a marker record to track successful download sync
        now = get_timezone_aware_now()
        db.session.execute(sa_text("""
            INSERT INTO sync_queue (table_name, record_id, operation, payload, created_at, status, synced_at)
            VALUES ('_sync_marker', 0, 'download_complete', '{}', :now, 'synced', :now)
        """), {"now": now})
        
        db.session.commit()
        print(f"[SYNC] Updated last sync timestamp: {now.isoformat()}")
        
    except Exception as e:
        print(f"[SYNC] Error updating last sync timestamp: {e}")

def get_incremental_sync_since(since_timestamp):
    """
    Helper function to format timestamp for incremental sync requests.
    """
    if since_timestamp:
        return f"?since={since_timestamp}"
    return ""
