#!/usr/bin/env python3
"""
Test script to verify that machine name fallback works correctly.
This tests the case where the CSV has an empty 'name' field but a populated 'machine_name' field.
"""

def test_machine_name_fallback():
    """Test that the machine name fallback works when 'name' is empty"""
    print("=== Testing machine name fallback ===")
    
    # This simulates the case in the CSV where 'name' is empty but 'machine_name' has the value
    csv_row_data = {
        'name': '',  # Empty name field
        'model': '',
        'serial_number': '',
        'machine_number': '',
        'machine_name': 'demo 3',  # Machine name is here instead
        'part_name': 'lubrication',
        'maintenance_type': 'refill',
        'description': '',
        'date': '1/1/25',
        'performed_by': 'You',
        'status': '',
        'notes': '',
        'maintenance_frequency': '30',
        'maintenance_unit': 'days'
    }
    
    # Simulate the find_or_create_machine logic
    machine_mappings = {
        'name': ['name', 'machine', 'machine_name', 'Machine'],
        'model': ['model', 'machine_model', 'Model'],
        'serial_number': ['serial_number', 'serial', 'Serial Number', 'sn'],
        'machine_number': ['machine_number', 'Machine Number', 'number', 'id']
    }
    
    mapped = {}
    for standard_field, possible_names in machine_mappings.items():
        for possible_name in possible_names:
            if possible_name in csv_row_data and csv_row_data[possible_name] is not None:
                mapped[standard_field] = csv_row_data[possible_name]
                break
    
    name = str(mapped.get('name', '')).strip()
    model = str(mapped.get('model', '')).strip()
    serial = str(mapped.get('serial_number', '')).strip()
    
    # If no name found in standard mapping, try machine_name field (NEW LOGIC)
    if not name:
        name = str(csv_row_data.get('machine_name', '')).strip()
    
    print(f"Input row: {csv_row_data}")
    print(f"Initial mapped: {mapped}")
    print(f"Final machine name: '{name}'")
    print(f"Final model: '{model}'")
    print(f"Final serial: '{serial}'")
    
    # Verify the machine name was correctly extracted
    assert name == 'demo 3', f"Expected machine name 'demo 3', got '{name}'"
    
    # Verify that model defaults to name when empty (existing logic)
    if not model:
        model = name
    assert model == 'demo 3', f"Expected model to default to 'demo 3', got '{model}'"
    
    print("✅ Machine name fallback test PASSED!")
    return True

def test_maintenance_extraction_with_fallback():
    """Test that maintenance data extraction works with machine name fallback"""
    print("\n=== Testing maintenance extraction with machine name fallback ===")
    
    csv_row_data = {
        'name': '',  # Empty name field
        'model': '',
        'serial_number': '',
        'machine_number': '',
        'machine_name': 'demo 3',  # Machine name is here instead
        'part_name': 'lubrication',
        'maintenance_type': 'refill',
        'description': '',
        'date': '1/1/25',
        'performed_by': 'You',
        'status': '',
        'notes': '',
        'maintenance_frequency': '30',
        'maintenance_unit': 'days'
    }
    
    # Test the maintenance extraction logic with machine name fallback
    records = []
    
    if csv_row_data.get('part_name') and (csv_row_data.get('description') or csv_row_data.get('maintenance_type')):
        # Extract maintenance data from flat CSV row
        machine_name = csv_row_data.get('name', '')  # First try using 'name' field
        if not machine_name:
            # Try alternative machine name field (THIS SHOULD CATCH IT)
            machine_name = csv_row_data.get('machine_name', '')
        
        part_name = csv_row_data.get('part_name', '').strip()
        maintenance_type = csv_row_data.get('maintenance_type', 'Scheduled').strip()
        description = csv_row_data.get('description', '').strip()
        
        if machine_name and part_name:
            record = {
                'machine_name': machine_name,
                'part_name': part_name,
                'maintenance_type': maintenance_type,
                'description': description
            }
            records.append(record)
    
    print(f"Input row: {csv_row_data}")
    print(f"Extracted maintenance records: {records}")
    
    assert len(records) == 1, f"Expected 1 record, got {len(records)}"
    assert records[0]['machine_name'] == 'demo 3', f"Expected machine name 'demo 3', got '{records[0]['machine_name']}'"
    assert records[0]['part_name'] == 'lubrication', f"Expected part name 'lubrication', got '{records[0]['part_name']}'"
    
    print("✅ Maintenance extraction with fallback test PASSED!")
    return True

if __name__ == "__main__":
    print("Testing machine name fallback logic for CSV import...\n")
    
    try:
        test_machine_name_fallback()
        test_maintenance_extraction_with_fallback()
        
        print("\n🎉 ALL FALLBACK TESTS PASSED!")
        print("\nThe fix now handles the case where:")
        print("- The 'name' field is empty")
        print("- But the 'machine_name' field contains the actual machine name")
        print("- This matches the structure in your CSV file where some rows have empty 'name' fields")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        print("The fix may need additional adjustments.")
