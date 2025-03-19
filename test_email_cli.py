#!/usr/bin/env python3
"""
Simple CLI tool to test email sending without running the full Flask app.
This helps isolate email configuration issues.
"""

import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Get the directory of this file
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# Look for .env file in the current directory
dotenv_path = os.path.join(BASE_DIR, '.env')
# Load environment variables from .env file
load_dotenv(dotenv_path)

def send_test_email(recipient):
    print(f"Testing email configuration...")
    print(f"  MAIL_SERVER: {os.environ.get('MAIL_SERVER', 'Not set')}")
    print(f"  MAIL_PORT: {os.environ.get('MAIL_PORT', 'Not set')}")
    print(f"  MAIL_USE_TLS: {os.environ.get('MAIL_USE_TLS', 'Not set')}")
    print(f"  MAIL_USERNAME: {os.environ.get('MAIL_USERNAME', 'Not set')}")
    print(f"  MAIL_DEFAULT_SENDER: {os.environ.get('MAIL_DEFAULT_SENDER', 'Not set')}")
    
    # Create message
    msg = MIMEMultipart()
    msg['Subject'] = 'Test Email from Maintenance System'
    msg['From'] = os.environ.get('MAIL_DEFAULT_SENDER', 'maintenance@example.com')
    msg['To'] = recipient
    
    # Create HTML body
    html = """
    <html>
      <body>
        <h1>Test Email</h1>
        <p>This is a test email from the Maintenance System.</p>
        <p>If you're seeing this, your email configuration is working!</p>
      </body>
    </html>
    """
    msg.attach(MIMEText(html, 'html'))
    
    # Connect to server and send
    try:
        server = smtplib.SMTP(
            os.environ.get('MAIL_SERVER', 'smtp.example.com'),
            int(os.environ.get('MAIL_PORT', 587))
        )
        
        if os.environ.get('MAIL_USE_TLS', 'True').lower() in ('true', 'yes', '1'):
            server.starttls()
        
        username = os.environ.get('MAIL_USERNAME')
        password = os.environ.get('MAIL_PASSWORD')
        
        if username and password:
            server.login(username, password)
        
        server.send_message(msg)
        server.quit()
        print(f"Test email sent successfully to {recipient}!")
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_email_cli.py recipient@example.com")
        sys.exit(1)
    
    recipient = sys.argv[1]
    success = send_test_email(recipient)
    if not success:
        sys.exit(1)
