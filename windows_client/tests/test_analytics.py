import os
import sys
import unittest
import tempfile
import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Add parent directory to path to import application modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Try importing the analytics modules
try:
    from analytics.maintenance_stats import MaintenanceAnalytics
    from analytics.system_health import SystemHealthAnalytics
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False

@unittest.skipIf(not ANALYTICS_AVAILABLE, "Analytics modules not available")
class TestMaintenanceAnalytics(unittest.TestCase):
    """Tests for the MaintenanceAnalytics class"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a mock offline_db
        self.mock_db = MagicMock()
        
        # Create sample maintenance records for testing
        self.sample_records = [
            {
                "id": "record1",
                "part_id": "part1",
                "timestamp": (datetime.now() - timedelta(days=5)).isoformat(),
                "synced": True,
                "part_name": "Test Part 1",
                "machine_id": "machine1",
                "is_preventative": True,
                "data": {"notes": "Routine maintenance"}
            },
            {
                "id": "record2",
                "part_id": "part2",
                "timestamp": (datetime.now() - timedelta(days=3)).isoformat(),
                "synced": True,
                "part_name": "Test Part 2",
                "machine_id": "machine1",
                "is_preventative": False,
                "data": {"notes": "Repair required"}
            },
            {
                "id": "record3",
                "part_id": "part1",
                "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
                "synced": False,
                "part_name": "Test Part 1",
                "machine_id": "machine1",
                "is_preventative": True,
                "data": {"notes": "Follow-up maintenance"}
            }
        ]
        
        # Configure the mock to return our sample records
        self.mock_db.get_maintenance_records_for_period.return_value = self.sample_records
        
        # Mock part data retrieval
        self.mock_db.get_part_data.return_value = {"name": "Mock Part", "id": "part1"}
        
        # Create the analytics instance with the mock db
        self.analytics = MaintenanceAnalytics(self.mock_db)
        
    def test_get_maintenance_summary(self):
        """Test getting maintenance summary statistics"""
        # Call the method
        summary = self.analytics.get_maintenance_summary()
        
        # Verify the result contains expected keys
        self.assertIn("total_maintenance_count", summary)
        self.assertIn("preventative_count", summary)
        self.assertIn("corrective_count", summary)
        self.assertIn("unique_parts_maintained", summary)
        
        # Verify values match our sample data
        self.assertEqual(summary["total_maintenance_count"], 3)
        self.assertEqual(summary["preventative_count"], 2)
        self.assertEqual(summary["corrective_count"], 1)
        self.assertEqual(summary["unique_parts_maintained"], 2)
    
    def test_get_part_name(self):
        """Test retrieving part names"""
        part_name = self.analytics._get_part_name("part1")
        self.assertEqual(part_name, "Mock Part")
        
        # Test with unknown part
        self.mock_db.get_part_data.return_value = None
        part_name = self.analytics._get_part_name("unknown_part")
        self.assertEqual(part_name, "unknown_part")
    
    @patch("analytics.maintenance_stats.PLOTTING_AVAILABLE", False)
    def test_chart_generation_unavailable(self):
        """Test behavior when plotting libraries are unavailable"""
        # With plotting unavailable, chart methods should return None
        result = self.analytics.get_maintenance_trend_chart()
        self.assertIsNone(result)
        
        result = self.analytics.get_maintenance_by_part_chart()
        self.assertIsNone(result)

@unittest.skipIf(not ANALYTICS_AVAILABLE, "Analytics modules not available")
class TestSystemHealthAnalytics(unittest.TestCase):
    """Tests for the SystemHealthAnalytics class"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a mock offline_db with a temporary database file
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_db.sqlite")
        
        # Create a small SQLite database for testing
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)")
        cursor.execute("INSERT INTO test_table VALUES (1, 'Test')")
        conn.commit()
        conn.close()
        
        # Create a mock db object with the real db_path
        self.mock_db = MagicMock()
        self.mock_db.db_path = self.db_path
        
        # Mock sync history
        self.mock_db.get_sync_history.return_value = [
            {"status": "success", "timestamp": datetime.now().isoformat(), "operations_count": 10}
        ]
        
        # Mock pending operations
        self.mock_db.get_pending_operations.return_value = [{"id": "op1"}]
        
        # Mock failed operations count
        self.mock_db.get_failed_operations_count.return_value = 0
        
        # Create mock diagnostics manager
        self.mock_diagnostics = MagicMock()
        self.mock_diagnostics.metrics = {
            "app_cpu_percent": [5.0, 10.0, 15.0],
            "app_memory_mb": [50.0, 55.0, 60.0]
        }
        
        # Create the health analytics instance
        self.health_analytics = SystemHealthAnalytics(self.mock_db, self.mock_diagnostics)
    
    def tearDown(self):
        """Clean up after tests"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_get_database_health(self):
        """Test getting database health information"""
        health_info = self.health_analytics.get_database_health()
        
        self.assertIn("status", health_info)
        self.assertIn("database_path", health_info)
        self.assertIn("file_size_bytes", health_info)
        self.assertIn("file_size_mb", health_info)
        self.assertIn("total_tables", health_info)
        
        # Since we're using a real file, verify some values
        self.assertEqual(health_info["database_path"], self.db_path)
        self.assertGreater(health_info["file_size_bytes"], 0)
        self.assertEqual(health_info["total_tables"], 1)  # Our test_table
    
    def test_get_sync_health(self):
        """Test getting sync health information"""
        sync_health = self.health_analytics.get_sync_health()
        
        self.assertIn("status", sync_health)
        self.assertIn("pending_operations", sync_health)
        self.assertIn("failed_operations", sync_health)
        self.assertIn("success_rate", sync_health)
        
        # Verify values match our mocked data
        self.assertEqual(sync_health["pending_operations"], 1)
        self.assertEqual(sync_health["failed_operations"], 0)
        self.assertEqual(sync_health["success_rate"], 100.0)
    
    @patch("analytics.system_health.PLOTTING_AVAILABLE", False)
    def test_performance_chart_unavailable(self):
        """Test behavior when plotting libraries are unavailable"""
        # With plotting unavailable, chart methods should return None
        result = self.health_analytics.get_performance_chart()
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()
