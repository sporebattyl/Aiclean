"""
Analytics Data Collector - Automated metrics aggregation and collection
"""
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import asdict

try:
    from ..data import (
        TaskHistoryRepository, PerformanceMetricsRepository,
        TaskHistory, PerformanceMetrics, DatabaseManager
    )
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from data import (
        TaskHistoryRepository, PerformanceMetricsRepository,
        TaskHistory, PerformanceMetrics, DatabaseManager
    )


class AnalyticsCollector:
    """Collects and aggregates analytics data from various sources"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.logger = logging.getLogger(__name__)
        self.db = db_manager
        self.history_repo = TaskHistoryRepository(db_manager)
        self.metrics_repo = PerformanceMetricsRepository(db_manager)
        
        self.logger.info("Analytics collector initialized")
    
    def collect_daily_metrics(self, zone_id: int, target_date: Optional[date] = None) -> bool:
        """
        Collect and aggregate daily metrics for a specific zone
        
        Args:
            zone_id: Zone to collect metrics for
            target_date: Date to collect metrics for (defaults to yesterday)
            
        Returns:
            True if metrics were successfully collected and stored
        """
        if target_date is None:
            target_date = date.today() - timedelta(days=1)
        
        try:
            self.logger.info(f"Collecting daily metrics for zone {zone_id} on {target_date}")
            
            # Get all task history for the target date
            history_records = self._get_daily_history(zone_id, target_date)
            
            if not history_records:
                self.logger.info(f"No history records found for zone {zone_id} on {target_date}")
                return True  # Not an error, just no data
            
            # Calculate aggregated metrics
            metrics = self._calculate_daily_metrics(zone_id, target_date, history_records)
            
            # Calculate streak days
            metrics.streak_days = self._calculate_streak_days(zone_id, target_date)
            
            # Store metrics in database
            success = self.metrics_repo.upsert_daily_metrics(metrics)
            
            if success:
                self.logger.info(f"Successfully stored daily metrics for zone {zone_id}")
            else:
                self.logger.error(f"Failed to store daily metrics for zone {zone_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error collecting daily metrics for zone {zone_id}: {e}")
            return False
    
    def collect_all_zones_metrics(self, target_date: Optional[date] = None) -> Dict[int, bool]:
        """
        Collect daily metrics for all zones
        
        Args:
            target_date: Date to collect metrics for (defaults to yesterday)
            
        Returns:
            Dictionary mapping zone_id to success status
        """
        if target_date is None:
            target_date = date.today() - timedelta(days=1)
        
        results = {}
        
        try:
            # Get all unique zone IDs from task history
            zone_ids = self._get_active_zone_ids(target_date)
            
            for zone_id in zone_ids:
                results[zone_id] = self.collect_daily_metrics(zone_id, target_date)
            
            self.logger.info(f"Collected metrics for {len(zone_ids)} zones on {target_date}")
            
        except Exception as e:
            self.logger.error(f"Error collecting metrics for all zones: {e}")
        
        return results
    
    def backfill_metrics(self, zone_id: int, start_date: date, end_date: date) -> int:
        """
        Backfill metrics for a date range
        
        Args:
            zone_id: Zone to backfill metrics for
            start_date: Start date for backfill
            end_date: End date for backfill
            
        Returns:
            Number of days successfully backfilled
        """
        successful_days = 0
        current_date = start_date
        
        while current_date <= end_date:
            if self.collect_daily_metrics(zone_id, current_date):
                successful_days += 1
            current_date += timedelta(days=1)
        
        self.logger.info(f"Backfilled {successful_days} days of metrics for zone {zone_id}")
        return successful_days
    
    def _get_daily_history(self, zone_id: int, target_date: date) -> List[TaskHistory]:
        """Get all task history records for a specific zone and date"""
        query = """
            SELECT * FROM task_history 
            WHERE zone_id = ? AND DATE(created_at) = ?
            ORDER BY created_at
        """
        rows = self.db.execute_query(query, (zone_id, target_date.isoformat()))
        return [self.history_repo._row_to_history(row) for row in rows]
    
    def _calculate_daily_metrics(self, zone_id: int, target_date: date, 
                                history_records: List[TaskHistory]) -> PerformanceMetrics:
        """Calculate aggregated metrics from history records"""
        
        # Basic counts
        analyses_performed = len(history_records)
        total_tasks_created = sum(h.tasks_detected for h in history_records)
        total_tasks_completed = sum(h.tasks_completed for h in history_records)
        total_tasks_auto_completed = sum(h.tasks_auto_completed for h in history_records)
        
        # Calculate ignored tasks (detected but not completed)
        total_tasks_ignored = total_tasks_created - total_tasks_completed
        
        # Cleanliness scores
        scores = [h.cleanliness_score for h in history_records if h.cleanliness_score > 0]
        avg_cleanliness_score = sum(scores) / len(scores) if scores else 0.0
        min_cleanliness_score = min(scores) if scores else 100
        max_cleanliness_score = max(scores) if scores else 0
        
        # Rates
        completion_rate = (total_tasks_completed / total_tasks_created * 100) if total_tasks_created > 0 else 0.0
        auto_completion_rate = (total_tasks_auto_completed / total_tasks_completed * 100) if total_tasks_completed > 0 else 0.0
        
        # Performance metrics
        durations = [h.analysis_duration for h in history_records if h.analysis_duration > 0]
        avg_analysis_duration = sum(durations) / len(durations) if durations else 0.0
        total_gemini_tokens = sum(h.gemini_tokens_used for h in history_records)
        
        return PerformanceMetrics(
            zone_id=zone_id,
            metric_date=target_date.isoformat(),
            analyses_performed=analyses_performed,
            tasks_created=total_tasks_created,
            tasks_completed=total_tasks_completed,
            tasks_auto_completed=total_tasks_auto_completed,
            tasks_ignored=total_tasks_ignored,
            avg_cleanliness_score=avg_cleanliness_score,
            min_cleanliness_score=min_cleanliness_score,
            max_cleanliness_score=max_cleanliness_score,
            completion_rate=completion_rate,
            auto_completion_rate=auto_completion_rate,
            avg_analysis_duration=avg_analysis_duration,
            total_gemini_tokens=total_gemini_tokens,
            streak_days=0,  # Will be calculated separately
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def _calculate_streak_days(self, zone_id: int, target_date: date) -> int:
        """Calculate consecutive days with good cleanliness scores"""
        streak = 0
        current_date = target_date
        
        # Look back up to 365 days for streak calculation
        for _ in range(365):
            metrics = self.metrics_repo.get_metrics_by_date(zone_id, current_date.isoformat())
            
            if metrics and metrics.avg_cleanliness_score >= 80:  # Good cleanliness threshold
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break
        
        return streak
    
    def _get_active_zone_ids(self, target_date: date) -> List[int]:
        """Get all zone IDs that had activity on the target date"""
        query = """
            SELECT DISTINCT zone_id FROM task_history 
            WHERE DATE(created_at) = ?
        """
        rows = self.db.execute_query(query, (target_date.isoformat(),))
        return [row[0] for row in rows]
    
    def get_collection_status(self) -> Dict[str, Any]:
        """Get status information about metrics collection"""
        try:
            # Get latest collection dates per zone
            query = """
                SELECT zone_id, MAX(metric_date) as latest_date, COUNT(*) as total_days
                FROM performance_metrics 
                GROUP BY zone_id
            """
            rows = self.db.execute_query(query)
            
            zone_status = {}
            for row in rows:
                zone_status[row[0]] = {
                    'latest_date': row[1],
                    'total_days': row[2],
                    'days_behind': (date.today() - date.fromisoformat(row[1])).days - 1
                }
            
            return {
                'zones_tracked': len(zone_status),
                'zone_status': zone_status,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting collection status: {e}")
            return {'error': str(e)}
