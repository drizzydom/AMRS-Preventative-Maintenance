#!/usr/bin/env python
"""
AMRS Maintenance Tracker - Windows WebView2 Application
This script launches a native Windows application with WebView2
that loads the Flask application
"""

import os
import sys
import time
import threading
import logging
import argparse
import webview
import requests
import subprocess
from pathlib import Path
import shutil
import pathlib
import secrets # Added for key generation
import local_database # Added for local DB operations
import json # For handling JSON payloads for sync

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[WEBVIEW] %(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("webview_app")

# --- BEGIN NEW API CLASS ---
class Api:
    def __init__(self):
        app_name_slug = "".join(c if c.isalnum() else "_" for c in APP_TITLE.lower())
        # Use a user-specific directory for application data
        self.data_path = Path.home() / f".{app_name_slug}_data"
        self.instance_path = self.data_path / 'instance'
        self.instance_path.mkdir(parents=True, exist_ok=True)
        
        self.token_file = self.instance_path / 'auth.token'
        self.db_key_file = self.instance_path / 'local_db.key' # For storing the DB encryption key
        self.local_db_file = self.instance_path / 'local_app.db' # Path to the SQLite DB file
        
        self.current_token = None
        self.db_encryption_key = None # Will hold the loaded/generated DB key

        logger.info(f"Token file location: {self.token_file}")
        logger.info(f"DB key file location: {self.db_key_file}")
        logger.info(f"Local DB file location: {self.local_db_file}")

        self.load_token()
        self.load_or_generate_db_key()

        # Initialize local database schema if key is available
        if self.db_encryption_key:
            try:
                local_database.create_tables(self.local_db_file, self.db_encryption_key)
                logger.info("Local database tables ensured.")
            except Exception as e:
                logger.error(f"Failed to initialize local database tables: {e}")
        else:
            logger.error("Cannot initialize local database: DB encryption key is not available.")

    def _generate_encryption_key(self):
        # Generate a 64-character hex key (32 bytes)
        return secrets.token_hex(32)

    def load_or_generate_db_key(self):
        logger.info(f"Attempting to load or generate DB encryption key from {self.db_key_file}")
        if self.db_key_file.exists():
            try:
                with open(self.db_key_file, 'r') as f:
                    key = f.read().strip()
                if len(key) == 64: # Basic validation for a 32-byte hex key
                    self.db_encryption_key = key
                    logger.info("DB encryption key loaded successfully.")
                else:
                    logger.error("DB key file exists but content is invalid. Will attempt to regenerate.")
                    self._regenerate_db_key()
            except Exception as e:
                logger.error(f"Failed to load DB encryption key: {e}. Will attempt to regenerate.")
                self._regenerate_db_key()
        else:
            logger.info(f"No DB key file found at {self.db_key_file}. Generating a new key.")
            self._regenerate_db_key()
        return self.db_encryption_key

    def _regenerate_db_key(self):
        try:
            new_key = self._generate_encryption_key()
            with open(self.db_key_file, 'w') as f:
                f.write(new_key)
            # Attempt to set file permissions to be readable/writable by owner only
            # This is platform-dependent and might not work on all OSes (e.g. Windows)
            try:
                os.chmod(self.db_key_file, 0o600) 
                logger.info(f"Set permissions for {self.db_key_file} to 600.")
            except OSError as e:
                logger.warning(f"Could not set permissions for {self.db_key_file}: {e}. This is common on Windows.")

            self.db_encryption_key = new_key
            logger.info("New DB encryption key generated and stored successfully.")
        except Exception as e:
            logger.error(f"FATAL: Failed to generate and store DB encryption key: {e}")
            # This is a critical failure. The application might not be able to proceed with local DB.
            # Consider how to handle this - perhaps by disabling offline features or exiting.
            self.db_encryption_key = None

    def store_token(self, token):
        logger.info(f"Api.store_token called. Token is {'present' if token else 'absent'}.")
        if token:
            try:
                with open(self.token_file, 'w') as f:
                    f.write(token)
                self.current_token = token
                logger.info(f"Token stored successfully at {self.token_file}")
                return {"success": True, "message": "Token stored."}
            except Exception as e:
                logger.error(f"Failed to store token: {e}")
                return {"success": False, "message": f"Failed to store token: {e}"}
        else:
            logger.warning("No token provided to store_token. Clearing existing token if any.")
            if self.token_file.exists():
                try:
                    self.token_file.unlink()
                    self.current_token = None
                    logger.info("Existing token file removed as no token was provided.")
                except Exception as e:
                    logger.error(f"Failed to remove existing token file: {e}")
            return {"success": False, "message": "No token provided."}

    def load_token(self):
        logger.info(f"Attempting to load token from {self.token_file}")
        if self.token_file.exists():
            try:
                with open(self.token_file, 'r') as f:
                    self.current_token = f.read().strip()
                if self.current_token:
                    logger.info(f"Token loaded successfully: {self.current_token[:20]}...") # Log a snippet
                else:
                    logger.info("Token file was empty. No token loaded.")
                    self.current_token = None
            except Exception as e:
                logger.error(f"Failed to load token: {e}")
                self.current_token = None
        else:
            logger.info(f"No token file found at {self.token_file}. No token loaded.")
            self.current_token = None
        return self.current_token

    def get_current_token(self):
        return self.current_token

    def clear_token(self):
        logger.info(f"Api.clear_token called. Attempting to clear token from {self.token_file}")
        if self.token_file.exists():
            try:
                self.token_file.unlink()
                self.current_token = None
                logger.info("Token cleared successfully.")
                return {"success": True, "message": "Token cleared."}
            except Exception as e:
                logger.error(f"Failed to clear token: {e}")
                return {"success": False, "message": f"Failed to clear token: {e}"}
        logger.info("No token file existed to clear.")
        return {"success": True, "message": "No token to clear."}

    def sync_with_server(self):
        logger.info("Attempting to synchronize with server...")
        if not self.current_token:
            logger.warning("No auth token available. Sync aborted.")
            return {"success": False, "message": "Authentication token not found. Please log in."}
        
        if not self.db_encryption_key or not self.local_db_file.exists():
            logger.error("Local database or encryption key not available. Sync aborted.")
            return {"success": False, "message": "Local database not configured. Cannot sync."}

        headers = {
            'Authorization': f'Bearer {self.current_token}',
            'Content-Type': 'application/json'
        }
        sync_results = {"pull": {}, "push": {}}

        # 1. PULL DATA FROM SERVER
        try:
            logger.info("Starting PULL operation from server.")
            last_sync_ts = local_database.get_last_sync_timestamp(self.local_db_file, self.db_encryption_key)
            pull_url = f"{FLASK_URL}/api/sync/pull"
            params = {}
            if last_sync_ts:
                params['last_sync_timestamp'] = last_sync_ts
            
            logger.info(f"Pulling data from {pull_url} with params: {params}")
            response = requests.get(pull_url, headers=headers, params=params, timeout=60)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully pulled data. Server timestamp: {data.get('server_timestamp')}")
                
                # Order of upserting matters due to foreign key relationships
                # Roles -> Users -> Sites -> Machines -> Parts -> AuditTasks -> MaintenanceRecords/AuditTaskCompletions
                
                if 'roles' in data:
                    for role_data in data['roles']:
                        local_database.upsert_role_from_server(self.local_db_file, self.db_encryption_key, role_data)
                    logger.info(f"Processed {len(data['roles'])} roles.")
                
                if 'users' in data:
                    for user_data in data['users']:
                        local_database.upsert_user_from_server(self.local_db_file, self.db_encryption_key, user_data)
                    logger.info(f"Processed {len(data['users'])} users.")

                if 'sites' in data:
                    for site_data in data['sites']:
                        local_database.upsert_site_from_server(self.local_db_file, self.db_encryption_key, site_data)
                    logger.info(f"Processed {len(data['sites'])} sites.")

                if 'machines' in data:
                    for machine_data in data['machines']:
                        local_database.upsert_machine_from_server(self.local_db_file, self.db_encryption_key, machine_data)
                    logger.info(f"Processed {len(data['machines'])} machines.")

                if 'parts' in data:
                    for part_data in data['parts']:
                        local_database.upsert_part_from_server(self.local_db_file, self.db_encryption_key, part_data)
                    logger.info(f"Processed {len(data['parts'])} parts.")
                
                if 'audit_tasks' in data:
                    for task_data in data['audit_tasks']:
                        local_database.upsert_audit_task_from_server(self.local_db_file, self.db_encryption_key, task_data)
                    logger.info(f"Processed {len(data['audit_tasks'])} audit tasks.")

                if 'maintenance_records' in data:
                    for record_data in data['maintenance_records']:
                        local_database.upsert_maintenance_record_from_server(self.local_db_file, self.db_encryption_key, record_data)
                    logger.info(f"Processed {len(data['maintenance_records'])} maintenance records.")
                
                if 'audit_task_completions' in data:
                    for completion_data in data['audit_task_completions']:
                        local_database.upsert_audit_task_completion_from_server(self.local_db_file, self.db_encryption_key, completion_data)
                    logger.info(f"Processed {len(data['audit_task_completions'])} audit task completions.")

                local_database.update_last_sync_timestamp(self.local_db_file, self.db_encryption_key, data['server_timestamp'])
                sync_results["pull"] = {"success": True, "message": "Pull successful", "timestamp": data['server_timestamp']}
                logger.info("PULL operation completed successfully.")
            elif response.status_code == 401:
                logger.error("Pull failed: Unauthorized (401). Token might be invalid or expired.")
                sync_results["pull"] = {"success": False, "message": "Pull failed: Unauthorized. Please log in again."}
                # Optionally, could try to clear token here or prompt re-login
            else:
                logger.error(f"Pull failed with status {response.status_code}: {response.text}")
                sync_results["pull"] = {"success": False, "message": f"Pull failed: Server error {response.status_code}"}
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Pull operation failed due to network error: {e}")
            sync_results["pull"] = {"success": False, "message": f"Pull failed: Network error - {e}"}
        except Exception as e:
            logger.error(f"An unexpected error occurred during PULL operation: {e}", exc_info=True)
            sync_results["pull"] = {"success": False, "message": f"Pull failed: Unexpected error - {e}"}

        # 2. PUSH DATA TO SERVER
        try:
            logger.info("Starting PUSH operation to server.")
            unsynced_mrs = local_database.get_unsynced_maintenance_records(self.local_db_file, self.db_encryption_key)
            unsynced_atcs = local_database.get_unsynced_audit_task_completions(self.local_db_file, self.db_encryption_key)
            
            # Get deleted records that need to be synced with server
            deleted_mrs = local_database.get_deleted_maintenance_records(self.local_db_file, self.db_encryption_key)
            deleted_atcs = local_database.get_deleted_audit_task_completions(self.local_db_file, self.db_encryption_key)

            if not unsynced_mrs and not unsynced_atcs and not deleted_mrs and not deleted_atcs:
                logger.info("No unsynced data or deletions to push.")
                sync_results["push"] = {"success": True, "message": "No data to push."}
            else:
                push_payload = {}
                if unsynced_mrs:
                    push_payload['maintenance_records'] = unsynced_mrs
                    logger.info(f"Prepared {len(unsynced_mrs)} maintenance records for push.")
                if unsynced_atcs:
                    push_payload['audit_task_completions'] = unsynced_atcs
                    logger.info(f"Prepared {len(unsynced_atcs)} audit task completions for push.")
                if deleted_mrs:
                    push_payload['deleted_maintenance_records'] = deleted_mrs
                    logger.info(f"Prepared {len(deleted_mrs)} deleted maintenance records for push.")
                if deleted_atcs:
                    push_payload['deleted_audit_task_completions'] = deleted_atcs
                    logger.info(f"Prepared {len(deleted_atcs)} deleted audit task completions for push.")

                push_url = f"{FLASK_URL}/api/sync/push"
                logger.info(f"Pushing data to {push_url}")
                response = requests.post(push_url, headers=headers, json=push_payload, timeout=60)

                if response.status_code == 200:
                    push_response_data = response.json()
                    logger.info(f"Push successful: {push_response_data.get('message')}")
                    
                    current_push_ts = local_database._get_current_timestamp_iso() # Get a consistent timestamp for updates

                    # Process results for maintenance records
                    mr_results = push_response_data.get('maintenance_records_status', [])
                    successful_mr_pushes = 0
                    for res in mr_results:
                        if res.get('success') and res.get('client_id') and res.get('server_id'):
                            local_database.update_sync_status(
                                self.local_db_file, self.db_encryption_key, 
                                'maintenance_records', res['client_id'], res['server_id'], current_push_ts
                            )
                            successful_mr_pushes += 1
                        else:
                            logger.error(f"Failed to push maintenance record (client_id: {res.get('client_id')}): {res.get('error')}")
                    logger.info(f"Successfully updated sync status for {successful_mr_pushes} maintenance records.")

                    # Process results for audit task completions
                    atc_results = push_response_data.get('audit_task_completions_status', [])
                    successful_atc_pushes = 0
                    for res in atc_results:
                        if res.get('success') and res.get('client_id') and res.get('server_id'):
                            local_database.update_sync_status(
                                self.local_db_file, self.db_encryption_key, 
                                'audit_task_completions', res['client_id'], res['server_id'], current_push_ts
                            )
                            successful_atc_pushes += 1
                        else:
                            logger.error(f"Failed to push audit task completion (client_id: {res.get('client_id')}): {res.get('error')}")
                    logger.info(f"Successfully updated sync status for {successful_atc_pushes} audit task completions.")
                    
                    # Process deletion results for maintenance records
                    mr_deletion_results = push_response_data.get('deleted_maintenance_records_status', [])
                    successful_mr_deletions = 0
                    mr_deletion_client_ids = []
                    for res in mr_deletion_results:
                        if res.get('success') and res.get('client_id'):
                            mr_deletion_client_ids.append(res.get('client_id'))
                            successful_mr_deletions += 1
                        else:
                            logger.error(f"Failed to sync deletion of maintenance record (client_id: {res.get('client_id')}): {res.get('error')}")
                    
                    if mr_deletion_client_ids:
                        cleaned_mrs = local_database.clean_up_synced_deletions(
                            self.local_db_file, self.db_encryption_key, 
                            'maintenance_records', mr_deletion_client_ids
                        )
                        logger.info(f"Permanently removed {cleaned_mrs} synced maintenance record deletions.")
                    
                    # Process deletion results for audit task completions
                    atc_deletion_results = push_response_data.get('deleted_audit_task_completions_status', [])
                    successful_atc_deletions = 0
                    atc_deletion_client_ids = []
                    for res in atc_deletion_results:
                        if res.get('success') and res.get('client_id'):
                            atc_deletion_client_ids.append(res.get('client_id'))
                            successful_atc_deletions += 1
                        else:
                            logger.error(f"Failed to sync deletion of audit task completion (client_id: {res.get('client_id')}): {res.get('error')}")
                    
                    if atc_deletion_client_ids:
                        cleaned_atcs = local_database.clean_up_synced_deletions(
                            self.local_db_file, self.db_encryption_key, 
                            'audit_task_completions', atc_deletion_client_ids
                        )
                        logger.info(f"Permanently removed {cleaned_atcs} synced audit task completion deletions.")
                    
                    # Update overall results
                    total_successful_ops = successful_mr_pushes + successful_atc_pushes + successful_mr_deletions + successful_atc_deletions
                    sync_results["push"] = {
                        "success": True, 
                        "message": f"Push successful ({total_successful_ops} operations)", 
                        "details": push_response_data
                    }
                    logger.info("PUSH operation completed successfully.")
                elif response.status_code == 401:
                    logger.error("Push failed: Unauthorized (401). Token might be invalid or expired.")
                    sync_results["push"] = {"success": False, "message": "Push failed: Unauthorized. Please log in again."}
                else:
                    logger.error(f"Push failed with status {response.status_code}: {response.text}")
                    sync_results["push"] = {"success": False, "message": f"Push failed: Server error {response.status_code}"}

        except requests.exceptions.RequestException as e:
            logger.error(f"Push operation failed due to network error: {e}")
            sync_results["push"] = {"success": False, "message": f"Push failed: Network error - {e}"}
        except Exception as e:
            logger.error(f"An unexpected error occurred during PUSH operation: {e}", exc_info=True)
            sync_results["push"] = {"success": False, "message": f"Push failed: Unexpected error - {e}"}
        
        final_success = sync_results["pull"].get("success", False) and sync_results["push"].get("success", False)
        final_message = f"Pull: {sync_results['pull']['message']}. Push: {sync_results['push']['message']}."
        logger.info(f"Synchronization attempt finished. Overall success: {final_success}. Message: {final_message}")
        return {"success": final_success, "message": final_message, "details": sync_results}

    # --- Offline-capable data access methods for UI ---
    def get_sites(self): # Renamed from get_local_sites
        logger.info("Api.get_sites called")
        if not self.db_encryption_key or not self.local_db_file.exists():
            logger.error("Local database or encryption key not available.")
            return {"success": False, "message": "Local database not configured.", "data": []}
        try:
            sites = local_database.get_all_local_records(self.local_db_file, self.db_encryption_key, 'sites')
            logger.info(f"Retrieved {len(sites)} sites from local DB.")
            return {"success": True, "message": "Sites retrieved locally.", "data": sites}
        except Exception as e:
            logger.error(f"Error getting sites: {e}", exc_info=True)
            return {"success": False, "message": f"Error getting sites: {e}", "data": []}

    def get_machines_for_site(self, site_id): # Renamed from get_local_machines_for_site
        logger.info(f"Api.get_machines_for_site called for site_id: {site_id}")
        if not self.db_encryption_key or not self.local_db_file.exists():
            logger.error("Local database or encryption key not available.")
            return {"success": False, "message": "Local database not configured.", "data": []}
        try:
            machines = local_database.get_local_records_by_fk(self.local_db_file, self.db_encryption_key, 'machines', 'site_id', site_id)
            logger.info(f"Retrieved {len(machines)} machines for site_id {site_id} from local DB.")
            return {"success": True, "message": "Machines retrieved locally.", "data": machines}
        except Exception as e:
            logger.error(f"Error getting machines for site {site_id}: {e}", exc_info=True)
            return {"success": False, "message": f"Error getting machines: {e}", "data": []}

    def get_parts_for_machine(self, machine_id): # Renamed from get_local_parts_for_machine
        logger.info(f"Api.get_parts_for_machine called for machine_id: {machine_id}")
        if not self.db_encryption_key or not self.local_db_file.exists():
            logger.error("Local database or encryption key not available.")
            return {"success": False, "message": "Local database not configured.", "data": []}
        try:
            parts = local_database.get_local_records_by_fk(self.local_db_file, self.db_encryption_key, 'parts', 'machine_id', machine_id)
            logger.info(f"Retrieved {len(parts)} parts for machine_id {machine_id} from local DB.")
            return {"success": True, "message": "Parts retrieved locally.", "data": parts}
        except Exception as e:
            logger.error(f"Error getting parts for machine {machine_id}: {e}", exc_info=True)
            return {"success": False, "message": f"Error getting parts: {e}", "data": []}

    def get_audit_tasks_for_machine(self, machine_id): # Renamed from get_local_audit_tasks_for_machine
        logger.info(f"Api.get_audit_tasks_for_machine called for machine_id: {machine_id}")
        if not self.db_encryption_key or not self.local_db_file.exists():
            logger.error("Local database or encryption key not available.")
            return {"success": False, "message": "Local database not configured.", "data": []}
        try:
            audit_tasks = local_database.get_local_records_by_fk(self.local_db_file, self.db_encryption_key, 'audit_tasks', 'machine_id', machine_id)
            logger.info(f"Retrieved {len(audit_tasks)} audit tasks for machine_id {machine_id} from local DB.")
            return {"success": True, "message": "Audit tasks retrieved locally.", "data": audit_tasks}
        except Exception as e:
            logger.error(f"Error getting audit tasks for machine {machine_id}: {e}", exc_info=True)
            return {"success": False, "message": f"Error getting audit tasks: {e}", "data": []}
            
    def get_maintenance_records_for_machine(self, machine_id): # Renamed from get_local_maintenance_records_for_machine
        logger.info(f"Api.get_maintenance_records_for_machine called for machine_id: {machine_id}")
        if not self.db_encryption_key or not self.local_db_file.exists():
            logger.error("Local database or encryption key not available.")
            return {"success": False, "message": "Local database not configured.", "data": []}
        try:
            records = local_database.get_local_records_by_fk(self.local_db_file, self.db_encryption_key, 'maintenance_records', 'machine_id', machine_id)
            logger.info(f"Retrieved {len(records)} maintenance records for machine_id {machine_id} from local DB.")
            return {"success": True, "message": "Maintenance records retrieved locally.", "data": records}
        except Exception as e:
            logger.error(f"Error getting maintenance records for machine {machine_id}: {e}", exc_info=True)
            return {"success": False, "message": f"Error getting maintenance records: {e}", "data": []}

    def get_audit_task_completions_for_task(self, audit_task_id): # Renamed from get_local_audit_task_completions_for_task
        logger.info(f"Api.get_audit_task_completions_for_task called for audit_task_id: {audit_task_id}")
        if not self.db_encryption_key or not self.local_db_file.exists():
            logger.error("Local database or encryption key not available.")
            return {"success": False, "message": "Local database not configured.", "data": []}
        try:
            completions = local_database.get_local_records_by_fk(self.local_db_file, self.db_encryption_key, 'audit_task_completions', 'audit_task_id', audit_task_id)
            logger.info(f"Retrieved {len(completions)} audit task completions for audit_task_id {audit_task_id} from local DB.")
            return {"success": True, "message": "Audit task completions retrieved locally.", "data": completions}
        except Exception as e:
            logger.error(f"Error getting audit task completions for task {audit_task_id}: {e}", exc_info=True)
            return {"success": False, "message": f"Error getting audit task completions: {e}", "data": []}

    def create_maintenance_record(self, record_data): # Renamed from create_local_maintenance_record
        logger.info(f"Api.create_maintenance_record called with data: {record_data}")
        if not self.db_encryption_key or not self.local_db_file.exists():
            logger.error("Local database or encryption key not available.")
            return {"success": False, "message": "Local database not configured."}
        try:
            required_fields = ['machine_id', 'part_id', 'description', 'user_id', 'maintenance_type']
            for field in required_fields:
                if field not in record_data:
                    logger.error(f"Missing required field: {field}")
                    return {"success": False, "message": f"Missing required field: {field}"}
            
            client_id = local_database.create_local_maintenance_record(
                self.local_db_file, self.db_encryption_key,
                record_data['machine_id'], 
                record_data['part_id'], 
                record_data['description'],
                record_data['user_id'], 
                record_data['maintenance_type'],
                record_data.get('cost'),
                record_data.get('timestamp')
            )
            if client_id:
                logger.info(f"Maintenance record created locally with client_id: {client_id}")
                return {"success": True, "message": "Maintenance record created locally.", "client_id": client_id}
            else:
                logger.error("Failed to create maintenance record locally (DB error).")
                return {"success": False, "message": "Failed to create maintenance record locally."}
        except Exception as e:
            logger.error(f"Error creating maintenance record: {e}", exc_info=True)
            return {"success": False, "message": f"Error creating maintenance record: {e}"}

    def update_maintenance_record(self, client_id: str, record_data: dict) -> dict:
        logger.info(f"Api.update_maintenance_record called for client_id: {client_id} with data: {record_data}")
        if not self.db_encryption_key or not self.local_db_file.exists():
            logger.error("Local database or encryption key not available for update.")
            return {"success": False, "message": "Local database not configured."}
        try:
            success = local_database.update_local_maintenance_record(
                self.local_db_file, self.db_encryption_key,
                client_id,
                record_data
            )
            if success:
                logger.info(f"Maintenance record (client_id: {client_id}) updated locally.")
                return {"success": True, "message": "Maintenance record updated locally."}
            else:
                # The local_database function logs specific errors (e.g., not found)
                logger.error(f"Failed to update maintenance record (client_id: {client_id}) locally.")
                return {"success": False, "message": "Failed to update maintenance record locally. Record may not exist or no valid fields provided."}
        except Exception as e:
            logger.error(f"Error updating maintenance record (client_id: {client_id}): {e}", exc_info=True)
            return {"success": False, "message": f"Error updating maintenance record: {e}"}

    def create_audit_task_completion(self, completion_data): # Renamed from create_local_audit_task_completion
        logger.info(f"Api.create_audit_task_completion called with data: {completion_data}")
        if not self.db_encryption_key or not self.local_db_file.exists():
            logger.error("Local database or encryption key not available.")
            return {"success": False, "message": "Local database not configured."}
        try:
            required_fields = ['audit_task_id', 'user_id', 'completed_date', 'status']
            for field in required_fields:
                if field not in completion_data:
                    logger.error(f"Missing required field: {field}")
                    return {"success": False, "message": f"Missing required field: {field}"}

            client_id = local_database.create_local_audit_task_completion(
                self.local_db_file, self.db_encryption_key,
                completion_data['audit_task_id'],
                completion_data['user_id'], 
                completion_data['completed_date'],
                completion_data['status'],
                completion_data.get('notes'),
                completion_data.get('completion_image_path')
            )
            if client_id:
                logger.info(f"Audit task completion created locally with client_id: {client_id}")
                return {"success": True, "message": "Audit task completion created locally.", "client_id": client_id}
            else:
                logger.error("Failed to create audit task completion locally (DB error).")
                return {"success": False, "message": "Failed to create audit task completion locally."}
        except Exception as e:
            logger.error(f"Error creating audit task completion: {e}", exc_info=True)
            return {"success": False, "message": f"Error creating audit task completion: {e}"}

    def update_audit_task_completion(self, client_id: str, completion_data: dict) -> dict:
        logger.info(f"Api.update_audit_task_completion called for client_id: {client_id} with data: {completion_data}")
        if not self.db_encryption_key or not self.local_db_file.exists():
            logger.error("Local database or encryption key not available for update.")
            return {"success": False, "message": "Local database not configured."}
        try:
            success = local_database.update_local_audit_task_completion(
                self.local_db_file, self.db_encryption_key,
                client_id,
                completion_data
            )
            if success:
                logger.info(f"Audit task completion (client_id: {client_id}) updated locally.")
                return {"success": True, "message": "Audit task completion updated locally."}
            else:
                logger.error(f"Failed to update audit task completion (client_id: {client_id}) locally.")
                return {"success": False, "message": "Failed to update audit task completion locally. Record may not exist or no valid fields provided."}
        except Exception as e:
            logger.error(f"Error updating audit task completion (client_id: {client_id}): {e}", exc_info=True)
            return {"success": False, "message": f"Error updating audit task completion: {e}"}

    def delete_maintenance_record(self, client_id: str) -> dict:
        """Deletes a maintenance record locally.
        Uses soft delete to mark it for deletion sync with the server.
        """
        logger.info(f"Api.delete_maintenance_record called for client_id: {client_id}")
        if not self.db_encryption_key or not self.local_db_file.exists():
            logger.error("Local database or encryption key not available for deletion.")
            return {"success": False, "message": "Local database not configured."}
        
        try:
            success = local_database.soft_delete_local_maintenance_record(
                self.local_db_file, self.db_encryption_key, client_id
            )
            if success:
                logger.info(f"Maintenance record (client_id: {client_id}) marked for deletion locally.")
                return {"success": True, "message": "Maintenance record marked for deletion."}
            else:
                logger.error(f"Failed to mark maintenance record (client_id: {client_id}) for deletion.")
                return {"success": False, "message": "Failed to delete maintenance record. Record may not exist."}
        except Exception as e:
            logger.error(f"Error deleting maintenance record (client_id: {client_id}): {e}", exc_info=True)
            return {"success": False, "message": f"Error deleting maintenance record: {e}"}

    def delete_audit_task_completion(self, client_id: str) -> dict:
        """Deletes an audit task completion locally.
        Uses soft delete to mark it for deletion sync with the server.
        """
        logger.info(f"Api.delete_audit_task_completion called for client_id: {client_id}")
        if not self.db_encryption_key or not self.local_db_file.exists():
            logger.error("Local database or encryption key not available for deletion.")
            return {"success": False, "message": "Local database not configured."}
        
        try:
            success = local_database.soft_delete_local_audit_task_completion(
                self.local_db_file, self.db_encryption_key, client_id
            )
            if success:
                logger.info(f"Audit task completion (client_id: {client_id}) marked for deletion locally.")
                return {"success": True, "message": "Audit task completion marked for deletion."}
            else:
                logger.error(f"Failed to mark audit task completion (client_id: {client_id}) for deletion.")
                return {"success": False, "message": "Failed to delete audit task completion. Record may not exist."}
        except Exception as e:
            logger.error(f"Error deleting audit task completion (client_id: {client_id}): {e}", exc_info=True)
            return {"success": False, "message": f"Error deleting audit task completion: {e}"}

# --- END NEW API CLASS ---

# Application configuration
APP_TITLE = "AMRS Maintenance Tracker"
FLASK_PORT = 10000
FLASK_URL = f"http://localhost:{FLASK_PORT}"
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'img', 'favicon.ico')
BOOTSTRAP_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app_bootstrap.py')

# Flask process
flask_process = None

def is_port_in_use(port):
    """Check if the port is already in use"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def start_flask():
    """Start the Flask server in a subprocess"""
    global flask_process
    
    logger.info(f"Starting Flask application on port {FLASK_PORT}")
    
    # Check if the port is already in use
    if is_port_in_use(FLASK_PORT):
        logger.info(f"Port {FLASK_PORT} is already in use, assuming Flask is running")
        return True
    
    # Start the Flask app using app_bootstrap.py or app_bootstrap.exe
    try:
        if getattr(sys, 'frozen', False):
            # Running as a PyInstaller bundle
            # First try to find app_bootstrap.exe in the main dist folder
            exe_dir = os.path.dirname(sys.executable)
            
            # Check multiple possible locations for app_bootstrap.exe
            possible_paths = [
                os.path.abspath(os.path.join(exe_dir, 'app_bootstrap', 'app_bootstrap.exe')),  # inside app_bootstrap subfolder
                os.path.abspath(os.path.join(os.path.dirname(exe_dir), 'app_bootstrap', 'app_bootstrap.exe')),  # parallel to webview_app folder
                os.path.abspath(os.path.join(exe_dir, '..', 'app_bootstrap', 'app_bootstrap.exe')),  # up one level
                os.path.abspath(os.path.join(exe_dir, '..', '..', 'app_bootstrap')),  # up two levels
                os.path.abspath(os.path.join(exe_dir, 'app_bootstrap.exe'))  # directly in same folder
            ]
            
            bootstrap_exe = None
            for path in possible_paths:
                logger.info(f"[WEBVIEW] Checking for app_bootstrap.exe at: {path}")
                if os.path.exists(path):
                    bootstrap_exe = path
                    logger.info(f"[WEBVIEW] Found app_bootstrap.exe at: {bootstrap_exe}")
                    break
            
            if not bootstrap_exe:
                # Last resort: search the disk
                logger.info("[WEBVIEW] Searching for app_bootstrap.exe in parent directories...")
                current_dir = exe_dir
                max_levels = 5  # Don't search too high up
                for _ in range(max_levels):
                    app_bootstrap_dir = os.path.join(current_dir, 'app_bootstrap')
                    if os.path.exists(app_bootstrap_dir):
                        bootstrap_exe = os.path.join(app_bootstrap_dir, 'app_bootstrap.exe')
                        if os.path.exists(bootstrap_exe):
                            logger.info(f"[WEBVIEW] Found app_bootstrap.exe at: {bootstrap_exe}")
                            break
                    # Move up one directory
                    parent_dir = os.path.dirname(current_dir)
                    if parent_dir == current_dir:  # Reached root directory
                        break
                    current_dir = parent_dir
            
            if not bootstrap_exe:
                logger.error("app_bootstrap.exe not found in any expected location")
                raise RuntimeError("app_bootstrap.exe not found in any expected location")
                
            cmd = [bootstrap_exe, '--port', str(FLASK_PORT)]
        else:
            python_exe = sys.executable
            bootstrap_script = BOOTSTRAP_SCRIPT
            cmd = [python_exe, bootstrap_script, '--port', str(FLASK_PORT)]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        # Start process with output redirected to PIPE
        flask_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Start a thread to read and log the output
        def log_output():
            for line in iter(flask_process.stdout.readline, ''):
                logger.info(f"[FLASK] {line.rstrip()}")
        
        threading.Thread(target=log_output, daemon=True).start()
        
        # Wait for Flask to start
        logger.info("Waiting for Flask to start...")
        max_retries = 30
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                response = requests.get(f"{FLASK_URL}/health-check", timeout=1)
                if response.status_code == 200:
                    logger.info("Flask application is running")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            retry_count += 1
            time.sleep(1)
        
        logger.error(f"Flask application failed to start after {max_retries} seconds")
        return False
    
    except Exception as e:
        logger.error(f"Error starting Flask application: {e}")
        return False

def shutdown_flask():
    """Shutdown the Flask server subprocess"""
    global flask_process
    if flask_process:
        logger.info("Shutting down Flask application")
        try:
            # Try to terminate gracefully
            flask_process.terminate()
            flask_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # If it doesn't shut down, kill it
            logger.warning("Flask application did not terminate gracefully, killing process")
            flask_process.kill()
        
        flask_process = None

def on_closed():
    """Handle window closed event"""
    logger.info("WebView window closed")
    shutdown_flask()

def on_shown():
    """Handle window shown event"""
    logger.info("WebView window shown")

def on_new_window(url):
    """Handle new window requests (e.g., print view) by opening inside the app"""
    logger.info(f"Opening new window for URL: {url}")
    webview.create_window('Print View', url)

def wait_for_flask(url, timeout=60):
    """Wait for Flask to be ready"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False

def start_app():
    """Start the application with splash screen"""
    # Get splash screen HTML path
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        splash_path = os.path.join(exe_dir, 'static', 'splash.html')
        if not os.path.exists(splash_path):
            splash_path = os.path.abspath(os.path.join('static', 'splash.html'))
    else:
        splash_path = os.path.abspath(os.path.join('static', 'splash.html'))
    logger.info(f"[WEBVIEW] Final splash path: {splash_path} (exists: {os.path.exists(splash_path)})")

    # Instantiate API for JS interaction
    api = Api() # This will also attempt to load_token
    logger.info(f"Initial token loaded by Api: {'TOKEN PRESENT' if api.get_current_token() else 'NO TOKEN'}.")

    # Create a splash window that will be replaced with the main window
    splash_html = ''
    if os.path.exists(splash_path):
        with open(splash_path, 'r') as f:
            splash_html = f.read()
    else:
        splash_html = '<html><body style="background-color: #333; color: white; font-family: Arial; display: flex; align-items: center; justify-content: center;"><h1>AMRS Maintenance Tracker</h1><p>Loading...</p></body></html>'

    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()
    
    # Show splash window
    splash_window = webview.create_window('Loading...', html=splash_html, width=600, height=400, resizable=False, frameless=True)
    
    def on_splash_shown_handler(): # Renamed for clarity
        logger.info("[WEBVIEW] Splash screen shown, waiting for Flask...")
        
        def check_flask_ready_and_launch_main(): # Renamed for clarity
            if wait_for_flask(f"{FLASK_URL}/health-check"):
                logger.info("[WEBVIEW] Flask is ready, switching to main window.")
                # Create the main window and pass the api instance
                main_window = webview.create_window(
                    APP_TITLE,
                    FLASK_URL,
                    width=WINDOW_WIDTH,
                    height=WINDOW_HEIGHT,
                    js_api=api  # Pass the API object here
                )
                # Ensure main window closure also triggers flask shutdown if not already handled globally
                # main_window.events.closed += on_closed # The global on_closed should cover this.

                # Destroy splash window after a slight delay to ensure main window is visible
                def destroy_splash_task(): # Renamed for clarity
                    time.sleep(0.5)
                    logger.info("[WEBVIEW] Destroying splash screen.")
                    splash_window.destroy()
                threading.Thread(target=destroy_splash_task, daemon=True).start()
            else:
                logger.error("[WEBVIEW] Flask did not start in time, showing error.")
                splash_window.destroy() # Destroy splash before showing error window
                webview.create_window('Error', html='<h1>Failed to start backend application. Please restart.</h1>', width=500, height=200)
        
        # Check Flask in a background thread to avoid blocking UI
        threading.Thread(target=check_flask_ready_and_launch_main, daemon=True).start()
    
    # Register the shown event handler for the splash window
    splash_window.events.shown += on_splash_shown_handler
    
    logger.info("[WEBVIEW] Starting webview event loop with manual splash screen...")
    webview.start(gui='edgechromium', debug=True, private_mode=False) # private_mode=False is default

def main():
    """Main entry point for the application"""
    # Create the API object which handles token and DB key management
    api = Api()

    # Ensure Flask server is started
    start_flask()

    # Create and show the webview window
    try:
        webview.create_window(
            APP_TITLE,
            FLASK_URL,
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT,
            resizable=True,
            js_api=api,  # Expose the Api class to JavaScript
        )
        webview.start(debug=True, gui='cef', http_server=False, private_mode=False) # Added private_mode=False
    except Exception as e:
        logger.error(f"Failed to create or start webview window: {e}")
    finally:
        # Clean up: terminate Flask process and close DB connection
        if flask_process:
            logger.info("Terminating Flask process...")
            flask_process.terminate()
            flask_process.wait()
            logger.info("Flask process terminated.")
        
        local_database.close_db_connection() # Close local DB connection
        logger.info("webview_app.py finished.")

if __name__ == "__main__":
    main()