import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import or_

# Add the app directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, mail
from models import User, Site, Machine, Part
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

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "daily":
        send_daily_digest()
    elif len(sys.argv) > 1 and sys.argv[1] == "weekly":
        send_weekly_digest()
    else:
        print("Please specify 'daily' or 'weekly' as an argument")
