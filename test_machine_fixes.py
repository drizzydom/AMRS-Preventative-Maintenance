from app import create_app, db
from models import Machine, Part, Site
from datetime import datetime, timedelta

app = create_app()

with app.app_context():
    # Create a dummy site and machine if needed, or query existing
    site = Site.query.first()
    if not site:
        site = Site(name="Test Site")
        db.session.add(site)
        db.session.commit()
    
    machine = Machine(name="Test Machine", site_id=site.id)
    db.session.add(machine)
    db.session.commit()
    
    # Create parts
    p1 = Part(name="Part 1", machine_id=machine.id, maintenance_frequency=30)
    p1.last_maintenance = datetime.utcnow() - timedelta(days=10)
    p1.next_maintenance = datetime.utcnow() + timedelta(days=20)
    
    p2 = Part(name="Part 2", machine_id=machine.id, maintenance_frequency=30)
    p2.last_maintenance = datetime.utcnow() - timedelta(days=5)
    p2.next_maintenance = datetime.utcnow() + timedelta(days=25)
    
    db.session.add(p1)
    db.session.add(p2)
    db.session.commit()
    
    # Reload machine from DB to ensure relationships are loaded
    # Use joinedload to simulate api behavior, although accessing property triggers dynamic calculation
    m = Machine.query.get(machine.id)
    
    print(f"Machine Last Maintenance: {m.last_maintenance}")
    print(f"Machine Next Maintenance: {m.next_maintenance}")
    
    # Expected: Last = p2.last_maintenance (more recent), Next = p1.next_maintenance (sooner)
    # Using approx comparison for datetime due to db storage precision
    assert abs((m.last_maintenance - p2.last_maintenance).total_seconds()) < 1.0
    assert abs((m.next_maintenance - p1.next_maintenance).total_seconds()) < 1.0
    
    print("Dates Correct!")
    
    # Check cycle status
    p_cycle = Part(name="Cycle Part", machine_id=machine.id, maintenance_unit='cycle', maintenance_cycle_frequency=100)
    m.cycle_count = 0
    p_cycle.last_maintenance_cycle = 0
    p_cycle.next_maintenance_cycle = 100
    
    # Should return None now
    status = p_cycle.get_cycle_status()
    print(f"Cycle Status: {status}")
    assert status is None
    
    print("Cycle status disabled!")
    
    # Cleanup
    db.session.delete(p1)
    db.session.delete(p2)
    db.session.delete(p_cycle)
    db.session.delete(machine)
    db.session.commit()
