"""
Maintenance statistics and analytics module
Provides statistical analysis of maintenance data
"""
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import base64
from io import BytesIO

# Try importing visualization libraries, make them optional
try:
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False

class MaintenanceAnalytics:
    """
    Analytics for maintenance operations and performance
    """
    
    def __init__(self, offline_db):
        """Initialize with offline database"""
        self.db = offline_db
        self.logger = logging.getLogger("MaintenanceAnalytics")
        
    def get_maintenance_summary(self, start_date=None, end_date=None, site_id=None):
        """
        Get a summary of maintenance activities for a given period
        
        Args:
            start_date: Beginning of date range (defaults to 30 days ago)
            end_date: End of date range (defaults to today)
            site_id: Filter by specific site ID
            
        Returns:
            Dictionary containing maintenance summary statistics
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).date()
        if not end_date:
            end_date = datetime.now().date()
            
        # Build query parameters
        query = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        
        if site_id:
            query["site_id"] = site_id
            
        # Get maintenance data
        maintenance_records = self.db.get_maintenance_records_for_period(
            query["start_date"],
            query["end_date"],
            site_id
        )
        
        if not maintenance_records:
            return {
                "total_maintenance_count": 0,
                "preventative_count": 0,
                "corrective_count": 0,
                "unique_parts_maintained": 0,
                "most_maintained_parts": [],
                "avg_time_between_maintenance": 0,
                "maintenance_by_day": {},
                "period_start": query["start_date"],
                "period_end": query["end_date"],
                "site_id": site_id
            }
            
        # Calculate statistics
        stats = self._calculate_maintenance_stats(maintenance_records)
        
        # Add query parameters to results
        stats.update({
            "period_start": query["start_date"],
            "period_end": query["end_date"],
            "site_id": site_id
        })
        
        return stats
        
    def _calculate_maintenance_stats(self, records):
        """Calculate statistics from maintenance records"""
        if not records:
            return {}
            
        # Initialize counters
        preventative_count = 0
        corrective_count = 0
        parts_map = {}  # Map part_id to count
        maintenance_dates = {}  # Map date to count
        time_between_map = {}  # Map part_id to list of time differences
        
        # Process each record
        for record in records:
            # Determine maintenance type
            is_preventative = record.get('is_preventative', True)
            if is_preventative:
                preventative_count += 1
            else:
                corrective_count += 1
                
            # Track part frequencies
            part_id = record.get('part_id')
            parts_map[part_id] = parts_map.get(part_id, 0) + 1
            
            # Track by date
            maint_date = record.get('timestamp', '').split('T')[0]  # Get date part only
            maintenance_dates[maint_date] = maintenance_dates.get(maint_date, 0) + 1
            
            # Track time between maintenance (for same part)
            if part_id in time_between_map:
                try:
                    last_date = datetime.fromisoformat(time_between_map[part_id][-1])
                    current_date = datetime.fromisoformat(record.get('timestamp'))
                    days_diff = (current_date - last_date).days
                    if days_diff > 0:  # Only count positive differences
                        time_between_map[part_id].append(days_diff)
                except (ValueError, IndexError):
                    time_between_map[part_id].append(record.get('timestamp'))
            else:
                time_between_map[part_id] = [record.get('timestamp')]
        
        # Calculate top maintained parts
        most_maintained = sorted(
            [{"id": k, "count": v} for k, v in parts_map.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:5]  # Top 5
        
        # Calculate average time between maintenance
        avg_time_between = 0
        time_diffs = []
        for part_id, timestamps in time_between_map.items():
            if isinstance(timestamps[0], int):  # Already calculated differences
                time_diffs.extend(timestamps)
        
        if time_diffs:
            avg_time_between = sum(time_diffs) / len(time_diffs)
            
        # Return all statistics
        return {
            "total_maintenance_count": len(records),
            "preventative_count": preventative_count,
            "corrective_count": corrective_count,
            "unique_parts_maintained": len(parts_map),
            "most_maintained_parts": most_maintained,
            "avg_time_between_maintenance": avg_time_between,
            "maintenance_by_day": maintenance_dates
        }
    
    def get_maintenance_by_part_chart(self, start_date=None, end_date=None, site_id=None, limit=10):
        """
        Generate a chart of maintenance by part
        
        Returns:
            Base64 encoded PNG image of the chart
        """
        if not PLOTTING_AVAILABLE:
            self.logger.warning("Plotting libraries not available")
            return None
            
        # Get data
        records = self.db.get_maintenance_records_for_period(
            start_date.isoformat() if start_date else None,
            end_date.isoformat() if end_date else None,
            site_id
        )
        
        if not records:
            return None
            
        # Count by part
        part_counts = {}
        part_names = {}
        
        for record in records:
            part_id = record.get('part_id')
            part_name = self._get_part_name(part_id)
            part_names[part_id] = part_name
            part_counts[part_id] = part_counts.get(part_id, 0) + 1
        
        # Sort and limit
        sorted_parts = sorted(part_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        # Create plot
        fig, ax = plt.subplots(figsize=(10, 6))
        
        x_data = [part_names.get(part_id, part_id) for part_id, _ in sorted_parts]
        y_data = [count for _, count in sorted_parts]
        
        ax.bar(x_data, y_data, color='#3498db')
        ax.set_xlabel('Part')
        ax.set_ylabel('Maintenance Count')
        ax.set_title('Maintenance by Part')
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Convert plot to base64 image
        buffer = BytesIO()
        fig.savefig(buffer, format='png')
        buffer.seek(0)
        image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close(fig)
        
        return image_data
    
    def get_maintenance_trend_chart(self, start_date=None, end_date=None, site_id=None):
        """
        Generate a chart of maintenance trends over time
        
        Returns:
            Base64 encoded PNG image of the chart
        """
        if not PLOTTING_AVAILABLE:
            self.logger.warning("Plotting libraries not available")
            return None
            
        if not start_date:
            start_date = (datetime.now() - timedelta(days=90)).date()
        if not end_date:
            end_date = datetime.now().date()
            
        # Get data
        records = self.db.get_maintenance_records_for_period(
            start_date.isoformat(),
            end_date.isoformat(),
            site_id
        )
        
        if not records:
            return None
            
        # Create date buckets
        date_range = (end_date - start_date).days + 1
        
        # Determine appropriate time buckets based on date range
        if date_range <= 31:  # Up to a month, daily
            bucket_size = 'day'
        elif date_range <= 92:  # Up to 3 months, weekly
            bucket_size = 'week'
        else:  # Beyond 3 months, monthly
            bucket_size = 'month'
        
        # Process records into buckets
        preventative_data = {}
        corrective_data = {}
        
        for record in records:
            try:
                maint_date = datetime.fromisoformat(record.get('timestamp')).date()
                
                # Determine bucket key based on bucket size
                if bucket_size == 'day':
                    bucket_key = maint_date.isoformat()
                elif bucket_size == 'week':
                    # ISO week format: YYYY-WW
                    bucket_key = f"{maint_date.year}-W{maint_date.isocalendar()[1]:02d}"
                else:  # month
                    bucket_key = f"{maint_date.year}-{maint_date.month:02d}"
                
                # Count by maintenance type
                is_preventative = record.get('is_preventative', True)
                if is_preventative:
                    preventative_data[bucket_key] = preventative_data.get(bucket_key, 0) + 1
                else:
                    corrective_data[bucket_key] = corrective_data.get(bucket_key, 0) + 1
                    
            except (ValueError, AttributeError):
                continue
        
        # Create complete date range for x-axis
        x_keys = []
        current_date = start_date
        while current_date <= end_date:
            if bucket_size == 'day':
                x_keys.append(current_date.isoformat())
                current_date += timedelta(days=1)
            elif bucket_size == 'week':
                week_key = f"{current_date.year}-W{current_date.isocalendar()[1]:02d}"
                if week_key not in x_keys:
                    x_keys.append(week_key)
                current_date += timedelta(days=7)
            else:  # month
                month_key = f"{current_date.year}-{current_date.month:02d}"
                if month_key not in x_keys:
                    x_keys.append(month_key)
                # Move to next month
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
        
        # Fill missing values with zeros
        preventative_counts = [preventative_data.get(key, 0) for key in x_keys]
        corrective_counts = [corrective_data.get(key, 0) for key in x_keys]
        
        # Format x-axis labels
        if bucket_size == 'day':
            x_labels = [key[-5:] for key in x_keys]  # Just MM-DD
        elif bucket_size == 'week':
            x_labels = [f"W{key[-2:]}" for key in x_keys]  # Just week number
        else:  # month
            x_labels = [key[-2:] for key in x_keys]  # Just month number
            
        # Create the plot
        fig, ax = plt.subplots(figsize=(12, 6))
        
        width = 0.35
        x = np.arange(len(x_keys))
        
        ax.bar(x - width/2, preventative_counts, width, label='Preventative', color='#2ecc71')
        ax.bar(x + width/2, corrective_counts, width, label='Corrective', color='#e74c3c')
        
        ax.set_xlabel('Time Period')
        ax.set_ylabel('Maintenance Count')
        ax.set_title(f'Maintenance Trend ({bucket_size.capitalize()} View)')
        ax.set_xticks(x)
        
        # Only show subset of x labels if there are many
        if len(x_labels) > 12:
            step = len(x_labels) // 12 + 1
            ax.set_xticklabels(x_labels[::step])
            ax.set_xticks(x[::step])
        else:
            ax.set_xticklabels(x_labels)
            
        ax.legend()
        plt.tight_layout()
        
        # Convert plot to base64 image
        buffer = BytesIO()
        fig.savefig(buffer, format='png')
        buffer.seek(0)
        image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close(fig)
        
        return image_data
    
    def _get_part_name(self, part_id):
        """Get part name from part ID"""
        part_data = self.db.get_part_data(part_id)
        if part_data and isinstance(part_data, dict):
            return part_data.get('name', part_id)
        return part_id
