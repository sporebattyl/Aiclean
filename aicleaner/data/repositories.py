"""
Repository layer for data access in Roo AI Cleaning Assistant v2.0
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from .database import get_database
from .models import Zone, Task, TaskHistory, IgnoreRule, PerformanceMetrics, TaskStatus, PersonalityMode, RuleType


class BaseRepository:
    """Base repository with common functionality"""
    
    def __init__(self):
        self.db = get_database()
        self.logger = logging.getLogger(self.__class__.__name__)


class ZoneRepository(BaseRepository):
    """Repository for zone management"""
    
    def create(self, zone: Zone) -> int:
        """Create a new zone"""
        query = """
            INSERT INTO zones (name, display_name, camera_entity_id, todo_list_entity_id, 
                             sensor_entity_id, enabled, notification_enabled, personality_mode,
                             update_frequency, cleanliness_threshold, max_tasks_per_analysis)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            zone.name, zone.display_name, zone.camera_entity_id, zone.todo_list_entity_id,
            zone.sensor_entity_id, zone.enabled, zone.notification_enabled, 
            zone.personality_mode.value, zone.update_frequency, zone.cleanliness_threshold,
            zone.max_tasks_per_analysis
        )
        return self.db.execute_insert(query, params)
    
    def get_by_id(self, zone_id: int) -> Optional[Zone]:
        """Get zone by ID"""
        query = "SELECT * FROM zones WHERE id = ?"
        row = self.db.execute_single(query, (zone_id,))
        return self._row_to_zone(row) if row else None
    
    def get_by_name(self, name: str) -> Optional[Zone]:
        """Get zone by name"""
        query = "SELECT * FROM zones WHERE name = ?"
        row = self.db.execute_single(query, (name,))
        return self._row_to_zone(row) if row else None
    
    def get_all(self, enabled_only: bool = False) -> List[Zone]:
        """Get all zones"""
        query = "SELECT * FROM zones"
        if enabled_only:
            query += " WHERE enabled = 1"
        query += " ORDER BY name"
        
        rows = self.db.execute_query(query)
        return [self._row_to_zone(row) for row in rows]
    
    def update(self, zone: Zone) -> bool:
        """Update an existing zone"""
        query = """
            UPDATE zones SET display_name = ?, camera_entity_id = ?, todo_list_entity_id = ?,
                           sensor_entity_id = ?, enabled = ?, notification_enabled = ?,
                           personality_mode = ?, update_frequency = ?, cleanliness_threshold = ?,
                           max_tasks_per_analysis = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        params = (
            zone.display_name, zone.camera_entity_id, zone.todo_list_entity_id,
            zone.sensor_entity_id, zone.enabled, zone.notification_enabled,
            zone.personality_mode.value, zone.update_frequency, zone.cleanliness_threshold,
            zone.max_tasks_per_analysis, zone.id
        )
        return self.db.execute_update(query, params) > 0
    
    def delete(self, zone_id: int) -> bool:
        """Delete a zone (cascades to related data)"""
        query = "DELETE FROM zones WHERE id = ?"
        return self.db.execute_update(query, (zone_id,)) > 0
    
    def _row_to_zone(self, row) -> Zone:
        """Convert database row to Zone object"""
        return Zone(
            id=row['id'],
            name=row['name'],
            display_name=row['display_name'],
            camera_entity_id=row['camera_entity_id'],
            todo_list_entity_id=row['todo_list_entity_id'],
            sensor_entity_id=row['sensor_entity_id'],
            enabled=bool(row['enabled']),
            notification_enabled=bool(row['notification_enabled']),
            personality_mode=PersonalityMode(row['personality_mode']),
            update_frequency=row['update_frequency'],
            cleanliness_threshold=row['cleanliness_threshold'],
            max_tasks_per_analysis=row['max_tasks_per_analysis'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )


class TaskRepository(BaseRepository):
    """Repository for task management"""
    
    def create(self, task: Task) -> int:
        """Create a new task"""
        query = """
            INSERT INTO tasks (zone_id, description, status, confidence_score, priority,
                             estimated_duration, detection_count, last_detected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            task.zone_id, task.description, task.status.value, task.confidence_score,
            task.priority, task.estimated_duration, task.detection_count,
            task.last_detected_at or datetime.now()
        )
        return self.db.execute_insert(query, params)
    
    def get_by_id(self, task_id: int) -> Optional[Task]:
        """Get task by ID"""
        query = "SELECT * FROM tasks WHERE id = ?"
        row = self.db.execute_single(query, (task_id,))
        return self._row_to_task(row) if row else None
    
    def get_by_zone(self, zone_id: int, status: Optional[TaskStatus] = None) -> List[Task]:
        """Get tasks for a specific zone"""
        query = "SELECT * FROM tasks WHERE zone_id = ?"
        params = (zone_id,)

        if status:
            query += " AND status = ?"
            params = (zone_id, status.value)

        query += " ORDER BY created_at DESC"
        rows = self.db.execute_query(query, params)
        return [self._row_to_task(row) for row in rows]
    
    def get_pending_tasks(self, zone_id: int) -> List[Task]:
        """Get all pending tasks for a zone"""
        return self.get_by_zone(zone_id, TaskStatus.PENDING)
    
    def update_status(self, task_id: int, status: TaskStatus, user_id: Optional[str] = None) -> bool:
        """Update task status"""
        completion_field = ""
        completion_value = None
        
        if status == TaskStatus.COMPLETED:
            completion_field = ", completed_at = ?, completion_method = 'manual'"
            completion_value = datetime.now()
        elif status == TaskStatus.AUTO_COMPLETED:
            completion_field = ", auto_completed_at = ?, completion_method = 'auto'"
            completion_value = datetime.now()
        
        query = f"""
            UPDATE tasks SET status = ?, user_id = ?{completion_field}
            WHERE id = ?
        """
        
        params = [status.value, user_id]
        if completion_value:
            params.append(completion_value)
        params.append(task_id)
        
        return self.db.execute_update(query, tuple(params)) > 0
    
    def find_similar_tasks(self, zone_id: int, description: str) -> List[Task]:
        """Find tasks with similar descriptions (simple text matching for now)"""
        query = """
            SELECT * FROM tasks 
            WHERE zone_id = ? AND status = 'pending'
            AND (description LIKE ? OR ? LIKE '%' || description || '%')
        """
        like_pattern = f"%{description}%"
        rows = self.db.execute_query(query, (zone_id, like_pattern, description))
        return [self._row_to_task(row) for row in rows]
    
    def increment_detection_count(self, task_id: int) -> bool:
        """Increment detection count for a task"""
        query = """
            UPDATE tasks SET detection_count = detection_count + 1, 
                           last_detected_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        return self.db.execute_update(query, (task_id,)) > 0
    
    def delete_old_completed_tasks(self, days: int = 30) -> int:
        """Delete completed tasks older than specified days"""
        query = """
            DELETE FROM tasks 
            WHERE status IN ('completed', 'auto_completed') 
            AND (completed_at < datetime('now', '-{} days') 
                 OR auto_completed_at < datetime('now', '-{} days'))
        """.format(days, days)
        return self.db.execute_update(query)
    
    def _row_to_task(self, row) -> Task:
        """Convert database row to Task object"""
        return Task(
            id=row['id'],
            zone_id=row['zone_id'],
            description=row['description'],
            status=TaskStatus(row['status']),
            confidence_score=row['confidence_score'],
            priority=row['priority'],
            estimated_duration=row['estimated_duration'],
            detection_count=row['detection_count'],
            last_detected_at=datetime.fromisoformat(row['last_detected_at']) if row['last_detected_at'] else None,
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
            auto_completed_at=datetime.fromisoformat(row['auto_completed_at']) if row['auto_completed_at'] else None,
            user_id=row['user_id'],
            completion_method=row['completion_method']
        )


class TaskHistoryRepository(BaseRepository):
    """Repository for task history management"""
    
    def create(self, history: TaskHistory) -> int:
        """Create a new task history record"""
        query = """
            INSERT INTO task_history (zone_id, analysis_id, cleanliness_score, image_path,
                                    image_hash, tasks_detected, tasks_completed, tasks_auto_completed,
                                    analysis_duration, gemini_tokens_used, error_message,
                                    weather_condition, day_of_week, hour_of_day)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        now = datetime.now()
        params = (
            history.zone_id, history.analysis_id, history.cleanliness_score, history.image_path,
            history.image_hash, history.tasks_detected, history.tasks_completed, 
            history.tasks_auto_completed, history.analysis_duration, history.gemini_tokens_used,
            history.error_message, history.weather_condition, now.weekday(), now.hour
        )
        return self.db.execute_insert(query, params)
    
    def get_recent_by_zone(self, zone_id: int, limit: int = 10) -> List[TaskHistory]:
        """Get recent history for a zone"""
        query = """
            SELECT * FROM task_history 
            WHERE zone_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        """
        rows = self.db.execute_query(query, (zone_id, limit))
        return [self._row_to_history(row) for row in rows]
    
    def get_latest_analysis(self, zone_id: int) -> Optional[TaskHistory]:
        """Get the most recent analysis for a zone"""
        recent = self.get_recent_by_zone(zone_id, 1)
        return recent[0] if recent else None
    
    def _row_to_history(self, row) -> TaskHistory:
        """Convert database row to TaskHistory object"""
        return TaskHistory(
            id=row['id'],
            zone_id=row['zone_id'],
            analysis_id=row['analysis_id'],
            cleanliness_score=row['cleanliness_score'],
            image_path=row['image_path'],
            image_hash=row['image_hash'],
            tasks_detected=row['tasks_detected'],
            tasks_completed=row['tasks_completed'],
            tasks_auto_completed=row['tasks_auto_completed'],
            analysis_duration=row['analysis_duration'],
            gemini_tokens_used=row['gemini_tokens_used'],
            error_message=row['error_message'],
            weather_condition=row['weather_condition'],
            day_of_week=row['day_of_week'],
            hour_of_day=row['hour_of_day'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        )


class IgnoreRuleRepository(BaseRepository):
    """Repository for ignore rule management"""

    def create(self, rule: IgnoreRule) -> int:
        """Create a new ignore rule"""
        query = """
            INSERT INTO ignore_rules (zone_id, rule_type, rule_value, rule_description,
                                    enabled, case_sensitive, match_partial, priority, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            rule.zone_id, rule.rule_type.value, rule.rule_value, rule.rule_description,
            rule.enabled, rule.case_sensitive, rule.match_partial, rule.priority, rule.created_by
        )
        return self.db.execute_insert(query, params)

    def get_by_zone(self, zone_id: int, enabled_only: bool = True) -> List[IgnoreRule]:
        """Get ignore rules for a zone"""
        query = "SELECT * FROM ignore_rules WHERE zone_id = ?"
        params = [zone_id]

        if enabled_only:
            query += " AND enabled = 1"

        query += " ORDER BY priority DESC, created_at"
        rows = self.db.execute_query(query, tuple(params))
        return [self._row_to_rule(row) for row in rows]

    def update_usage(self, rule_id: int) -> bool:
        """Update usage statistics for a rule"""
        query = """
            UPDATE ignore_rules
            SET usage_count = usage_count + 1, last_used_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        return self.db.execute_update(query, (rule_id,)) > 0

    def delete(self, rule_id: int) -> bool:
        """Delete an ignore rule"""
        query = "DELETE FROM ignore_rules WHERE id = ?"
        return self.db.execute_update(query, (rule_id,)) > 0

    def _row_to_rule(self, row) -> IgnoreRule:
        """Convert database row to IgnoreRule object"""
        return IgnoreRule(
            id=row['id'],
            zone_id=row['zone_id'],
            rule_type=RuleType(row['rule_type']),
            rule_value=row['rule_value'],
            rule_description=row['rule_description'],
            enabled=bool(row['enabled']),
            case_sensitive=bool(row['case_sensitive']),
            match_partial=bool(row['match_partial']),
            priority=row['priority'],
            usage_count=row['usage_count'],
            last_used_at=datetime.fromisoformat(row['last_used_at']) if row['last_used_at'] else None,
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            created_by=row['created_by']
        )


class PerformanceMetricsRepository(BaseRepository):
    """Repository for performance metrics management"""

    def upsert_daily_metrics(self, metrics: PerformanceMetrics) -> bool:
        """Insert or update daily metrics"""
        query = """
            INSERT INTO performance_metrics (
                zone_id, metric_date, analyses_performed, tasks_created, tasks_completed,
                tasks_auto_completed, tasks_ignored, avg_cleanliness_score, min_cleanliness_score,
                max_cleanliness_score, completion_rate, auto_completion_rate, avg_analysis_duration,
                total_gemini_tokens, streak_days
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(zone_id, metric_date) DO UPDATE SET
                analyses_performed = excluded.analyses_performed,
                tasks_created = excluded.tasks_created,
                tasks_completed = excluded.tasks_completed,
                tasks_auto_completed = excluded.tasks_auto_completed,
                tasks_ignored = excluded.tasks_ignored,
                avg_cleanliness_score = excluded.avg_cleanliness_score,
                min_cleanliness_score = excluded.min_cleanliness_score,
                max_cleanliness_score = excluded.max_cleanliness_score,
                completion_rate = excluded.completion_rate,
                auto_completion_rate = excluded.auto_completion_rate,
                avg_analysis_duration = excluded.avg_analysis_duration,
                total_gemini_tokens = excluded.total_gemini_tokens,
                streak_days = excluded.streak_days,
                updated_at = CURRENT_TIMESTAMP
        """
        params = (
            metrics.zone_id, metrics.metric_date, metrics.analyses_performed,
            metrics.tasks_created, metrics.tasks_completed, metrics.tasks_auto_completed,
            metrics.tasks_ignored, metrics.avg_cleanliness_score, metrics.min_cleanliness_score,
            metrics.max_cleanliness_score, metrics.completion_rate, metrics.auto_completion_rate,
            metrics.avg_analysis_duration, metrics.total_gemini_tokens, metrics.streak_days
        )
        return self.db.execute_update(query, params) > 0

    def get_recent_metrics(self, zone_id: int, days: int = 30) -> List[PerformanceMetrics]:
        """Get recent performance metrics for a zone"""
        query = """
            SELECT * FROM performance_metrics
            WHERE zone_id = ? AND metric_date >= date('now', '-{} days')
            ORDER BY metric_date DESC
        """.format(days)
        rows = self.db.execute_query(query, (zone_id,))
        return [self._row_to_metrics(row) for row in rows]

    def get_metrics_summary(self, zone_id: int, days: int = 30) -> Dict[str, Any]:
        """Get aggregated metrics summary"""
        query = """
            SELECT
                COUNT(*) as total_days,
                AVG(avg_cleanliness_score) as avg_score,
                AVG(completion_rate) as avg_completion_rate,
                SUM(tasks_created) as total_tasks_created,
                SUM(tasks_completed) as total_tasks_completed,
                MAX(streak_days) as max_streak
            FROM performance_metrics
            WHERE zone_id = ? AND metric_date >= date('now', '-{} days')
        """.format(days)
        row = self.db.execute_single(query, (zone_id,))

        if row:
            return {
                'total_days': row['total_days'],
                'avg_cleanliness_score': round(row['avg_score'] or 0, 1),
                'avg_completion_rate': round(row['avg_completion_rate'] or 0, 1),
                'total_tasks_created': row['total_tasks_created'] or 0,
                'total_tasks_completed': row['total_tasks_completed'] or 0,
                'max_streak': row['max_streak'] or 0
            }
        return {}

    def _row_to_metrics(self, row) -> PerformanceMetrics:
        """Convert database row to PerformanceMetrics object"""
        return PerformanceMetrics(
            id=row['id'],
            zone_id=row['zone_id'],
            metric_date=row['metric_date'],
            analyses_performed=row['analyses_performed'],
            tasks_created=row['tasks_created'],
            tasks_completed=row['tasks_completed'],
            tasks_auto_completed=row['tasks_auto_completed'],
            tasks_ignored=row['tasks_ignored'],
            avg_cleanliness_score=row['avg_cleanliness_score'],
            min_cleanliness_score=row['min_cleanliness_score'],
            max_cleanliness_score=row['max_cleanliness_score'],
            completion_rate=row['completion_rate'],
            auto_completion_rate=row['auto_completion_rate'],
            avg_analysis_duration=row['avg_analysis_duration'],
            total_gemini_tokens=row['total_gemini_tokens'],
            streak_days=row['streak_days'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )
