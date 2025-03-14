from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///maintenance.db'
db = SQLAlchemy(app)
CORS(app)

class MaintenanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    machine = db.Column(db.String(100), nullable=False)
    part = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(10), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'machine': self.machine,
            'part': self.part,
            'description': self.description,
            'date': self.date
        }

class Site(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name
        }

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role_id': self.role_id
        }

class Machine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    site_id = db.Column(db.Integer, db.ForeignKey('site.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'site_id': self.site_id
        }

class Part(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    machine_id = db.Column(db.Integer, db.ForeignKey('machine.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'machine_id': self.machine_id
        }

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name
        }

class Permission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'role_id': self.role_id
        }

def check_permission(user_id, permission_name):
    user = User.query.get(user_id)
    if user is None:
        return False
    role = Role.query.get(user.role_id)
    if role is None:
        return False
    permission = Permission.query.filter_by(role_id=role.id, name=permission_name).first()
    return permission is not None

@app.route('/maintenance', methods=['GET'])
def get_maintenance_records():
    records = MaintenanceRecord.query.all()
    return jsonify([record.to_dict() for record in records])

@app.route('/maintenance', methods=['POST'])
def add_maintenance_record():
    user_id = request.headers.get('User-ID')
    if not check_permission(user_id, 'create_maintenance_record'):
        return jsonify({'error': 'Permission denied'}), 403
    data = request.get_json()
    new_record = MaintenanceRecord(
        machine=data['machine'],
        part=data['part'],
        description=data['description'],
        date=data['date']
    )
    db.session.add(new_record)
    db.session.commit()
    return jsonify(new_record.to_dict()), 201

@app.route('/maintenance/<int:id>', methods=['PUT'])
def update_maintenance_record(id):
    user_id = request.headers.get('User-ID')
    if not check_permission(user_id, 'edit_maintenance_record'):
        return jsonify({'error': 'Permission denied'}), 403
    data = request.get_json()
    record = MaintenanceRecord.query.get(id)
    if record is None:
        return jsonify({'error': 'Record not found'}), 404
    record.machine = data['machine']
    record.part = data['part']
    record.description = data['description']
    record.date = data['date']
    db.session.commit()
    return jsonify(record.to_dict())

@app.route('/maintenance/<int:id>', methods=['DELETE'])
def delete_maintenance_record(id):
    user_id = request.headers.get('User-ID')
    if not check_permission(user_id, 'delete_maintenance_record'):
        return jsonify({'error': 'Permission denied'}), 403
    record = MaintenanceRecord.query.get(id)
    if record is None:
        return jsonify({'error': 'Record not found'}), 404
    db.session.delete(record)
    db.session.commit()
    return '', 204

@app.route('/sites', methods=['GET'])
def get_sites():
    sites = Site.query.all()
    return jsonify([site.to_dict() for site in sites])

@app.route('/sites', methods=['POST'])
def add_site():
    user_id = request.headers.get('User-ID')
    if not check_permission(user_id, 'create_site'):
        return jsonify({'error': 'Permission denied'}), 403
    data = request.get_json()
    new_site = Site(name=data['name'])
    db.session.add(new_site)
    db.session.commit()
    return jsonify(new_site.to_dict()), 201

@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@app.route('/users', methods=['POST'])
def add_user():
    user_id = request.headers.get('User-ID')
    if not check_permission(user_id, 'create_user'):
        return jsonify({'error': 'Permission denied'}), 403
    data = request.get_json()
    new_user = User(username=data['username'], password=data['password'], role_id=data['role_id'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify(new_user.to_dict()), 201

@app.route('/machines', methods=['GET'])
def get_machines():
    machines = Machine.query.all()
    return jsonify([machine.to_dict() for machine in machines])

@app.route('/machines', methods=['POST'])
def add_machine():
    user_id = request.headers.get('User-ID')
    if not check_permission(user_id, 'create_machine'):
        return jsonify({'error': 'Permission denied'}), 403
    data = request.get_json()
    new_machine = Machine(name=data['name'], site_id=data['site_id'])
    db.session.add(new_machine)
    db.session.commit()
    return jsonify(new_machine.to_dict()), 201

@app.route('/parts', methods=['GET'])
def get_parts():
    parts = Part.query.all()
    return jsonify([part.to_dict() for part in parts])

@app.route('/parts', methods=['POST'])
def add_part():
    user_id = request.headers.get('User-ID')
    if not check_permission(user_id, 'create_part'):
        return jsonify({'error': 'Permission denied'}), 403
    data = request.get_json()
    new_part = Part(name=data['name'], machine_id=data['machine_id'])
    db.session.add(new_part)
    db.session.commit()
    return jsonify(new_part.to_dict()), 201

@app.route('/roles', methods=['GET'])
def get_roles():
    roles = Role.query.all()
    return jsonify([role.to_dict() for role in roles])

@app.route('/roles', methods=['POST'])
def add_role():
    user_id = request.headers.get('User-ID')
    if not check_permission(user_id, 'create_role'):
        return jsonify({'error': 'Permission denied'}), 403
    data = request.get_json()
    new_role = Role(name=data['name'])
    db.session.add(new_role)
    db.session.commit()
    return jsonify(new_role.to_dict()), 201

@app.route('/permissions', methods=['GET'])
def get_permissions():
    permissions = Permission.query.all()
    return jsonify([permission.to_dict() for permission in permissions])

@app.route('/permissions', methods=['POST'])
def add_permission():
    user_id = request.headers.get('User-ID')
    if not check_permission(user_id, 'create_permission'):
        return jsonify({'error': 'Permission denied'}), 403
    data = request.get_json()
    new_permission = Permission(name=data['name'], role_id=data['role_id'])
    db.session.add(new_permission)
    db.session.commit()
    return jsonify(new_permission.to_dict()), 201

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5001, debug=True)
