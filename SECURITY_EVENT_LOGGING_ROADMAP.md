# AMRS Preventative Maintenance: Security Event Logging & Notification Roadmap

## Objective
Implement robust security event logging, notification, and admin visibility for all critical security-related actions in the application.


## Important Requirement
- All security events that occur while a client device is offline must be logged locally and synchronized to the server when the device comes online, ensuring no events are lost.

## Features to Implement

### 1. Security Event Logging
- Central `SecurityEvent` model/table for all security events (timestamp, type, user, IP, details)
- Utility function: `log_security_event(event_type, user, ip, details)`
- Log retention policy (auto-delete logs older than X days, configurable)
- Toggle to enable/disable logging (admin UI)

### 2. Email Notification System
- Automatic email notifications for security events
- Batch notifications: send all events in a 10-minute window in a single email
- Cooldown: never send more than one email per 10 minutes
- Use Flask-Mail and admin email from environment/config

### 3. Event Triggers
- Login from new device/IP (include user, IP, general location)
- Any rate limiting (login, bootstrap, DDoS, etc.)
- All access to bootstrap secrets endpoint (log all attempts)
- Changes to admin-level materials (sites, machines, users, etc.; no sensitive data)
- Failed login attempts
- Password reset requests
- Privilege escalations
- Suspicious activity (e.g., repeated forbidden endpoint access)

### 4. Admin Log Viewer
- `/admin/security-logs` endpoint, admin-only
- Paginated, filterable, with UI similar to `maintenance_records.html`
- Toggle for enabling/disabling logging

### 5. Additional Security & Reliability
- Audit trail for all critical models (who, what, when)
- Configurable logging and notification settings
- Health check endpoint (`/health`)
- Sensitive data redaction in logs/emails
- Log IP blacklisting for repeated abusers

## Implementation Steps
1. Add Flask-Limiter to requirements and set up global/per-endpoint limits
2. Create `SecurityEvent` model and migration
3. Implement `log_security_event()` utility
4. Add event logging calls to all relevant places
5. Implement background email batcher (thread or scheduled job)
6. Add `/admin/security-logs` endpoint and template
7. Add admin UI toggle for logging
8. Add log retention and health check endpoint

## Transfer Instructions
- Share this file with Copilot Chat on any device to resume or continue this work.
- Reference this file for all security event logging, notification, and admin log viewer requirements.
- All code, models, and UI should follow the requirements and steps outlined here.

---

**If you are picking up this project on a new machine, share this file with Copilot Chat and ask for implementation help.**
