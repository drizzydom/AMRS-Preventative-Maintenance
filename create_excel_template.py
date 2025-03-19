"""
Create an Excel template file for importing maintenance data.
"""

import pandas as pd
from datetime import datetime

def create_template(output_file="maintenance_import_template.xlsx"):
    """Create a template Excel file with example data."""
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Sites sheet
        sites_df = pd.DataFrame({
            'name': ['Example Site 1', 'Example Site 2'],
            'location': ['123 Main St', '456 Elm St'],
            'contact_email': ['site1@example.com', 'site2@example.com'],
            'enable_notifications': [True, False],
            'notification_threshold': [7, 14]
        })
        sites_df.to_excel(writer, sheet_name='Sites', index=False)
        
        # Machines sheet
        machines_df = pd.DataFrame({
            'name': ['Machine 1', 'Machine 2', 'Machine 3'],
            'model': ['Model A', 'Model B', 'Model C'],
            'site_name': ['Example Site 1', 'Example Site 1', 'Example Site 2']
        })
        machines_df.to_excel(writer, sheet_name='Machines', index=False)
        
        # Parts sheet
        today = datetime.now().strftime('%Y-%m-%d')
        parts_df = pd.DataFrame({
            'name': ['Part 1', 'Part 2', 'Part 3', 'Part 4'],
            'description': ['Description 1', 'Description 2', 'Description 3', 'Description 4'],
            'machine_name': ['Machine 1', 'Machine 1', 'Machine 2', 'Machine 3'],
            'site_name': ['Example Site 1', 'Example Site 1', 'Example Site 1', 'Example Site 2'],
            'maintenance_frequency': [7, 14, 30, 90],
            'last_maintenance': [today, today, today, today]
        })
        parts_df.to_excel(writer, sheet_name='Parts', index=False)
    
    print(f"Template created successfully: {output_file}")

if __name__ == "__main__":
    create_template()
