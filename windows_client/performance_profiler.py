"""
Performance profiling and optimization utilities
"""
import time
import functools
import logging
import threading
import cProfile
import pstats
import io
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime

class PerformanceProfiler:
    """
    Utility for profiling and optimizing application performance
    """
    
    def __init__(self, log_level=logging.INFO):
        """Initialize the performance profiler"""
        self.logger = logging.getLogger("PerformanceProfiler")
        self.logger.setLevel(log_level)
        
        # Store performance metrics
        self.metrics = {}
        self.function_times = {}
        self.critical_paths = {}
        self._lock = threading.RLock()
    
    def timed(self, category: str = "default"):
        """
        Decorator for timing function execution
        
        Args:
            category: Category to group timing results
        
        Example:
            @profiler.timed("database")
            def query_database(param):
                # Function implementation
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    return func(*args, **kwargs)
                finally:
                    elapsed = time.time() - start_time
                    self._record_function_time(func.__qualname__, elapsed, category)
            return wrapper
        return decorator
    
    def profile_function(self, func_name=None):
        """
        Decorator to do detailed cProfile profiling of a function
        
        Args:
            func_name: Optional custom name for the function
        """
        def decorator(func):
            name = func_name or func.__qualname__
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                profiler = cProfile.Profile()
                result = None
                try:
                    result = profiler.runcall(func, *args, **kwargs)
                    return result
                finally:
                    output = io.StringIO()
                    stats = pstats.Stats(profiler, stream=output)
                    stats.sort_stats('cumulative')
                    stats.print_stats(20)  # Print top 20 lines
                    
                    # Log the profile data
                    self.logger.debug(f"Profile for {name}:\n{output.getvalue()}")
                    
                    # Store summary data
                    with self._lock:
                        path = []
                        # Extract the critical path (most time consuming function calls)
                        for func, (calls, ccalls, total_time, cumtime, callers) in stats.stats.items():
                            if len(path) < 5:  # Store top 5 most expensive functions
                                path.append({
                                    'func': f"{func[0]}:{func[1]}({func[2]})",
                                    'calls': calls,
                                    'time': cumtime,
                                    'time_per_call': cumtime / calls if calls else 0
                                })
                        
                        # Sort by time
                        path.sort(key=lambda x: x['time'], reverse=True)
                        self.critical_paths[name] = path
                        
            return wrapper
        return decorator
    
    def _record_function_time(self, func_name, elapsed, category="default"):
        """Record function execution time"""
        with self._lock:
            if category not in self.function_times:
                self.function_times[category] = {}
                
            if func_name not in self.function_times[category]:
                self.function_times[category][func_name] = {
                    'count': 0, 
                    'total_time': 0, 
                    'min_time': float('inf'),
                    'max_time': 0
                }
            
            stats = self.function_times[category][func_name]
            stats['count'] += 1
            stats['total_time'] += elapsed
            stats['min_time'] = min(stats['min_time'], elapsed)
            stats['max_time'] = max(stats['max_time'], elapsed)
    
    def start_measurement(self, name: str):
        """
        Start measuring time for a code block
        
        Args:
            name: Name of the measurement
        
        Returns:
            Measurement token to pass to end_measurement
        """
        return (name, time.time())
    
    def end_measurement(self, token, category: str = "default"):
        """
        End measuring time for a code block
        
        Args:
            token: Token returned from start_measurement
            category: Category to group timing results
        """
        name, start_time = token
        elapsed = time.time() - start_time
        self._record_function_time(name, elapsed, category)
    
    def get_function_times(self, category: Optional[str] = None) -> Dict:
        """
        Get timing statistics for functions
        
        Args:
            category: Optional category to filter by
            
        Returns:
            Dictionary of timing statistics
        """
        with self._lock:
            if category:
                return self.function_times.get(category, {})
            return self.function_times
    
    def get_critical_paths(self) -> Dict:
        """
        Get critical path information for profiled functions
        
        Returns:
            Dictionary of critical path data
        """
        with self._lock:
            return self.critical_paths
    
    def get_slowest_functions(self, category: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """
        Get the slowest functions based on average execution time
        
        Args:
            category: Optional category to filter by
            limit: Maximum number of functions to return
            
        Returns:
            List of function timing data
        """
        result = []
        
        with self._lock:
            categories = [category] if category else self.function_times.keys()
            
            for cat in categories:
                if cat not in self.function_times:
                    continue
                    
                for func_name, stats in self.function_times[cat].items():
                    avg_time = stats['total_time'] / stats['count'] if stats['count'] > 0 else 0
                    
                    result.append({
                        'function': func_name,
                        'category': cat,
                        'count': stats['count'],
                        'total_time': stats['total_time'],
                        'avg_time': avg_time,
                        'min_time': stats['min_time'],
                        'max_time': stats['max_time']
                    })
        
        # Sort by average time (descending) and limit results
        result.sort(key=lambda x: x['avg_time'], reverse=True)
        return result[:limit]
    
    def reset_metrics(self):
        """Reset all collected metrics"""
        with self._lock:
            self.metrics = {}
            self.function_times = {}
            self.critical_paths = {}
    
    def analyze_database_performance(self, offline_db):
        """
        Analyze database performance
        
        Args:
            offline_db: Offline database instance to analyze
            
        Returns:
            Dictionary of database performance metrics
        """
        results = {}
        
        try:
            # Record initial stats
            initial_stats = {}
            
            # Measure common operations
            operations = [
                ("get_part_data", lambda: offline_db.get_part_data("test_part_id")),
                ("get_pending_operations", lambda: offline_db.get_pending_operations()),
                ("get_maintenance_records_for_period", 
                 lambda: offline_db.get_maintenance_records_for_period(
                     (datetime.now() - timedelta(days=30)).isoformat(),
                     datetime.now().isoformat()
                 )),
                ("get_maintenance_schedules", lambda: offline_db.get_maintenance_schedules()),
                ("get_sync_history", lambda: offline_db.get_sync_history(limit=100))
            ]
            
            # Measure each operation
            for name, operation in operations:
                token = self.start_measurement(f"db_{name}")
                try:
                    # Execute operation
                    operation()
                except Exception as e:
                    self.logger.error(f"Error in database operation {name}: {e}")
                finally:
                    self.end_measurement(token, "database")
            
            # Get metrics
            db_metrics = self.get_function_times("database")
            results["operations"] = db_metrics
            
            # Analyze query times
            slow_queries = []
            for name, stats in db_metrics.items():
                avg_time = stats['total_time'] / stats['count'] if stats['count'] > 0 else 0
                if avg_time > 0.1:  # Threshold for slow queries (100ms)
                    slow_queries.append({
                        'operation': name,
                        'avg_time': avg_time,
                        'count': stats['count']
                    })
            
            results["slow_queries"] = slow_queries
            
            # Add recommendations
            recommendations = []
            
            if slow_queries:
                recommendations.append("Consider adding indexes for frequently queried columns")
                recommendations.append("Review database schema for optimization opportunities")
                recommendations.append("Consider using query caching for frequently accessed data")
            
            # Check database size
            if hasattr(offline_db, 'db_path') and os.path.exists(offline_db.db_path):
                db_size_mb = os.path.getsize(offline_db.db_path) / (1024 * 1024)
                results["database_size_mb"] = db_size_mb
                
                if db_size_mb > 100:
                    recommendations.append("Database is large. Consider implementing data pruning")
            
            results["recommendations"] = recommendations
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing database performance: {e}")
            return {"error": str(e)}

# Global instance that can be imported directly
profiler = PerformanceProfiler()
