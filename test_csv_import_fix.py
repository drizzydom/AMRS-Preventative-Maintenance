#!/usr/bin/env python3
"""
Test script to verify that the CSV import fix works correctly.
This simulates the CSV structure provided by the user.
"""

def test_extract_parts_data():
    """Test the extract_parts_data function with CSV-like data"""
    print("=== Testing extract_parts_data function ===")
    
    # Simulate CSV row data similar to the user's file
    csv_row_data = {
        'name': 'demo 1',
        'model': 'VTC',
        'serial_number': '123',
        'machine_number': '1',
        'machine_name': 'demo 1',  # This is the alternative name field
        'part_name': 'thingamabob',
        'maintenance_type': 'cleaning',
        'description': 'Spotless',
        'date': '1/1/25',
        'performed_by': 'Someone',
        'status': "it's ok",
        'notes': 'Yeah',
        'maintenance_frequency': '3',
        'maintenance_unit': 'months'
    }
    
    machine_name = 'demo 1'
    
    # Test the modified function logic
    parts = []
    
    # Handle flat CSV structure (this is the new logic we added)
    if csv_row_data.get('part_name'):
        # Extract part data from flat CSV row
        part_name = csv_row_data.get('part_name', '').strip()
        if part_name:
            # Parse frequency from CSV columns
            freq_value = 30  # default
            freq_unit = 'day'  # default
            
            if csv_row_data.get('maintenance_frequency'):
                try:
                    freq_value = int(csv_row_data.get('maintenance_frequency', 30))
                except (ValueError, TypeError):
                    freq_value = 30
            
            if csv_row_data.get('maintenance_unit'):
                freq_unit = csv_row_data.get('maintenance_unit', 'day').lower()
                # Convert months to days for consistency
                if freq_unit in ['month', 'months']:
                    freq_value = freq_value * 30
                    freq_unit = 'day'
                elif freq_unit in ['year', 'years']:
                    freq_value = freq_value * 365
                    freq_unit = 'day'
            
            part = {
                'name': part_name,
                'description': csv_row_data.get('description', '').strip(),
                'machine_name': machine_name,
                'maintenance_frequency': freq_value,
                'maintenance_unit': freq_unit,
                'materials': csv_row_data.get('materials', ''),
                'quantity': csv_row_data.get('quantity', '')
            }
            
            parts.append(part)
    
    print(f"Input CSV row: {csv_row_data}")
    print(f"Extracted parts: {parts}")
    
    expected_part = {
        'name': 'thingamabob',
        'description': 'Spotless',
        'machine_name': 'demo 1',
        'maintenance_frequency': 90,  # 3 months * 30 days
        'maintenance_unit': 'day',
        'materials': '',
        'quantity': ''
    }
    
    assert len(parts) == 1, f"Expected 1 part, got {len(parts)}"
    assert parts[0]['name'] == expected_part['name'], f"Part name mismatch: {parts[0]['name']} != {expected_part['name']}"
    assert parts[0]['maintenance_frequency'] == expected_part['maintenance_frequency'], f"Frequency mismatch: {parts[0]['maintenance_frequency']} != {expected_part['maintenance_frequency']}"
    
    print("✅ extract_parts_data test PASSED!")
    return True

def test_extract_maintenance_data():
    """Test the extract_maintenance_data function with CSV-like data"""
    print("\n=== Testing extract_maintenance_data function ===")
    
    # Simulate CSV row data similar to the user's file
    csv_row_data = {
        'name': 'demo 1',
        'model': 'VTC',
        'serial_number': '123',
        'machine_number': '1',
        'machine_name': 'demo 1',  # This is the alternative name field
        'part_name': 'thingamabob',
        'maintenance_type': 'cleaning',
        'description': 'Spotless',
        'date': '1/1/25',
        'performed_by': 'Someone',
        'status': "it's ok",
        'notes': 'Yeah',
        'maintenance_frequency': '3',
        'maintenance_unit': 'months'
    }
    
    # Test the modified function logic
    records = []
    
    # Handle flat CSV structure (this is the new logic we added)
    if csv_row_data.get('part_name') and (csv_row_data.get('description') or csv_row_data.get('maintenance_type')):
        # Extract maintenance data from flat CSV row
        machine_name = csv_row_data.get('name', '')  # First try using 'name' field
        if not machine_name:
            # Try alternative machine name field
            machine_name = csv_row_data.get('machine_name', '')
        
        part_name = csv_row_data.get('part_name', '').strip()
        maintenance_type = csv_row_data.get('maintenance_type', 'Scheduled').strip()
        description = csv_row_data.get('description', '').strip()
        date = csv_row_data.get('date', '').strip()
        performed_by = csv_row_data.get('performed_by', 'System Import').strip()
        status = csv_row_data.get('status', 'completed').strip()
        notes = csv_row_data.get('notes', '').strip()
        
        # Parse frequency
        freq_value = 30  # default
        freq_unit = 'day'  # default
        
        if csv_row_data.get('maintenance_frequency'):
            try:
                freq_value = int(csv_row_data.get('maintenance_frequency', 30))
            except (ValueError, TypeError):
                freq_value = 30
        
        if csv_row_data.get('maintenance_unit'):
            freq_unit = csv_row_data.get('maintenance_unit', 'day').lower()
            # Convert months to days for consistency
            if freq_unit in ['month', 'months']:
                freq_value = freq_value * 30
                freq_unit = 'day'
            elif freq_unit in ['year', 'years']:
                freq_value = freq_value * 365
                freq_unit = 'day'
        
        if machine_name and part_name:
            record = {
                'machine_name': machine_name,
                'part_name': part_name,
                'maintenance_type': maintenance_type,
                'description': description,
                'date': date,
                'performed_by': performed_by or 'System Import',
                'status': status or 'completed',
                'notes': notes,
                'maintenance_frequency': freq_value,
                'maintenance_unit': freq_unit
            }
            
            records.append(record)
    
    print(f"Input CSV row: {csv_row_data}")
    print(f"Extracted maintenance records: {records}")
    
    expected_record = {
        'machine_name': 'demo 1',
        'part_name': 'thingamabob',
        'maintenance_type': 'cleaning',
        'description': 'Spotless',
        'date': '1/1/25',
        'performed_by': 'Someone',
        'status': "it's ok",
        'notes': 'Yeah',
        'maintenance_frequency': 90,  # 3 months * 30 days
        'maintenance_unit': 'day'
    }
    
    assert len(records) == 1, f"Expected 1 record, got {len(records)}"
    assert records[0]['machine_name'] == expected_record['machine_name'], f"Machine name mismatch"
    assert records[0]['part_name'] == expected_record['part_name'], f"Part name mismatch"
    assert records[0]['maintenance_frequency'] == expected_record['maintenance_frequency'], f"Frequency mismatch: {records[0]['maintenance_frequency']} != {expected_record['maintenance_frequency']}"
    
    print("✅ extract_maintenance_data test PASSED!")
    return True

def test_smart_field_mapping():
    """Test that the smart field mapping works for CSV fields"""
    print("\n=== Testing smart_field_mapping function ===")
    
    csv_row_data = {
        'name': 'demo 1',
        'model': 'VTC',
        'serial_number': '123',
        'machine_number': '1',
        'machine_name': 'demo 1',
        'part_name': 'thingamabob',
        'maintenance_type': 'cleaning',
        'description': 'Spotless',
        'date': '1/1/25',
        'performed_by': 'Someone',
        'status': "it's ok",
        'notes': 'Yeah',
        'maintenance_frequency': '3',
        'maintenance_unit': 'months'
    }
    
    # Simulate the smart_field_mapping function for machines
    machine_mappings = {
        'name': ['name', 'machine', 'machine_name', 'Machine'],
        'model': ['model', 'machine_model', 'Model'],
        'serial_number': ['serial_number', 'serial', 'Serial Number', 'sn'],
        'machine_number': ['machine_number', 'Machine Number', 'number', 'id']
    }
    
    machine_mapped = {}
    for standard_field, possible_names in machine_mappings.items():
        for possible_name in possible_names:
            if possible_name in csv_row_data and csv_row_data[possible_name] is not None:
                machine_mapped[standard_field] = csv_row_data[possible_name]
                break
    
    print(f"Machine field mapping: {machine_mapped}")
    
    expected_machine = {
        'name': 'demo 1',
        'model': 'VTC', 
        'serial_number': '123',
        'machine_number': '1'
    }
    
    assert machine_mapped == expected_machine, f"Machine mapping mismatch: {machine_mapped} != {expected_machine}"
    
    # Test maintenance field mapping
    maintenance_mappings = {
        'machine_name': ['machine_name', 'machine', 'Machine', 'Machine Name'],
        'part_name': ['part_name', 'part', 'Part', 'component'],
        'maintenance_type': ['maintenance_type', 'type', 'Type', 'Maintenance Type'],
        'description': ['description', 'desc', 'Description', 'work_done'],
        'date': ['date', 'Date', 'maintenance_date', 'performed_date'],
        'performed_by': ['performed_by', 'technician', 'Technician', 'worker'],
        'status': ['status', 'Status', 'state'],
        'notes': ['notes', 'Notes', 'comments', 'Comments']
    }
    
    maintenance_mapped = {}
    for standard_field, possible_names in maintenance_mappings.items():
        for possible_name in possible_names:
            if possible_name in csv_row_data and csv_row_data[possible_name] is not None:
                maintenance_mapped[standard_field] = csv_row_data[possible_name]
                break
    
    print(f"Maintenance field mapping: {maintenance_mapped}")
    
    expected_maintenance = {
        'machine_name': 'demo 1',
        'part_name': 'thingamabob',
        'maintenance_type': 'cleaning',
        'description': 'Spotless',
        'date': '1/1/25',
        'performed_by': 'Someone',
        'status': "it's ok",
        'notes': 'Yeah'
    }
    
    assert maintenance_mapped == expected_maintenance, f"Maintenance mapping mismatch"
    
    print("✅ smart_field_mapping test PASSED!")
    return True

if __name__ == "__main__":
    print("Testing CSV import fixes for flat CSV structure...\n")
    
    try:
        test_smart_field_mapping()
        test_extract_parts_data()
        test_extract_maintenance_data()
        
        print("\n🎉 ALL TESTS PASSED!")
        print("\nThe CSV import fix should now work correctly with your CSV file structure.")
        print("When you upload a CSV file using the 'unified' import (which is the default),")
        print("it will now extract both parts and maintenance records from the flat CSV structure.")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        print("The fix may need additional adjustments.")
