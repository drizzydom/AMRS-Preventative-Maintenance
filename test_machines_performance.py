#!/usr/bin/env python3
"""
Quick test to verify machines page query optimization
"""

from app import app, db, Machine
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time

# Track SQL queries
query_count = 0
query_start_time = None

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    global query_count, query_start_time
    query_count += 1
    query_start_time = time.time()
    
@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    global query_start_time
    if query_start_time:
        total = time.time() - query_start_time
        if total > 0.1:  # Log slow queries
            print(f"[SLOW QUERY {total:.3f}s] {statement[:100]}...")

def test_machines_query():
    """Test the optimized machines query"""
    global query_count
    
    with app.app_context():
        print("Testing machines query optimization...")
        
        # Reset counter
        query_count = 0
        start_time = time.time()
        
        # Test the optimized query with eager loading
        machines = Machine.query.options(
            db.joinedload(Machine.site),
            db.joinedload(Machine.parts)
        ).limit(10).all()
        
        end_time = time.time()
        
        print(f"✓ Fetched {len(machines)} machines")
        print(f"✓ Total queries executed: {query_count}")
        print(f"✓ Query time: {end_time - start_time:.3f}s")
        
        # Test accessing related data (should not trigger additional queries)
        query_count_before_access = query_count
        
        for machine in machines:
            _ = machine.site.name  # Should not trigger query
            _ = len(machine.parts)  # Should not trigger query
            
        print(f"✓ Accessing related data triggered {query_count - query_count_before_access} additional queries")
        
        if query_count - query_count_before_access == 0:
            print("🎉 NO N+1 QUERIES! Optimization successful!")
        else:
            print("⚠️  Still has N+1 queries - optimization needed")

if __name__ == "__main__":
    test_machines_query()
