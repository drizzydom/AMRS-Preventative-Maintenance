import os
import pandas as pd
from datetime import datetime
from app import db, Site, Machine, Part

def import_excel(file_path):
    """Import maintenance data from an Excel file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Excel file not found: {file_path}")
        
    stats = {
        'sites_added': 0,
        'sites_skipped': 0,
        'machines_added': 0,
        'machines_skipped': 0,
        'parts_added': 0,
        'parts_skipped': 0,
        'errors': []
    }
    
    try:
        # Read sites sheet
        sites_df = pd.read_excel(file_path, sheet_name='Sites')
        for _, row in sites_df.iterrows():
            site_name = row.get('name')
            if not site_name:
                stats['errors'].append("Skipped site with missing name")
                continue
                
            # Check if site already exists
            existing_site = Site.query.filter_by(name=site_name).first()
            if existing_site:
                stats['sites_skipped'] += 1
                continue
                
            # Create new site
            new_site = Site(
                name=site_name,
                location=row.get('location', ''),
                contact_email=row.get('contact_email', ''),
                enable_notifications=bool(row.get('enable_notifications', False)),
                notification_threshold=int(row.get('notification_threshold', 7))
            )
            db.session.add(new_site)
            stats['sites_added'] += 1
            
        db.session.commit()
        
        # Read machines sheet
        machines_df = pd.read_excel(file_path, sheet_name='Machines')
        for _, row in machines_df.iterrows():
            machine_name = row.get('name')
            site_name = row.get('site_name')
            
            if not machine_name or not site_name:
                stats['errors'].append("Skipped machine with missing name or site")
                continue
                
            # Find site
            site = Site.query.filter_by(name=site_name).first()
            if not site:
                stats['errors'].append(f"Site not found for machine: {machine_name}")
                continue
                
            # Check if machine already exists
            existing_machine = Machine.query.filter_by(name=machine_name, site_id=site.id).first()
            if existing_machine:
                stats['machines_skipped'] += 1
                continue
                
            # Create new machine
            new_machine = Machine(
                name=machine_name,
                model=row.get('model', ''),
                machine_number=row.get('machine_number', ''),
                serial_number=row.get('serial_number', ''),
                site_id=site.id
            )
            db.session.add(new_machine)
            stats['machines_added'] += 1
            
        db.session.commit()
        
        # Read parts sheet
        parts_df = pd.read_excel(file_path, sheet_name='Parts')
        for _, row in parts_df.iterrows():
            part_name = row.get('name')
            machine_name = row.get('machine_name')
            site_name = row.get('site_name')
            
            if not part_name or not machine_name or not site_name:
                stats['errors'].append("Skipped part with missing information")
                continue
                
            # Find site and machine
            site = Site.query.filter_by(name=site_name).first()
            if not site:
                stats['errors'].append(f"Site not found for part: {part_name}")
                continue
                
            machine = Machine.query.filter_by(name=machine_name, site_id=site.id).first()
            if not machine:
                stats['errors'].append(f"Machine not found for part: {part_name}")
                continue
                
            # Check if part already exists
            existing_part = Part.query.filter_by(name=part_name, machine_id=machine.id).first()
            if existing_part:
                stats['parts_skipped'] += 1
                continue
                
            # Parse maintenance frequency and date
            try:
                maintenance_frequency = int(row.get('maintenance_frequency', 7))
                last_maintenance_str = row.get('last_maintenance')
                if last_maintenance_str:
                    if isinstance(last_maintenance_str, str):
                        last_maintenance = datetime.strptime(last_maintenance_str, '%Y-%m-%d')
                    else:
                        last_maintenance = last_maintenance_str  # Assume it's already a datetime
                else:
                    last_maintenance = datetime.utcnow()
            except Exception as e:
                stats['errors'].append(f"Error parsing maintenance info for {part_name}: {str(e)}")
                continue
                
            # Create new part
            new_part = Part(
                name=part_name,
                description=row.get('description', ''),
                machine_id=machine.id,
                maintenance_frequency=maintenance_frequency,
                last_maintenance=last_maintenance
            )
            new_part.update_next_maintenance()
            db.session.add(new_part)
            stats['parts_added'] += 1
            
        db.session.commit()
        
        return stats
        
    except Exception as e:
        db.session.rollback()
        raise Exception(f"Error importing Excel data: {str(e)}")
