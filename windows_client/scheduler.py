"""
Scheduler module for maintenance reminders and other scheduled tasks
"""
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

class MaintenanceScheduler:
    """
    Manages scheduled maintenance reminders and recurring tasks
    """
    
    def __init__(self, offline_db, notification_manager=None):
        """
        Initialize the maintenance scheduler
        
        Args:
            offline_db: Local database instance
            notification_manager: Optional notification manager for alerts
        """
        self.db = offline_db
        self.notification_manager = notification_manager
        self.logger = logging.getLogger("MaintenanceScheduler")
        
        # Initialize background scheduler
        self.scheduler = BackgroundScheduler(
            jobstores={'default': MemoryJobStore()}
        )
        
        # Track callbacks for maintenance events
        self.maintenance_due_callbacks = []
        self.scheduler_event_callbacks = []
        
        # Add event listeners
        self.scheduler.add_listener(self._job_event_listener, 
                                   EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    
    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            self.logger.info("Maintenance scheduler started")
            
            # Load existing maintenance schedules
            self._load_maintenance_schedules()
            
            # Add the daily maintenance check job
            self._schedule_daily_maintenance_check()
    
    def shutdown(self):
        """Shutdown the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.logger.info("Maintenance scheduler shutdown")
    
    def _load_maintenance_schedules(self):
        """Load maintenance schedules from database"""
        try:
            schedules = self.db.get_maintenance_schedules()
            
            if not schedules:
                self.logger.info("No maintenance schedules found in database")
                return
                
            self.logger.info(f"Loading {len(schedules)} maintenance schedules")
            
            for schedule in schedules:
                self._schedule_maintenance_reminder(schedule)
                
        except Exception as e:
            self.logger.error(f"Error loading maintenance schedules: {e}", exc_info=True)
    
    def _schedule_daily_maintenance_check(self):
        """Schedule the daily maintenance check job"""
        # Run once at startup and then daily at 7:00 AM
        self.scheduler.add_job(
            self._check_upcoming_maintenance,
            'cron',
            hour=7,
            minute=0,
            id='daily_maintenance_check',
            replace_existing=True
        )
        
        # Also run immediately
        self.scheduler.add_job(
            self._check_upcoming_maintenance,
            'date',
            run_date=datetime.now() + timedelta(seconds=30),
            id='initial_maintenance_check',
            replace_existing=True
        )
    
    def _check_upcoming_maintenance(self):
        """Check for upcoming maintenance tasks"""
        try:
            # Get maintenance schedules due in the next 48 hours
            now = datetime.now()
            upcoming = self.db.get_upcoming_maintenance(days=2)
            
            if not upcoming:
                self.logger.debug("No upcoming maintenance in next 48 hours")
                return
                
            self.logger.info(f"Found {len(upcoming)} upcoming maintenance tasks")
            
            # Process each upcoming task
            for task in upcoming:
                # Calculate how soon the maintenance is due
                due_date = datetime.fromisoformat(task.get('next_due', now.isoformat()))
                hours_remaining = (due_date - now).total_seconds() / 3600
                
                if hours_remaining <= 0:
                    # Overdue
                    self._notify_maintenance_due(task, is_overdue=True)
                elif hours_remaining <= 24:
                    # Due within 24 hours
                    self._notify_maintenance_due(task, is_overdue=False)
                
        except Exception as e:
            self.logger.error(f"Error checking upcoming maintenance: {e}", exc_info=True)
    
    def _notify_maintenance_due(self, task, is_overdue=False):
        """Send notification for maintenance due soon or overdue"""
        try:
            # Extract information
            part_id = task.get('part_id')
            part_name = task.get('part_name', f"Part #{part_id}")
            machine_name = task.get('machine_name', 'Unknown machine')
            site_name = task.get('site_name', 'Unknown location')
            
            # Create message
            if is_overdue:
                title = f"OVERDUE: Maintenance for {part_name}"
                message = f"Maintenance is OVERDUE for {part_name} on {machine_name} at {site_name}."
            else:
                title = f"Maintenance Due: {part_name}"
                message = f"Maintenance is due soon for {part_name} on {machine_name} at {site_name}."
            
            # Send notification if available
            if self.notification_manager:
                self.notification_manager.send_notification(
                    title=title,
                    message=message,
                    category='maintenance',
                    data=task
                )
            
            # Invoke callbacks
            for callback in self.maintenance_due_callbacks:
                try:
                    callback(task, is_overdue)
                except Exception as cb_error:
                    self.logger.error(f"Error in maintenance callback: {cb_error}")
                
        except Exception as e:
            self.logger.error(f"Error notifying maintenance due: {e}", exc_info=True)
    
    def _schedule_maintenance_reminder(self, schedule):
        """Schedule a specific maintenance reminder"""
        try:
            # Extract schedule information
            schedule_id = schedule.get('id')
            next_due = schedule.get('next_due')
            
            if not next_due:
                self.logger.warning(f"Schedule {schedule_id} has no next_due date")
                return
                
            # Parse the due date
            due_date = datetime.fromisoformat(next_due)
            
            # Skip if already past due
            if due_date < datetime.now():
                self.logger.debug(f"Schedule {schedule_id} is already past due: {next_due}")
                return
            
            # Schedule at due date minus advance notice time
            advance_notice_hours = schedule.get('advance_notice_hours', 24)
            reminder_time = due_date - timedelta(hours=advance_notice_hours)
            
            # Don't schedule in the past
            if reminder_time < datetime.now():
                reminder_time = datetime.now() + timedelta(minutes=2)
            
            # Add job with the schedule ID
            job_id = f"maintenance_{schedule_id}"
            
            self.scheduler.add_job(
                self._maintenance_reminder_job,
                'date',
                run_date=reminder_time,
                args=[schedule],
                id=job_id,
                replace_existing=True
            )
            
            self.logger.info(f"Scheduled reminder for {due_date} (ID: {schedule_id})")
            
        except Exception as e:
            self.logger.error(f"Error scheduling maintenance reminder: {e}", exc_info=True)
    
    def _maintenance_reminder_job(self, schedule):
        """Job function for maintenance reminders"""
        try:
            # Get updated schedule to ensure it's still relevant
            schedule_id = schedule.get('id')
            updated_schedule = self.db.get_maintenance_schedule(schedule_id)
            
            if not updated_schedule:
                self.logger.warning(f"Schedule {schedule_id} no longer exists")
                return
                
            # Check if still due (might have been completed)
            next_due = updated_schedule.get('next_due')
            if not next_due:
                self.logger.info(f"Schedule {schedule_id} no longer has a due date")
                return
                
            due_date = datetime.fromisoformat(next_due)
            
            # If within 48 hours, send notification
            now = datetime.now()
            hours_until_due = (due_date - now).total_seconds() / 3600
            
            if hours_until_due <= 48:
                self._notify_maintenance_due(updated_schedule, is_overdue=(hours_until_due <= 0))
                
        except Exception as e:
            self.logger.error(f"Error in maintenance reminder job: {e}", exc_info=True)
    
    def schedule_maintenance(self, part_id, interval_days, next_due=None, advance_notice_hours=24):
        """
        Schedule maintenance for a part
        
        Args:
            part_id: ID of the part to schedule maintenance for
            interval_days: Maintenance interval in days
            next_due: Next due date (datetime or ISO string), or None for interval from now
            advance_notice_hours: Hours before due date to send advance notice
            
        Returns:
            Schedule ID if successful, None otherwise
        """
        try:
            # Get part information
            part_data = self.db.get_part_data(part_id)
            if not part_data:
                self.logger.warning(f"Part {part_id} not found")
                return None
                
            # Calculate next due date if not provided
            if not next_due:
                next_due = datetime.now() + timedelta(days=interval_days)
            elif isinstance(next_due, str):
                next_due = datetime.fromisoformat(next_due)
            
            # Create schedule record
            schedule = {
                'part_id': part_id,
                'interval_days': interval_days,
                'next_due': next_due.isoformat(),
                'advance_notice_hours': advance_notice_hours,
                'created_at': datetime.now().isoformat(),
                'schedule_type': 'interval',
                'schedule_data': json.dumps({
                    'interval': interval_days,
                    'unit': 'days'
                })
            }
            
            # Store in database
            schedule_id = self.db.store_maintenance_schedule(schedule)
            
            if not schedule_id:
                self.logger.error("Failed to store maintenance schedule")
                return None
                
            # Update schedule with ID and create a reminder
            schedule['id'] = schedule_id
            self._schedule_maintenance_reminder(schedule)
            
            return schedule_id
            
        except Exception as e:
            self.logger.error(f"Error scheduling maintenance: {e}", exc_info=True)
            return None
    
    def update_schedule(self, schedule_id, interval_days=None, next_due=None, advance_notice_hours=None):
        """
        Update an existing maintenance schedule
        
        Args:
            schedule_id: ID of the schedule to update
            interval_days: New interval days, or None to keep current
            next_due: New next due date, or None to keep current
            advance_notice_hours: New advance notice hours, or None to keep current
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current schedule
            schedule = self.db.get_maintenance_schedule(schedule_id)
            if not schedule:
                self.logger.warning(f"Schedule {schedule_id} not found")
                return False
                
            # Update fields
            updates = {}
            
            if interval_days is not None:
                updates['interval_days'] = interval_days
                updates['schedule_data'] = json.dumps({
                    'interval': interval_days,
                    'unit': 'days'
                })
                
            if next_due is not None:
                if isinstance(next_due, str):
                    updates['next_due'] = next_due
                else:
                    updates['next_due'] = next_due.isoformat()
                    
            if advance_notice_hours is not None:
                updates['advance_notice_hours'] = advance_notice_hours
            
            if not updates:
                return True  # No changes needed
                
            # Update in database
            success = self.db.update_maintenance_schedule(schedule_id, updates)
            
            if not success:
                self.logger.error(f"Failed to update schedule {schedule_id}")
                return False
                
            # Re-schedule the reminder with updated information
            updated_schedule = self.db.get_maintenance_schedule(schedule_id)
            if updated_schedule:
                # Remove old job
                job_id = f"maintenance_{schedule_id}"
                self.scheduler.remove_job(job_id, jobstore='default', ignore_nomatches=True)
                
                # Schedule new reminder
                self._schedule_maintenance_reminder(updated_schedule)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating schedule: {e}", exc_info=True)
            return False
    
    def delete_schedule(self, schedule_id):
        """
        Delete a maintenance schedule
        
        Args:
            schedule_id: ID of the schedule to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete from database
            success = self.db.delete_maintenance_schedule(schedule_id)
            
            if not success:
                self.logger.error(f"Failed to delete schedule {schedule_id}")
                return False
                
            # Remove scheduled job
            job_id = f"maintenance_{schedule_id}"
            self.scheduler.remove_job(job_id, jobstore='default', ignore_nomatches=True)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting schedule: {e}", exc_info=True)
            return False
    
    def record_maintenance_completion(self, part_id, completion_date=None, notes=None):
        """
        Record completion of maintenance for a part
        
        Args:
            part_id: ID of the part maintained
            completion_date: Date of completion or None for current time
            notes: Optional notes about the maintenance
            
        Returns:
            Tuple of (success, maintenance record ID, updated schedule ID)
        """
        try:
            # Default to current time if no completion date provided
            if not completion_date:
                completion_date = datetime.now()
            elif isinstance(completion_date, str):
                completion_date = datetime.fromisoformat(completion_date)
                
            # Get part data
            part_data = self.db.get_part_data(part_id)
            if not part_data:
                self.logger.warning(f"Part {part_id} not found")
                return False, None, None
                
            # Create maintenance record
            record = {
                'part_id': part_id,
                'timestamp': completion_date.isoformat(),
                'data': {
                    'notes': notes or '',
                    'is_preventative': True
                }
            }
            
            # Store maintenance record
            record_id = self.db.store_maintenance(record)
            
            if not record_id:
                self.logger.error("Failed to store maintenance record")
                return False, None, None
                
            # Find and update maintenance schedule for this part
            schedule = self.db.get_part_maintenance_schedule(part_id)
            
            if schedule:
                schedule_id = schedule['id']
                interval_days = int(schedule.get('interval_days', 30))
                
                # Calculate next due date based on completion
                next_due = completion_date + timedelta(days=interval_days)
                
                # Update schedule
                success = self.update_schedule(
                    schedule_id,
                    next_due=next_due
                )
                
                if not success:
                    self.logger.warning(f"Failed to update schedule after maintenance completion")
                
                return True, record_id, schedule_id
            
            return True, record_id, None
            
        except Exception as e:
            self.logger.error(f"Error recording maintenance completion: {e}", exc_info=True)
            return False, None, None
    
    def add_maintenance_due_callback(self, callback):
        """
        Add a callback for maintenance due events
        
        Args:
            callback: Function to call with (task, is_overdue) parameters
        """
        if callback not in self.maintenance_due_callbacks:
            self.maintenance_due_callbacks.append(callback)
    
    def remove_maintenance_due_callback(self, callback):
        """Remove a maintenance due callback"""
        if callback in self.maintenance_due_callbacks:
            self.maintenance_due_callbacks.remove(callback)
    
    def _job_event_listener(self, event):
        """Handle job execution events"""
        try:
            # Notify callbacks about job events
            for callback in self.scheduler_event_callbacks:
                try:
                    callback(event)
                except Exception as cb_error:
                    self.logger.error(f"Error in scheduler event callback: {cb_error}")
                    
        except Exception as e:
            self.logger.error(f"Error in job event listener: {e}", exc_info=True)
