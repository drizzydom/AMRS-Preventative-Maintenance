#!/usr/bin/env python3
"""
Debug script to analyze the JSON import data and identify why only some machines are being imported.
"""

import json

def analyze_json_data(file_path):
    """Analyze the JSON data to identify potential import issues"""
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    print(f"Total records in JSON: {len(data)}")
    
    valid_machines = []
    invalid_records = []
    
    for i, record in enumerate(data):
        # Check if record has essential machine data
        has_machine_name = record.get('Machine') is not None and str(record.get('Machine')).strip() != ''
        has_serial = record.get('Serial Number') is not None and str(record.get('Serial Number')).strip() != ''
        
        # Check if all values are null/empty
        all_null = all(v is None or str(v).strip() == '' for v in record.values())
        
        if all_null:
            invalid_records.append(f"Record {i+1}: All null values")
        elif has_machine_name or has_serial:
            machine_info = {
                'index': i+1,
                'machine_name': record.get('Machine', 'N/A'),
                'serial_number': record.get('Serial Number', 'N/A'),
                'machine_number': record.get('Machine Number', 'N/A'),
                'has_maintenance_data': 'MaintenanceData' in record and record['MaintenanceData'] is not None
            }
            valid_machines.append(machine_info)
        else:
            invalid_records.append(f"Record {i+1}: Missing essential data - Machine: {record.get('Machine')}, Serial: {record.get('Serial Number')}")
    
    print(f"\nValid machine records: {len(valid_machines)}")
    for machine in valid_machines:
        print(f"  {machine['index']}: {machine['machine_name']} (Serial: {machine['serial_number']}, Has Maintenance: {machine['has_maintenance_data']})")
    
    print(f"\nInvalid records: {len(invalid_records)}")
    for invalid in invalid_records[:5]:  # Show first 5 invalid records
        print(f"  {invalid}")
    
    if len(invalid_records) > 5:
        print(f"  ... and {len(invalid_records) - 5} more invalid records")
    
    # Check for duplicates
    print("\nDuplicate analysis:")
    names = [m['machine_name'] for m in valid_machines if m['machine_name'] != 'N/A']
    serials = [m['serial_number'] for m in valid_machines if m['serial_number'] != 'N/A']
    
    from collections import Counter
    name_counts = Counter(names)
    serial_counts = Counter(serials)
    
    print("Machine name frequency:")
    for name, count in name_counts.items():
        if count > 1:
            print(f"  '{name}': {count} times")
        else:
            print(f"  '{name}': {count} time")
    
    print("\nSerial number frequency:")
    for serial, count in serial_counts.items():
        if count > 1:
            print(f"  '{serial}': {count} times (DUPLICATE!)")
        else:
            print(f"  '{serial}': {count} time")

if __name__ == "__main__":
    # Analyze the provided JSON file
    analyze_json_data("/Users/dominicmoriello/Documents/Excel Exporter/output_KL_Microwave PM.json")
