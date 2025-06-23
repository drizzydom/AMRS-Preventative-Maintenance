#!/usr/bin/env python3
"""
Test the field mapping for the JSON data
"""

import json

def smart_field_mapping(row, entity_type):
    """Copy of the smart_field_mapping function from the app"""
    mapped = {}
    
    # Define field mappings for different naming conventions
    field_mappings = {
        'machines': {
            'name': ['name', 'machine', 'machine_name', 'Machine'],
            'model': ['model', 'machine_model', 'Model'],
            'serial_number': ['serial_number', 'serial', 'Serial Number', 'sn'],
            'machine_number': ['machine_number', 'Machine Number', 'number', 'id']
        }
    }
    
    # Map fields based on entity type
    if entity_type in field_mappings:
        for standard_field, possible_names in field_mappings[entity_type].items():
            for possible_name in possible_names:
                if possible_name in row and row[possible_name] is not None:
                    mapped[standard_field] = row[possible_name]
                    break
    
    return mapped

def test_field_mapping():
    """Test the field mapping with the actual JSON data"""
    
    with open("/Users/dominicmoriello/Documents/Excel Exporter/output_KL_Microwave PM.json", 'r') as f:
        data = json.load(f)
    
    print("Testing field mapping for first 5 valid records:")
    
    valid_count = 0
    for i, record in enumerate(data):
        # Skip null records
        if all(v is None or str(v).strip() == '' for v in record.values()):
            continue
            
        if valid_count >= 5:
            break
            
        valid_count += 1
        
        print(f"\n--- Record {i+1} ---")
        print("Raw data:")
        print(f"  Machine: {record.get('Machine')}")
        print(f"  Serial Number: {record.get('Serial Number')}")
        print(f"  Machine Number: {record.get('Machine Number')}")
        
        mapped = smart_field_mapping(record, 'machines')
        print("Mapped data:")
        print(f"  name: {mapped.get('name')}")
        print(f"  serial_number: {mapped.get('serial_number')}")
        print(f"  machine_number: {mapped.get('machine_number')}")
        print(f"  model: {mapped.get('model')}")
        
        # Check if essential data is present
        name = str(mapped.get('name', '')).strip()
        print(f"  Has valid name: {bool(name)}")

if __name__ == "__main__":
    test_field_mapping()
