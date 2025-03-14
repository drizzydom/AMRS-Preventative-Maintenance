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

@app.route('/maintenance', methods=['GET'])
def get_maintenance_records():
    records = MaintenanceRecord.query.all()
    return jsonify([record.to_dict() for record in records])

@app.route('/maintenance', methods=['POST'])
def add_maintenance_record():
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
    record = MaintenanceRecord.query.get(id)
    if record is None:
        return jsonify({'error': 'Record not found'}), 404
    db.session.delete(record)
    db.session.commit()
    return '', 204

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5001, debug=True)
