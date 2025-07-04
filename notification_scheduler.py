import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import or_

# Add the app directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, mail
from models import User, Site, Machine, Part, AuditTask, AuditTaskCompletion
from flask_mail import Message
from flask import render_template

def get_maintenance_due(site):
    """Get overdue and due soon parts for a site"""
    now = datetime.utcnow()
    overdue_parts = []
    due_soon_parts = []
    
    for machine in site.machines:
        for part in machine.parts:
            days_until = (part.next_maintenance - now).days
            if days_until < 0:
                overdue_parts.append(part)
            elif days_until <= site.notification_threshold:
                due_soon_parts.append(part)
    
    return overdue_parts, due_soon_parts

def send_daily_digest():
    """Send daily digest emails to users who have selected this frequency"""
    print(f"Running daily digest at {datetime.now()}")
    
    with app.app_context():
        # Get all users who have enabled email notifications and selected daily frequency
        users = User.query.filter(
            User.email.isnot(None),
            User.notification_preferences.contains({"enable_email": True, "email_frequency": "daily"})
        ).all()
        
        for user in users:
            # Get all sites assigned to this user
            sites = user.sites
            
            # Skip if user has no sites assigned
            if not sites:
                continue
                
            # Check notification types the user wants to receive
            preferences = user.get_notification_preferences()
            notification_types = preferences.get('notification_types', ['overdue', 'due_soon'])
            
            # Collect all parts needing attention across all sites
            all_overdue = []
            all_due_soon = []
            
            for site in sites:
                if not site.enable_notifications:
                    continue
                # Per-site notification preference check
                site_prefs = preferences.get('site_notifications', {})
                if str(site.id) in site_prefs and not site_prefs[str(site.id)]:
                    continue
                overdue, due_soon = get_maintenance_due(site)
                if 'overdue' in notification_types:
                    all_overdue.extend(overdue)
                if 'due_soon' in notification_types:
                    all_due_soon.extend(due_soon)
            
            # Skip if no parts need attention
            if not all_overdue and not all_due_soon:
                continue
                
            # Prepare and send email
            subject = f"Daily Maintenance Digest - {datetime.now().strftime('%Y-%m-%d')}"
            html = render_template(
                'email/maintenance_digest.html',
                user=user,
                overdue_parts=all_overdue,
                due_soon_parts=all_due_soon,
                digest_type='Daily'
            )
            
            try:
                with app.app_context():
                    msg = Message(subject=subject,
                                 recipients=[user.email],
                                 html=html,
                                 sender=app.config['MAIL_DEFAULT_SENDER'])
                    mail.send(msg)
                    print(f"Sent daily digest to {user.email}")
            except Exception as e:
                print(f"Failed to send daily digest to {user.email}: {str(e)}")

def send_weekly_digest():
    """Send weekly digest emails to users who have selected this frequency"""
    print(f"Running weekly digest at {datetime.now()}")
    
    with app.app_context():
        # Get all users who have enabled email notifications and selected weekly frequency
        users = User.query.filter(
            User.email.isnot(None),
            User.notification_preferences.contains({"enable_email": True, "email_frequency": "weekly"})
        ).all()
        
        for user in users:
            # Similar logic to daily digest but for weekly frequency
            sites = user.sites
            if not sites:
                continue
                
            preferences = user.get_notification_preferences()
            notification_types = preferences.get('notification_types', ['overdue', 'due_soon'])
            
            all_overdue = []
            all_due_soon = []
            
            for site in sites:
                if not site.enable_notifications:
                    continue
                # Per-site notification preference check
                site_prefs = preferences.get('site_notifications', {})
                if str(site.id) in site_prefs and not site_prefs[str(site.id)]:
                    continue
                overdue, due_soon = get_maintenance_due(site)
                if 'overdue' in notification_types:
                    all_overdue.extend(overdue)
                if 'due_soon' in notification_types:
                    all_due_soon.extend(due_soon)
            
            if not all_overdue and not all_due_soon:
                continue
                
            subject = f"Weekly Maintenance Digest - {datetime.now().strftime('%Y-%m-%d')}"
            html = render_template(
                'email/maintenance_digest.html',
                user=user,
                overdue_parts=all_overdue,
                due_soon_parts=all_due_soon,
                digest_type='Weekly'
            )
            
            try:
                with app.app_context():
                    msg = Message(subject=subject,
                                 recipients=[user.email],
                                 html=html,
                                 sender=app.config['MAIL_DEFAULT_SENDER'])
                    mail.send(msg)
                    print(f"Sent weekly digest to {user.email}")
            except Exception as e:
                print(f"Failed to send weekly digest to {user.email}: {str(e)}")

def send_audit_reminders():
    """Send audit reminder emails for incomplete audit tasks at end of day."""
    print(f"Running audit reminders at {datetime.now()}")
    with app.app_context():
        today = datetime.utcnow().date()
        # Get all audit tasks
        audit_tasks = AuditTask.query.all()
        for task in audit_tasks:
            site = db.session.get(Site, task.site_id)
            if not site or not site.enable_notifications:
                continue
            # Find site owner(s) (users assigned to the site)
            site_users = site.users
            for machine in task.machines:
                # Check if today's completion exists and is completed
                completion = AuditTaskCompletion.query.filter_by(
                    audit_task_id=task.id, machine_id=machine.id, date=today
                ).first()
                if not completion or not completion.completed:
                    # Send reminder to all users with audit reminders enabled
                    for user in site_users:
                        prefs = user.get_notification_preferences()
                        if not prefs.get('enable_email', True):
                            continue
                        if not prefs.get('audit_reminders', True):
                            continue
                        # Per-site notification preference check
                        site_prefs = prefs.get('site_notifications', {})
                        if str(site.id) in site_prefs and not site_prefs[str(site.id)]:
                            continue
                        subject = f"Audit Task Reminder: {task.name} for {machine.name}"
                        html = render_template(
                            'email/audit_reminder.html',
                            user=user,
                            task=task,
                            machine=machine,
                            site=site,
                            date=today
                        )
                        try:
                            msg = Message(subject=subject,
                                         recipients=[user.email],
                                         html=html,
                                         sender=app.config['MAIL_DEFAULT_SENDER'])
                            mail.send(msg)
                            print(f"Sent audit reminder to {user.email} for {machine.name}")
                        except Exception as e:
                            print(f"Failed to send audit reminder to {user.email}: {str(e)}")

def send_immediate_notifications():
    """Send immediate notifications for users who want them."""
    with app.app_context():
        users = User.query.filter(
            User.email.isnot(None),
            User.notification_preferences.contains({"enable_email": True, "notification_frequency": "immediate"})
        ).all()
        for user in users:
            preferences = user.get_notification_preferences()
            notification_types = preferences.get('notification_types', ['overdue', 'due_soon'])
            for site in user.sites:
                if not site.enable_notifications:
                    continue
                # Per-site notification preference check
                site_prefs = preferences.get('site_notifications', {})
                if str(site.id) in site_prefs and not site_prefs[str(site.id)]:
                    continue
                overdue, due_soon = get_maintenance_due(site)
                if 'overdue' in notification_types and overdue:
                    subject = f"Immediate Maintenance Alert - Overdue Items"
                    html = render_template(
                        'email/maintenance_alert.html',
                        user=user,
                        overdue_parts=overdue,
                        due_soon_parts=[],
                        site=site
                    )
                    try:
                        msg = Message(subject=subject,
                                     recipients=[user.email],
                                     html=html,
                                     sender=app.config['MAIL_DEFAULT_SENDER'])
                        mail.send(msg)
                        print(f"Sent immediate overdue alert to {user.email}")
                    except Exception as e:
                        print(f"Failed to send immediate alert to {user.email}: {str(e)}")
                if 'due_soon' in notification_types and due_soon:
                    subject = f"Immediate Maintenance Alert - Due Soon Items"
                    html = render_template(
                        'email/maintenance_alert.html',
                        user=user,
                        overdue_parts=[],
                        due_soon_parts=due_soon,
                        site=site
                    )
                    try:
                        msg = Message(subject=subject,
                                     recipients=[user.email],
                                     html=html,
                                     sender=app.config['MAIL_DEFAULT_SENDER'])
                        mail.send(msg)
                        print(f"Sent immediate due soon alert to {user.email}")
                    except Exception as e:
                        print(f"Failed to send immediate alert to {user.email}: {str(e)}")

def send_monthly_digest():
    """Send monthly digest emails to users who have selected this frequency."""
    print(f"Running monthly digest at {datetime.now()}")
    with app.app_context():
        users = User.query.filter(
            User.email.isnot(None),
            User.notification_preferences.contains({"enable_email": True, "notification_frequency": "monthly"})
        ).all()
        for user in users:
            sites = user.sites
            if not sites:
                continue
            preferences = user.get_notification_preferences()
            notification_types = preferences.get('notification_types', ['overdue', 'due_soon'])
            all_overdue = []
            all_due_soon = []
            for site in sites:
                if not site.enable_notifications:
                    continue
                # Per-site notification preference check
                site_prefs = preferences.get('site_notifications', {})
                if str(site.id) in site_prefs and not site_prefs[str(site.id)]:
                    continue
                overdue, due_soon = get_maintenance_due(site)
                if 'overdue' in notification_types:
                    all_overdue.extend(overdue)
                if 'due_soon' in notification_types:
                    all_due_soon.extend(due_soon)
            if not all_overdue and not all_due_soon:
                continue
            subject = f"Monthly Maintenance Digest - {datetime.now().strftime('%Y-%m-%d')}"
            html = render_template(
                'email/maintenance_digest.html',
                user=user,
                overdue_parts=all_overdue,
                due_soon_parts=all_due_soon,
                digest_type='Monthly'
            )
            try:
                msg = Message(subject=subject,
                             recipients=[user.email],
                             html=html,
                             sender=app.config['MAIL_DEFAULT_SENDER'])
                mail.send(msg)
                print(f"Sent monthly digest to {user.email}")
            except Exception as e:
                print(f"Failed to send monthly digest to {user.email}: {str(e)}")

# Add function to save audit completions at end of day
def save_daily_audit_status(app):
    """
    Save the status of audit tasks at the end of each day to maintain a history.
    This ensures we have a record of which audits were completed each day.
    """
    with app.app_context():
        from models import db, AuditTask, AuditTaskCompletion
        from datetime import datetime, date
        import logging
        
        logger = logging.getLogger(__name__)
        logger.info("Starting daily audit status snapshot")
        
        today = date.today()
        
        try:
            # Get all audit tasks
            audit_tasks = AuditTask.query.all()
            
            # Count how many were already saved today
            already_saved = AuditTaskCompletion.query.filter_by(date=today).count()
            logger.info(f"Found {already_saved} audit task completions already saved for today")
            
            # Create a list to track newly saved completions
            new_completions = []
            
            # For each task, check if it has a completion record for today
            for task in audit_tasks:
                for machine in task.machines:
                    # Check if we already have a completion record for this task/machine today
                    existing_completion = AuditTaskCompletion.query.filter_by(
                        audit_task_id=task.id,
                        machine_id=machine.id,
                        date=today
                    ).first()
                    
                    # If no record exists, create one with completed=False
                    if not existing_completion:
                        completion = AuditTaskCompletion(
                            audit_task_id=task.id,
                            machine_id=machine.id,
                            date=today,
                            completed=False
                        )
                        db.session.add(completion)
                        new_completions.append((task.name, machine.name))
            
            # Save all new completions
            if new_completions:
                db.session.commit()
                logger.info(f"Saved {len(new_completions)} new audit task completion records")
                for task_name, machine_name in new_completions:
                    logger.debug(f"Saved audit status for '{task_name}' on '{machine_name}'")
            else:
                logger.info("No new audit task completions needed to be saved")
                
        except Exception as e:
            logger.error(f"Error saving daily audit status: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "daily":
            send_daily_digest()
            send_audit_reminders()
            save_daily_audit_status(app)
        elif sys.argv[1] == "weekly":
            send_weekly_digest()
        elif sys.argv[1] == "monthly":
            send_monthly_digest()
        elif sys.argv[1] == "immediate":
            send_immediate_notifications()
        elif sys.argv[1] == "audit":
            send_audit_reminders()
        elif sys.argv[1] == "save_audit_status":
            save_daily_audit_status(app)
        else:
            print("Please specify 'immediate', 'daily', 'weekly', 'monthly', 'audit', or 'save_audit_status' as an argument")
    else:
        print("Please specify 'immediate', 'daily', 'weekly', 'monthly', 'audit', or 'save_audit_status' as an argument")
