"""
Create an Excel template file for importing maintenance data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def create_template(output_file="maintenance_import_template.xlsx"):
    """Create a template Excel file with example data."""
    
    # Create a Pandas Excel writer
    writer = pd.ExcelWriter(output_file, engine='openpyxl')
    
    # Create example sites data
    sites_data = {
        'name': ['Main Factory', 'Assembly Plant', 'Distribution Center'],
        'location': ['123 Industrial Ave', '456 Production Blvd', '789 Shipping Lane'],
        'contact_email': ['factory@example.com', 'assembly@example.com', 'distribution@example.com'],
        'enable_notifications': [True, True, False],
        'notification_threshold': [7, 14, 7]
    }
    sites_df = pd.DataFrame(sites_data)
    sites_df.to_excel(writer, sheet_name='Sites', index=False)
    
    # Create example machines data
    machines_data = {
        'name': ['CNC Mill', 'Lathe', 'Drill Press', 'Assembly Robot', 'Conveyor'],
        'model': ['XYZ-1000', 'LT-500', 'DP-750', 'AR-200', 'CV-100'],
        'site_name': ['Main Factory', 'Main Factory', 'Assembly Plant', 'Assembly Plant', 'Distribution Center']
    }
    machines_df = pd.DataFrame(machines_data)
    machines_df.to_excel(writer, sheet_name='Machines', index=False)
    
    # Create example parts data
    now = datetime.utcnow()
    parts_data = {
        'name': ['Spindle', 'Coolant System', 'Tool Changer', 'Chuck', 'Tailstock', 
                'Drill Bit', 'Table', 'Servo Motor A', 'Servo Motor B', 'Conveyor Belt'],
        'description': ['Main cutting spindle', 'Cutting fluid circulation', 'Automatic tool changer',
                       'Workholding device', 'Supports workpiece end', 'Cutting tool',
                       'Work surface', 'Axis 1 movement', 'Axis 2 movement', 'Main belt'],
        'machine_name': ['CNC Mill', 'CNC Mill', 'CNC Mill', 'Lathe', 'Lathe',
                        'Drill Press', 'Drill Press', 'Assembly Robot', 'Assembly Robot', 'Conveyor'],
        'site_name': ['Main Factory', 'Main Factory', 'Main Factory', 'Main Factory', 'Main Factory',
                     'Assembly Plant', 'Assembly Plant', 'Assembly Plant', 'Assembly Plant', 'Distribution Center'],
        'maintenance_frequency': [7, 14, 30, 21, 30, 45, 60, 60, 90, 120],
        'last_maintenance': [
            (now - timedelta(days=5)).strftime('%Y-%m-%d'),
            (now - timedelta(days=10)).strftime('%Y-%m-%d'),
            (now - timedelta(days=15)).strftime('%Y-%m-%d'),
            (now - timedelta(days=10)).strftime('%Y-%m-%d'),
            (now - timedelta(days=20)).strftime('%Y-%m-%d'),
            (now - timedelta(days=15)).strftime('%Y-%m-%d'),
            (now - timedelta(days=10)).strftime('%Y-%m-%d'),
            (now - timedelta(days=5)).strftime('%Y-%m-%d'),
            (now - timedelta(days=25)).strftime('%Y-%m-%d'),
            (now - timedelta(days=30)).strftime('%Y-%m-%d'),
        ]
    }
    parts_df = pd.DataFrame(parts_data)
    parts_df.to_excel(writer, sheet_name='Parts', index=False)
    
    # Add instructions sheet
    instructions = """
    # Maintenance Data Import Instructions
    
    This Excel file is used to import maintenance data into the Maintenance Tracker system.
    
    ## Sheets and Required Columns:
    
    1. Sites
       - name (required): The name of the site
       - location (required): The location of the site
       - contact_email: Email address for maintenance notifications
       - enable_notifications: TRUE/FALSE to enable/disable notifications
       - notification_threshold: Days before due date to send notification
    
    2. Machines
       - name (required): The name of the machine
       - model: The model number/name of the machine
       - site_name (required): Must match a site name in the Sites sheet
    
    3. Parts
       - name (required): The name of the part
       - description: A description of the part
       - machine_name (required): Must match a machine name in the Machines sheet
       - site_name (required): Must match the site where the machine is located
       - maintenance_frequency (required): Number of days between maintenance
       - last_maintenance: Date of last maintenance (YYYY-MM-DD)
    
    ## Import Order:
    The import process will:
    1. First import all sites
    2. Then import machines (matching to sites)
    3. Finally import parts (matching to machines and sites)
    
    ## Duplicates:
    If a site, machine, or part with the same name already exists, it will be skipped during import.
    """
    
    instructions_df = pd.DataFrame({'Instructions': [instructions]})
    instructions_df.to_excel(writer, sheet_name='Instructions', index=False, header=False)
    
    # Save the Excel file
    writer.save()
    print(f"Template created successfully: {output_file}")

if __name__ == "__main__":
    create_template()
