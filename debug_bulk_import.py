#!/usr/bin/env python3
"""
Debug version of the bulk import logic to identify why only some machines are imported
"""

import json

# Simulate the database state
existing_machines = []

def find_or_create_machine_debug(machine_data, site_id):
    """Debug version of find_or_create_machine"""
    
    # Field mapping
    field_mappings = {
        'name': ['name', 'machine', 'machine_name', 'Machine'],
        'model': ['model', 'machine_model', 'Model'], 
        'serial_number': ['serial_number', 'serial', 'Serial Number', 'sn'],
        'machine_number': ['machine_number', 'Machine Number', 'number', 'id']
    }
    
    mapped = {}
    for standard_field, possible_names in field_mappings.items():
        for possible_name in possible_names:
            if possible_name in machine_data and machine_data[possible_name] is not None:
                mapped[standard_field] = machine_data[possible_name]
                break
    
    name = str(mapped.get('name', '')).strip()
    model = str(mapped.get('model', '')).strip()
    serial = str(mapped.get('serial_number', '')).strip()
    
    print(f"Processing machine: {name}, model: {model}, serial: {serial}")
    
    if not name:
        return None, "Missing machine name"
    
    # Default model to machine name if not provided
    if not model:
        model = name
        print(f"  Model defaulted to: {model}")
    
    # Try to find existing machine using multiple criteria
    existing = None
    
    # First try: exact match on name, model, and serial
    if serial:
        for machine in existing_machines:
            if (machine['name'] == name and 
                machine['model'] == model and 
                machine['serial_number'] == serial and
                machine['site_id'] == site_id):
                existing = machine
                print(f"  Found exact match: {machine}")
                break
    
    # Second try: match on name and serial
    if not existing and serial:
        for machine in existing_machines:
            if (machine['name'] == name and 
                machine['serial_number'] == serial and
                machine['site_id'] == site_id):
                existing = machine
                print(f"  Found name+serial match: {machine}")
                break
    
    # If we have a serial number and haven't found a match, this should be a new machine
    # Only check name/model matches if there's no serial number provided
    if not existing and not serial:
        # Third try: match on name and model (only if no serial number)
        if model:
            for machine in existing_machines:
                if (machine['name'] == name and 
                    machine['model'] == model and
                    machine['site_id'] == site_id):
                    existing = machine
                    print(f"  Found name+model match: {machine}")
                    break
        
        # Fourth try: match on name only (if it's unique within site and no serial)
        if not existing:
            name_matches = [m for m in existing_machines if m['name'] == name and m['site_id'] == site_id]
            if len(name_matches) == 1:
                existing = name_matches[0]
                print(f"  Found unique name match: {existing}")
    
    if existing:
        print(f"  Result: Found existing machine")
        return existing, "Found existing machine"
    else:
        new_machine = {
            'name': name,
            'model': model,
            'serial_number': serial,
            'machine_number': str(mapped.get('machine_number', '')).strip(),
            'site_id': site_id,
            'id': len(existing_machines) + 1
        }
        existing_machines.append(new_machine)
        print(f"  Result: Created new machine - {new_machine}")
        return new_machine, "Created new machine"

def test_bulk_import_logic():
    """Test the bulk import logic with the JSON data"""
    
    with open("/Users/dominicmoriello/Documents/Excel Exporter/output_KL_Microwave PM.json", 'r') as f:
        data = json.load(f)
    
    site_id = 1  # Assume site ID 1
    
    print("=== Testing Bulk Import Logic ===")
    print(f"Site ID: {site_id}")
    print(f"Starting with {len(existing_machines)} existing machines")
    
    added = 0
    updated = 0
    merged = 0
    errors = []
    
    for i, row in enumerate(data):
        print(f"\n--- Processing row {i+1} ---")
        
        # Skip rows with missing essential data
        if not row or all(v is None or v == '' for v in row.values()):
            print("  Skipping: All null values")
            continue
        
        try:
            machine, status = find_or_create_machine_debug(row, site_id)
            if not machine:
                errors.append(f"Could not process machine: {status}")
                print(f"  Error: {status}")
                continue
            
            # Determine action taken
            if "Created" in status:
                added += 1
                print(f"  Action: ADDED (new machine)")
            elif "Updated" in status:
                updated += 1
                print(f"  Action: UPDATED (existing machine)")
            elif "Found" in status:
                merged += 1
                print(f"  Action: MERGED/SKIPPED (existing machine)")
            
        except Exception as e:
            errors.append(f"Error processing machine row: {str(e)}")
            print(f"  Exception: {e}")
    
    print(f"\n=== FINAL RESULTS ===")
    print(f"Added: {added}")
    print(f"Updated: {updated}")
    print(f"Merged/Skipped: {merged}")
    print(f"Errors: {len(errors)}")
    
    if errors:
        print("Error details:")
        for error in errors:
            print(f"  - {error}")
    
    print(f"\nFinal machine count: {len(existing_machines)}")
    for machine in existing_machines:
        print(f"  {machine['name']} (Serial: {machine['serial_number']})")

if __name__ == "__main__":
    test_bulk_import_logic()
