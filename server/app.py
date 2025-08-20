#!/usr/bin/env python3
"""
AMRS Maintenance Tracker - Main Flask Application
"""
import os
import sqlite3
from datetime import datetime, timedelta
from functools import wraps
from flask import (
    Flask, request, jsonify, render_template, redirect, 
    url_for, session, g, abort
)
from werkzeug.security import check_password_hash, generate_password_hash

# Initialize Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_for_debugging')
app.config['DEBUG'] = os.environ.get('DEBUG', 'False').lower() == 'true'

# Database configuration
DATABASE = '/app/data/app.db'

def get_db():
    """Get database connection"""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Close database connection at end of request"""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def login_required(f):
    """Decorator to require login for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
@login_required
def index():
    """Dashboard page"""
    db = get_db()
    cursor = db.cursor()
    
    # Get dashboard stats
    cursor.execute("SELECT COUNT(*) FROM part")
    total_parts = cursor.fetchone()[0]
    
    # Calculate overdue maintenance
    now = datetime.now()
    overdue_count = 0
    due_soon_count = 0
    
    cursor.execute("""
        SELECT id, maintenance_interval, last_maintenance 
        FROM part
    """)
    for part in cursor.fetchall():
        if part['last_maintenance']:
            last_maint = datetime.strptime(part['last_maintenance'], '%Y-%m-%d %H:%M:%S')
            next_due = last_maint + timedelta(days=part['maintenance_interval'])
            
            if next_due < now:
                overdue_count += 1
            elif (next_due - now).days <= 7:
                due_soon_count += 1
        else:
            # If no maintenance has been done, consider it overdue
            overdue_count += 1
    
    # Get recent maintenance records
    cursor.execute("""
        SELECT 
            mr.id, 
            mr.timestamp, 
            p.name as part_name,
            m.name as machine_name,
            s.name as site_name,
            u.username as technician
        FROM maintenance_record mr
        JOIN part p ON mr.part_id = p.id
        JOIN machine m ON p.machine_id = m.id
        JOIN site s ON m.site_id = s.id
        LEFT JOIN user u ON mr.user_id = u.id
        ORDER BY mr.timestamp DESC
        LIMIT 10
    """)
    recent_maintenance = []
    for record in cursor.fetchall():
        recent_maintenance.append({
            'id': record['id'],
            'date': record['timestamp'],
            'part_name': record['part_name'],
            'machine_name': record['machine_name'],
            'site_name': record['site_name'],
            'technician': record['technician'] or 'Unknown'
        })
    
    dashboard = {
        'total_parts': total_parts,
        'overdue_count': overdue_count,
        'due_soon_count': due_soon_count
    }
    
    return render_template('index.html', 
                           dashboard=dashboard,
                           recent_maintenance=recent_maintenance)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = 'remember' in request.form
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM user WHERE username = ?', (username,))
        user = cursor.fetchone()
        
        if user is None:
            error = 'Invalid username'
        elif not check_password_hash(user['password_hash'], password):
            error = 'Invalid password'
        else:
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            
            # Update last login time
            cursor.execute(
                'UPDATE user SET last_login = ? WHERE id = ?',
                (datetime.now(), user['id'])
            )
            db.commit()
            
            if remember:
                session.permanent = True
            
            return redirect(url_for('index'))
    
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    """Log out"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/maintenance')
@login_required
def maintenance():
    """Maintenance page"""
    db = get_db()
    cursor = db.cursor()

    # Get all sites for filter
    cursor.execute('SELECT id, name FROM site ORDER BY name')
    sites = [dict(row) for row in cursor.fetchall()]

    # Get dropdown prepopulation values from query params
    site_id = request.args.get('site_id', '')
    machine_id = request.args.get('machine_id', '')
    part_id = request.args.get('part_id', '')

    # You may want to fetch machines/parts for initial population if needed
    # For now, just pass the IDs for JS filtering
    return render_template(
        'maintenance.html',
        sites=sites,
        site_id=site_id,
        machine_id=machine_id,
        part_id=part_id
    )

# API routes
@app.route('/api/health')
def health():
    """API health check endpoint"""
    try:
        # Check database connection
        db = get_db()
        db.execute('SELECT 1')
        
        return jsonify({
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/parts')
def get_parts():
    """API endpoint to get parts"""
    try:
        site_id = request.args.get('site_id')
        machine_id = request.args.get('machine_id')
        
        db = get_db()
        cursor = db.cursor()
        
        query = """
            SELECT 
                p.id, p.name, p.maintenance_interval, p.last_maintenance,
                m.name as machine_name, m.id as machine_id,
                s.name as site_name, s.id as site_id
            FROM part p
            JOIN machine m ON p.machine_id = m.id
            JOIN site s ON m.site_id = s.id
            WHERE 1=1
        """
        params = []
        
        if site_id and site_id != '-1':
            query += " AND s.id = ?"
            params.append(site_id)
            
        if machine_id and machine_id != '-1':
            query += " AND m.id = ?"
            params.append(machine_id)
            
        query += " ORDER BY p.name"
        
        cursor.execute(query, params)
        parts = []
        for row in cursor.fetchall():
            # Calculate status
            status = "ok"
            next_due = None
            
            if row['last_maintenance']:
                last_maint = datetime.strptime(row['last_maintenance'], '%Y-%m-%d %H:%M:%S')
                next_due_date = last_maint + timedelta(days=row['maintenance_interval'])
                next_due = next_due_date.strftime('%Y-%m-%d')
                
                days_until_due = (next_due_date - datetime.now()).days
                
                if days_until_due < 0:
                    status = "overdue"
                elif days_until_due <= 7:
                    status = "due_soon"
            else:
                status = "overdue"
                next_due = "Overdue"
            
            parts.append({
                'id': row['id'],
                'name': row['name'],
                'machine_id': row['machine_id'],
                'machine_name': row['machine_name'],
                'site_id': row['site_id'],
                'site_name': row['site_name'],
                'maintenance_interval': row['maintenance_interval'],
                'last_maintenance': row['last_maintenance'],
                'next_due': next_due,
                'status': status
            })
        
        return jsonify({"parts": parts})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/maintenance/record', methods=['POST'])
@login_required
def record_maintenance():
    """API endpoint to record maintenance"""
    try:
        data = request.json
        part_id = data.get('part_id')
        notes = data.get('notes', '')
        
        if not part_id:
            return jsonify({"error": "part_id is required"}), 400
            
        db = get_db()
        cursor = db.cursor()
        
        # Record maintenance
        cursor.execute("""
            INSERT INTO maintenance_record (part_id, user_id, timestamp, notes)
            VALUES (?, ?, ?, ?)
        """, (part_id, session.get('user_id'), datetime.now(), notes))
        
        # Update last maintenance date
        cursor.execute("""
            UPDATE part SET last_maintenance = ? WHERE id = ?
        """, (datetime.now(), part_id))
        
        db.commit()
        
        return jsonify({"status": "success", "message": "Maintenance recorded"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sites')
@login_required
def get_sites():
    """API endpoint to get sites"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('SELECT id, name, location FROM site ORDER BY name')
        sites = [dict(row) for row in cursor.fetchall()]
        
        return jsonify({"sites": sites})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/machines')
@login_required
def get_machines():
    """API endpoint to get machines"""
    try:
        site_id = request.args.get('site_id')
        
        db = get_db()
        cursor = db.cursor()
        
        if site_id and site_id != '-1':
            cursor.execute(
                'SELECT id, name, model FROM machine WHERE site_id = ? ORDER BY name',
                (site_id,)
            )
        else:
            cursor.execute('SELECT id, name, model FROM machine ORDER BY name')
            
        machines = [dict(row) for row in cursor.fetchall()]
        
        return jsonify({"machines": machines})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# SSL Info page
@app.route('/ssl-info')
def ssl_info():
    """SSL certificate info page"""
    return render_template('ssl_info.html')

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    """404 error handler"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """500 error handler"""
    return render_template('500.html'), 500

if __name__ == '__main__':
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 9000))
    app.run(host=host, port=port, debug=app.debug)
