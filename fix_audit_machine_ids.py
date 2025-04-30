#!/usr/bin/env python
"""
Fix audit task completions that have missing or incorrect machine_id values.
This script identifies audit task completions that don't have proper machine ID associations
and attempts to repair them by finding the correct machine IDs.

Running this script should resolve issues with machine names not appearing in the audit history.
"""
import sys
import logging
from datetime import datetime

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def diagnose_and_repair_audit_machine_ids():
    """
    Identify and fix audit task completions with missing machine IDs.
    """
    try:
        logger.info("Starting audit completion machine ID diagnostics...")
        
        # Import models inside function to ensure app context is available
        from app import app, db
        from models import AuditTaskCompletion, AuditTask, Machine
        
        # Run within app context
        with app.app_context():
            # Get statistics
            total_completions = AuditTaskCompletion.query.count()
            valid_completions = AuditTaskCompletion.query.filter(
                AuditTaskCompletion.machine_id != None
            ).count()
            
            logger.info(f"Found {total_completions} total audit task completions")
            logger.info(f"Found {valid_completions} completions with valid machine IDs")
            logger.info(f"Found {total_completions - valid_completions} completions with missing machine IDs")
            
            # Check if any repairs needed
            if total_completions == valid_completions:
                logger.info("All audit completions have valid machine IDs. No repairs needed.")
                return True
                
            # Find completions with missing machine IDs
            missing_machine_id_completions = AuditTaskCompletion.query.filter(
                AuditTaskCompletion.machine_id == None
            ).all()
            
            # Count repairs
            repaired_count = 0
            
            # Attempt to repair completions with missing machine IDs
            for completion in missing_machine_id_completions:
                # Get the audit task this completion is for
                audit_task = AuditTask.query.get(completion.audit_task_id)
                if not audit_task:
                    logger.warning(f"Completion {completion.id} has invalid audit_task_id {completion.audit_task_id}")
                    continue
                    
                # Check if audit task has machines associated
                if not audit_task.machines:
                    logger.warning(f"Audit task {audit_task.id} ({audit_task.name}) has no machines associated")
                    continue
                    
                # If only one machine is associated with the audit task, use that
                if len(audit_task.machines) == 1:
                    completion.machine_id = audit_task.machines[0].id
                    logger.info(f"Assigned machine_id {completion.machine_id} to completion {completion.id} (single machine)")
                    repaired_count += 1
                else:
                    # Multiple machines - try to find a logical match
                    # For now, just use the first one as a default
                    # You can enhance this with more sophisticated matching logic if needed
                    completion.machine_id = audit_task.machines[0].id
                    logger.info(f"Assigned machine_id {completion.machine_id} to completion {completion.id} (first of multiple)")
                    repaired_count += 1
                    
            # Commit changes if any repairs were made
            if repaired_count > 0:
                db.session.commit()
                logger.info(f"Successfully repaired {repaired_count} audit task completions")
            else:
                logger.info("No repairs were needed or possible")
            
            # Update completion timestamps for any that are missing them
            missing_timestamp_completions = AuditTaskCompletion.query.filter(
                AuditTaskCompletion.completed == True,
                AuditTaskCompletion.completed_at == None
            ).all()
            
            timestamp_fixed = 0
            for completion in missing_timestamp_completions:
                completion.completed_at = completion.created_at or datetime.utcnow()
                timestamp_fixed += 1
                
            if timestamp_fixed > 0:
                db.session.commit()
                logger.info(f"Fixed completed_at timestamps for {timestamp_fixed} completions")
            
            # Check for any AuditTask entries with no machines assigned
            tasks_without_machines = AuditTask.query.filter(~AuditTask.machines.any()).all()
            if tasks_without_machines:
                logger.warning(f"Found {len(tasks_without_machines)} audit tasks with no machines assigned:")
                for task in tasks_without_machines:
                    logger.warning(f"  - Task ID {task.id}: {task.name} (Site ID: {task.site_id})")
            
            # Verify repairs
            invalid_completions_after = AuditTaskCompletion.query.filter(
                AuditTaskCompletion.machine_id == None
            ).count()
            
            logger.info(f"After repairs: {invalid_completions_after} completions still have missing machine IDs")
            if invalid_completions_after > 0:
                logger.warning("Some completions could not be repaired - they may need manual intervention")
            
            return repaired_count > 0
        
    except Exception as e:
        logger.error(f"Error diagnosing and repairing audit machine IDs: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = diagnose_and_repair_audit_machine_ids()
    if success:
        print("Audit machine ID repair completed successfully")
    else:
        print("Audit machine ID repair encountered errors")
        sys.exit(1)