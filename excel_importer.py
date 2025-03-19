"""
Excel Import Tool for Maintenance Tracker

This script provides functionality to import maintenance data from Excel files
into the Maintenance Tracker database.
"""

import pandas as pd
import numpy as np
import os
import logging
from datetime import datetime
from app import db, Site, Machine, Part, User, app

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('excel_importer')

class ExcelImporter:
    """Class to handle importing data from Excel files into the database."""
    
    def __init__(self, file_path):
        """Initialize with the path to the Excel file."""
        self.file_path = file_path
        self.stats = {
            'sites_added': 0,
            'sites_skipped': 0,
            'machines_added': 0,
            'machines_skipped': 0,
            'parts_added': 0,
            'parts_skipped': 0,
            'errors': 0,
        }
    
    def validate_file(self):
        """Validate that the Excel file exists and is readable."""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Excel file not found: {self.file_path}")
        
        # Check if pandas can read the file
        try:
            # Just read the sheet names to validate
            pd.ExcelFile(self.file_path).sheet_names
            return True
        except Exception as e:
            raise ValueError(f"Error reading Excel file: {str(e)}")
    
    def import_data(self):
        """Main method to import data from Excel into the database."""
        try:
            self.validate_file()
            excel_file = pd.ExcelFile(self.file_path)
            
            # Process based on available sheets
            sheet_names = excel_file.sheet_names
            
            # First, import sites if the sheet exists
            if 'Sites' in sheet_names:
                self._import_sites(excel_file)
            
            # Next, import machines if the sheet exists
            if 'Machines' in sheet_names:
                self._import_machines(excel_file)
                
            # Finally, import parts and maintenance schedules
            if 'Parts' in sheet_names:
                self._import_parts(excel_file)
            
            # Commit all changes to the database
            db.session.commit()
            return self.stats
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Import failed: {str(e)}")
            self.stats['errors'] += 1
            raise
    
    def _import_sites(self, excel_file):
        """Import sites from the Sites sheet."""
        logger.info("Importing sites...")
        
        # Read the Sites sheet
        df = excel_file.parse('Sites')
        
        # Clean column names and data
        df.columns = df.columns.str.strip().str.lower()
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].str.strip()
        
        # Required columns
        required_cols = ['name', 'location']
        if not all(col in df.columns for col in required_cols):
            missing = [col for col in required_cols if col not in df.columns]
            raise ValueError(f"Sites sheet missing required columns: {', '.join(missing)}")
        
        # Process each row
        for _, row in df.iterrows():
            try:
                # Check if site already exists
                existing_site = Site.query.filter_by(name=row['name']).first()
                if existing_site:
                    logger.info(f"Site already exists: {row['name']}")
                    self.stats['sites_skipped'] += 1
                    continue
                
                # Create new site
                site = Site(
                    name=row['name'],
                    location=row['location']
                )
                
                # Optional fields
                if 'contact_email' in row and not pd.isna(row['contact_email']):
                    site.contact_email = row['contact_email']
                
                if 'enable_notifications' in row:
                    site.enable_notifications = bool(row['enable_notifications'])
                
                if 'notification_threshold' in row and not pd.isna(row['notification_threshold']):
                    site.notification_threshold = int(row['notification_threshold'])
                
                db.session.add(site)
                self.stats['sites_added'] += 1
                logger.info(f"Added site: {site.name}")
                
            except Exception as e:
                logger.error(f"Error processing site {row['name']}: {str(e)}")
                self.stats['errors'] += 1
    
    def _import_machines(self, excel_file):
        """Import machines from the Machines sheet."""
        logger.info("Importing machines...")
        
        # Read the Machines sheet
        df = excel_file.parse('Machines')
        
        # Clean column names and data
        df.columns = df.columns.str.strip().str.lower()
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].str.strip()
        
        # Required columns
        required_cols = ['name', 'site_name']
        if not all(col in df.columns for col in required_cols):
            missing = [col for col in required_cols if col not in df.columns]
            raise ValueError(f"Machines sheet missing required columns: {', '.join(missing)}")
        
        # Process each row
        for _, row in df.iterrows():
            try:
                # Find the site
                site = Site.query.filter_by(name=row['site_name']).first()
                if not site:
                    logger.warning(f"Site not found for machine: {row['name']} (site: {row['site_name']})")
                    self.stats['machines_skipped'] += 1
                    continue
                
                # Check if machine already exists
                existing_machine = Machine.query.filter_by(name=row['name'], site_id=site.id).first()
                if existing_machine:
                    logger.info(f"Machine already exists: {row['name']} at site {site.name}")
                    self.stats['machines_skipped'] += 1
                    continue
                
                # Create new machine
                machine = Machine(
                    name=row['name'],
                    site_id=site.id
                )
                
                # Optional fields
                if 'model' in row and not pd.isna(row['model']):
                    machine.model = row['model']
                
                db.session.add(machine)
                self.stats['machines_added'] += 1
                logger.info(f"Added machine: {machine.name} to site {site.name}")
                
            except Exception as e:
                logger.error(f"Error processing machine {row.get('name', 'unknown')}: {str(e)}")
                self.stats['errors'] += 1
    
    def _import_parts(self, excel_file):
        """Import parts from the Parts sheet."""
        logger.info("Importing parts...")
        
        # Read the Parts sheet
        df = excel_file.parse('Parts')
        
        # Clean column names and data
        df.columns = df.columns.str.strip().str.lower()
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].str.strip()
        
        # Required columns
        required_cols = ['name', 'machine_name', 'site_name', 'maintenance_frequency']
        if not all(col in df.columns for col in required_cols):
            missing = [col for col in required_cols if col not in df.columns]
            raise ValueError(f"Parts sheet missing required columns: {', '.join(missing)}")
        
        # Process each row
        for _, row in df.iterrows():
            try:
                # Find the site
                site = Site.query.filter_by(name=row['site_name']).first()
                if not site:
                    logger.warning(f"Site not found for part: {row['name']} (site: {row['site_name']})")
                    self.stats['parts_skipped'] += 1
                    continue
                
                # Find the machine
                machine = Machine.query.filter_by(name=row['machine_name'], site_id=site.id).first()
                if not machine:
                    logger.warning(f"Machine not found for part: {row['name']} (machine: {row['machine_name']})")
                    self.stats['parts_skipped'] += 1
                    continue
                
                # Check if part already exists
                existing_part = Part.query.filter_by(name=row['name'], machine_id=machine.id).first()
                if existing_part:
                    logger.info(f"Part already exists: {row['name']} on machine {machine.name}")
                    self.stats['parts_skipped'] += 1
                    continue
                
                # Process maintenance parameters
                maintenance_frequency = int(row['maintenance_frequency'])
                
                # Handle last maintenance date if provided
                last_maintenance = datetime.utcnow()
                if 'last_maintenance' in row and not pd.isna(row['last_maintenance']):
                    if isinstance(row['last_maintenance'], str):
                        last_maintenance = datetime.strptime(row['last_maintenance'], '%Y-%m-%d')
                    else:
                        last_maintenance = row['last_maintenance']
                
                # Create new part
                part = Part(
                    name=row['name'],
                    machine_id=machine.id,
                    maintenance_frequency=maintenance_frequency,
                    last_maintenance=last_maintenance
                )
                
                # Optional fields
                if 'description' in row and not pd.isna(row['description']):
                    part.description = row['description']
                
                # Calculate next maintenance date
                part.update_next_maintenance()
                
                db.session.add(part)
                self.stats['parts_added'] += 1
                logger.info(f"Added part: {part.name} to machine {machine.name}")
                
            except Exception as e:
                logger.error(f"Error processing part {row.get('name', 'unknown')}: {str(e)}")
                self.stats['errors'] += 1

def import_excel(file_path):
    """Helper function to import data from an Excel file."""
    importer = ExcelImporter(file_path)
    return importer.import_data()
