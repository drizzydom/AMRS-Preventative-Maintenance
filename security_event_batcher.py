import threading
import time
from flask import current_app
from flask_mail import Message
from models import db, SecurityEvent, User
from datetime import datetime, timedelta
import os

EMAIL_BATCH_INTERVAL = 600  # 10 minutes in seconds

class SecurityEventBatcher:
    def __init__(self, mail, admin_email):
        self.mail = mail
        self.admin_email = admin_email
        self.last_sent = datetime.utcnow() - timedelta(seconds=EMAIL_BATCH_INTERVAL)
        self.lock = threading.Lock()
        self.running = False

    def start(self):
        if not self.running:
            self.running = True
            t = threading.Thread(target=self.run, daemon=True)
            t.start()

    def run(self):
        while self.running:
            try:
                now = datetime.utcnow()
                if (now - self.last_sent).total_seconds() >= EMAIL_BATCH_INTERVAL:
                    with current_app.app_context():
                        events = SecurityEvent.query.filter(SecurityEvent.timestamp > self.last_sent).order_by(SecurityEvent.timestamp).all()
                        if events:
                            self.send_email(events)
                            self.last_sent = now
                time.sleep(30)
            except Exception as e:
                print(f"[SECURITY EMAIL BATCHER] Error: {e}")
                time.sleep(60)

    def send_email(self, events):
        subject = f"[AMRS] Security Events ({len(events)})"
        body = "Security events detected:\n\n"
        for event in events:
            body += f"[{event.timestamp}] {event.event_type} | User: {event.username or event.user_id or 'N/A'} | IP: {event.ip_address or 'N/A'} | Details: {event.details or ''}\n"
        msg = Message(subject, recipients=[self.admin_email], body=body)
        self.mail.send(msg)
        print(f"[SECURITY EMAIL BATCHER] Sent security event email with {len(events)} events.")

# Usage (in app.py after mail is initialized):
# from security_event_batcher import SecurityEventBatcher
# batcher = SecurityEventBatcher(mail, os.environ.get('ADMIN_EMAIL', 'admin@example.com'))
# batcher.start()
