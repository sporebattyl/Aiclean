"""
Performance Monitor - Tracks database and system performance metrics
"""
import time
import psutil
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from contextlib import contextmanager
from .database import DatabaseManager


class PerformanceMonitor:
    """Monitors and tracks database and system performance"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.logger = logging.getLogger(__name__)
        self.db = db_manager
        self.query_log = []
        self.max_query_log_size = 1000
        self.slow_query_threshold = 1.0  # seconds
        
        # Performance thresholds
        self.thresholds = {
            'slow_query_ms': 1000,
            'memory_usage_mb': 500,
            'cpu_usage_percent': 80,
            'disk_usage_percent': 90,
            'connection_count': 10
        }
        
        self.logger.info("Performance monitor initialized")
    
    @contextmanager
    def query_timer(self, query_description: str = "Unknown"):
        """Context manager to time database queries"""
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        try:
            yield
        finally:
            end_time = time.time()
            end_memory = self._get_memory_usage()
            duration = (end_time - start_time) * 1000  # Convert to milliseconds
            
            query_info = {
                'description': query_description,
                'duration_ms': duration,
                'memory_before_mb': start_memory,
                'memory_after_mb': end_memory,
                'memory_delta_mb': end_memory - start_memory,
                'timestamp': datetime.now().isoformat(),
                'is_slow': duration > self.slow_query_threshold * 1000
            }
            
            self._log_query_performance(query_info)
    
    def _log_query_performance(self, query_info: Dict[str, Any]):
        """Log query performance information"""
        # Add to in-memory log
        self.query_log.append(query_info)
        
        # Maintain log size
        if len(self.query_log) > self.max_query_log_size:
            self.query_log = self.query_log[-self.max_query_log_size:]
        
        # Log slow queries
        if query_info['is_slow']:
            self.logger.warning(
                f"Slow query detected: {query_info['description']} "
                f"took {query_info['duration_ms']:.2f}ms"
            )
    
    def get_database_statistics(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        try:
            stats = {}
            
            # Database file size
            stats['database_size_mb'] = self._get_database_size_mb()
            
            # Table statistics
            stats['tables'] = self._get_table_statistics()
            
            # Index statistics
            stats['indexes'] = self._get_index_statistics()
            
            # Connection statistics
            stats['connections'] = self._get_connection_statistics()
            
            # Query performance
            stats['query_performance'] = self._get_query_performance_stats()
            
            # Database settings
            stats['settings'] = self._get_database_settings()
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get database statistics: {e}")
            return {'error': str(e)}
    
    def _get_database_size_mb(self) -> float:
        """Get database file size in MB"""
        try:
            import os
            size_bytes = os.path.getsize(self.db.db_path)
            return size_bytes / (1024 * 1024)
        except:
            return 0.0
    
    def _get_table_statistics(self) -> List[Dict[str, Any]]:
        """Get statistics for all tables"""
        tables = []
        
        try:
            # Get all table names
            table_query = "SELECT name FROM sqlite_master WHERE type='table'"
            table_results = self.db.execute_query(table_query)
            
            for table_result in table_results:
                table_name = table_result['name']
                
                # Get row count
                count_result = self.db.execute_single(f"SELECT COUNT(*) as count FROM {table_name}")
                row_count = count_result['count'] if count_result else 0
                
                # Get table info
                info_results = self.db.execute_query(f"PRAGMA table_info({table_name})")
                column_count = len(info_results)
                
                tables.append({
                    'name': table_name,
                    'row_count': row_count,
                    'column_count': column_count,
                    'estimated_size_kb': self._estimate_table_size(table_name)
                })
                
        except Exception as e:
            self.logger.error(f"Failed to get table statistics: {e}")
        
        return tables
    
    def _get_index_statistics(self) -> List[Dict[str, Any]]:
        """Get statistics for all indexes"""
        indexes = []
        
        try:
            index_query = "SELECT name, tbl_name FROM sqlite_master WHERE type='index'"
            index_results = self.db.execute_query(index_query)
            
            for index_result in index_results:
                indexes.append({
                    'name': index_result['name'],
                    'table': index_result['tbl_name']
                })
                
        except Exception as e:
            self.logger.error(f"Failed to get index statistics: {e}")
        
        return indexes
    
    def _get_connection_statistics(self) -> Dict[str, Any]:
        """Get database connection statistics"""
        # SQLite doesn't have traditional connection pooling,
        # but we can track our usage patterns
        return {
            'active_connections': 1,  # SQLite typically uses one connection
            'max_connections': 1,
            'connection_pool_size': 1
        }
    
    def _get_query_performance_stats(self) -> Dict[str, Any]:
        """Get query performance statistics from recent queries"""
        if not self.query_log:
            return {
                'total_queries': 0,
                'avg_duration_ms': 0,
                'slow_queries': 0,
                'fastest_query_ms': 0,
                'slowest_query_ms': 0
            }
        
        durations = [q['duration_ms'] for q in self.query_log]
        slow_queries = [q for q in self.query_log if q['is_slow']]
        
        return {
            'total_queries': len(self.query_log),
            'avg_duration_ms': sum(durations) / len(durations),
            'slow_queries': len(slow_queries),
            'slow_query_percentage': (len(slow_queries) / len(self.query_log)) * 100,
            'fastest_query_ms': min(durations),
            'slowest_query_ms': max(durations),
            'recent_slow_queries': slow_queries[-5:]  # Last 5 slow queries
        }
    
    def _get_database_settings(self) -> Dict[str, Any]:
        """Get current database settings"""
        settings = {}
        
        try:
            pragma_queries = [
                'cache_size', 'journal_mode', 'synchronous', 'temp_store',
                'page_size', 'auto_vacuum', 'foreign_keys'
            ]
            
            for pragma in pragma_queries:
                result = self.db.execute_single(f"PRAGMA {pragma}")
                if result:
                    key = list(result.keys())[0]
                    settings[pragma] = result[key]
                    
        except Exception as e:
            self.logger.error(f"Failed to get database settings: {e}")
        
        return settings
    
    def _estimate_table_size(self, table_name: str) -> int:
        """Estimate table size in KB"""
        try:
            # This is a rough estimation
            count_result = self.db.execute_single(f"SELECT COUNT(*) as count FROM {table_name}")
            row_count = count_result['count'] if count_result else 0
            
            # Estimate average row size (rough approximation)
            avg_row_size = 100  # bytes
            return (row_count * avg_row_size) // 1024
            
        except:
            return 0
    
    def get_system_performance(self) -> Dict[str, Any]:
        """Get system-level performance metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Process-specific metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            
            return {
                'cpu': {
                    'usage_percent': cpu_percent,
                    'count': psutil.cpu_count(),
                    'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
                },
                'memory': {
                    'total_mb': memory.total // (1024 * 1024),
                    'available_mb': memory.available // (1024 * 1024),
                    'used_mb': memory.used // (1024 * 1024),
                    'usage_percent': memory.percent,
                    'process_memory_mb': process_memory.rss // (1024 * 1024)
                },
                'disk': {
                    'total_gb': disk.total // (1024 * 1024 * 1024),
                    'used_gb': disk.used // (1024 * 1024 * 1024),
                    'free_gb': disk.free // (1024 * 1024 * 1024),
                    'usage_percent': (disk.used / disk.total) * 100
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get system performance: {e}")
            return {'error': str(e)}
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except:
            return 0.0
    
    def check_performance_alerts(self) -> List[Dict[str, Any]]:
        """Check for performance issues and return alerts"""
        alerts = []
        
        try:
            # Check database performance
            db_stats = self.get_database_statistics()
            
            # Check database size
            if db_stats.get('database_size_mb', 0) > 1000:  # 1GB
                alerts.append({
                    'type': 'database_size',
                    'severity': 'warning',
                    'message': f"Database size is {db_stats['database_size_mb']:.1f}MB",
                    'recommendation': 'Consider archiving old data'
                })
            
            # Check slow queries
            query_stats = db_stats.get('query_performance', {})
            if query_stats.get('slow_query_percentage', 0) > 10:
                alerts.append({
                    'type': 'slow_queries',
                    'severity': 'warning',
                    'message': f"{query_stats['slow_query_percentage']:.1f}% of queries are slow",
                    'recommendation': 'Review query performance and add indexes'
                })
            
            # Check system performance
            sys_stats = self.get_system_performance()
            
            # Check memory usage
            memory_percent = sys_stats.get('memory', {}).get('usage_percent', 0)
            if memory_percent > self.thresholds['memory_usage_mb']:
                alerts.append({
                    'type': 'memory_usage',
                    'severity': 'warning',
                    'message': f"Memory usage is {memory_percent:.1f}%",
                    'recommendation': 'Monitor memory usage and consider optimization'
                })
            
            # Check CPU usage
            cpu_percent = sys_stats.get('cpu', {}).get('usage_percent', 0)
            if cpu_percent > self.thresholds['cpu_usage_percent']:
                alerts.append({
                    'type': 'cpu_usage',
                    'severity': 'warning',
                    'message': f"CPU usage is {cpu_percent:.1f}%",
                    'recommendation': 'Monitor CPU usage and optimize processing'
                })
            
        except Exception as e:
            self.logger.error(f"Failed to check performance alerts: {e}")
            alerts.append({
                'type': 'monitoring_error',
                'severity': 'error',
                'message': f"Performance monitoring failed: {e}",
                'recommendation': 'Check monitoring system'
            })
        
        return alerts
    
    def optimize_database_settings(self) -> Dict[str, Any]:
        """Optimize database settings for better performance"""
        optimizations = []
        
        try:
            # Set optimal cache size (negative value = KB)
            self.db.execute_query("PRAGMA cache_size = -64000")  # 64MB cache
            optimizations.append("Set cache size to 64MB")
            
            # Enable WAL mode for better concurrency
            self.db.execute_query("PRAGMA journal_mode = WAL")
            optimizations.append("Enabled WAL journal mode")
            
            # Set synchronous to NORMAL for better performance
            self.db.execute_query("PRAGMA synchronous = NORMAL")
            optimizations.append("Set synchronous mode to NORMAL")
            
            # Enable memory temp store
            self.db.execute_query("PRAGMA temp_store = MEMORY")
            optimizations.append("Enabled memory temp store")
            
            # Enable foreign keys
            self.db.execute_query("PRAGMA foreign_keys = ON")
            optimizations.append("Enabled foreign key constraints")
            
            self.logger.info(f"Applied {len(optimizations)} database optimizations")
            
            return {
                'success': True,
                'optimizations_applied': optimizations,
                'count': len(optimizations)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to optimize database settings: {e}")
            return {
                'success': False,
                'error': str(e),
                'optimizations_applied': optimizations
            }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        return {
            'timestamp': datetime.now().isoformat(),
            'database_statistics': self.get_database_statistics(),
            'system_performance': self.get_system_performance(),
            'performance_alerts': self.check_performance_alerts(),
            'query_log_summary': {
                'total_logged_queries': len(self.query_log),
                'log_size_limit': self.max_query_log_size,
                'slow_query_threshold_ms': self.slow_query_threshold * 1000
            },
            'thresholds': self.thresholds
        }
    
    def clear_query_log(self):
        """Clear the query performance log"""
        self.query_log.clear()
        self.logger.info("Query performance log cleared")
    
    def update_thresholds(self, new_thresholds: Dict[str, Any]):
        """Update performance monitoring thresholds"""
        self.thresholds.update(new_thresholds)
        self.logger.info(f"Updated performance thresholds: {new_thresholds}")
