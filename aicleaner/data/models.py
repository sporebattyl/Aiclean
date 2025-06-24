"""
Data models for Roo AI Cleaning Assistant v2.0
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class TaskStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    AUTO_COMPLETED = "auto_completed"
    IGNORED = "ignored"
    CANCELLED = "cancelled"


class PersonalityMode(Enum):
    CONCISE = "concise"
    SNARKY = "snarky"
    ENCOURAGING = "encouraging"


class RuleType(Enum):
    OBJECT = "object"
    AREA = "area"
    KEYWORD = "keyword"
    PATTERN = "pattern"


class NotificationType(Enum):
    TASK_REMINDER = "task_reminder"
    COMPLETION_CELEBRATION = "completion_celebration"
    STREAK_MILESTONE = "streak_milestone"
    ANALYSIS_ERROR = "analysis_error"


@dataclass
class Zone:
    """Represents a monitored zone/room"""
    id: Optional[int] = None
    name: str = ""
    display_name: str = ""
    camera_entity_id: str = ""
    todo_list_entity_id: Optional[str] = None
    sensor_entity_id: Optional[str] = None
    enabled: bool = True
    notification_enabled: bool = True
    personality_mode: PersonalityMode = PersonalityMode.CONCISE
    update_frequency: int = 60  # minutes
    cleanliness_threshold: int = 70
    max_tasks_per_analysis: int = 10
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'camera_entity_id': self.camera_entity_id,
            'todo_list_entity_id': self.todo_list_entity_id,
            'sensor_entity_id': self.sensor_entity_id,
            'enabled': self.enabled,
            'notification_enabled': self.notification_enabled,
            'personality_mode': self.personality_mode.value,
            'update_frequency': self.update_frequency,
            'cleanliness_threshold': self.cleanliness_threshold,
            'max_tasks_per_analysis': self.max_tasks_per_analysis,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class Task:
    """Represents a cleaning task"""
    id: Optional[int] = None
    zone_id: int = 0
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    confidence_score: float = 0.0
    priority: int = 1
    estimated_duration: Optional[int] = None
    detection_count: int = 1
    last_detected_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    auto_completed_at: Optional[datetime] = None
    user_id: Optional[str] = None
    completion_method: str = "pending"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'zone_id': self.zone_id,
            'description': self.description,
            'status': self.status.value,
            'confidence_score': self.confidence_score,
            'priority': self.priority,
            'estimated_duration': self.estimated_duration,
            'detection_count': self.detection_count,
            'last_detected_at': self.last_detected_at.isoformat() if self.last_detected_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'auto_completed_at': self.auto_completed_at.isoformat() if self.auto_completed_at else None,
            'user_id': self.user_id,
            'completion_method': self.completion_method
        }

    def is_completed(self) -> bool:
        """Check if task is completed (manually or automatically)"""
        return self.status in [TaskStatus.COMPLETED, TaskStatus.AUTO_COMPLETED]

    def days_since_created(self) -> int:
        """Calculate days since task was created"""
        if not self.created_at:
            return 0
        return (datetime.now() - self.created_at).days


@dataclass
class TaskHistory:
    """Represents an AI analysis session"""
    id: Optional[int] = None
    zone_id: int = 0
    analysis_id: str = ""
    cleanliness_score: int = 0
    image_path: Optional[str] = None
    image_hash: Optional[str] = None
    tasks_detected: int = 0
    tasks_completed: int = 0
    tasks_auto_completed: int = 0
    analysis_duration: float = 0.0
    gemini_tokens_used: int = 0
    error_message: Optional[str] = None
    weather_condition: Optional[str] = None
    day_of_week: Optional[int] = None
    hour_of_day: Optional[int] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'zone_id': self.zone_id,
            'analysis_id': self.analysis_id,
            'cleanliness_score': self.cleanliness_score,
            'image_path': self.image_path,
            'image_hash': self.image_hash,
            'tasks_detected': self.tasks_detected,
            'tasks_completed': self.tasks_completed,
            'tasks_auto_completed': self.tasks_auto_completed,
            'analysis_duration': self.analysis_duration,
            'gemini_tokens_used': self.gemini_tokens_used,
            'error_message': self.error_message,
            'weather_condition': self.weather_condition,
            'day_of_week': self.day_of_week,
            'hour_of_day': self.hour_of_day,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class IgnoreRule:
    """Represents a rule for ignoring certain objects/areas"""
    id: Optional[int] = None
    zone_id: int = 0
    rule_type: RuleType = RuleType.OBJECT
    rule_value: str = ""
    rule_description: Optional[str] = None
    enabled: bool = True
    case_sensitive: bool = False
    match_partial: bool = True
    priority: int = 1
    usage_count: int = 0
    last_used_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'zone_id': self.zone_id,
            'rule_type': self.rule_type.value,
            'rule_value': self.rule_value,
            'rule_description': self.rule_description,
            'enabled': self.enabled,
            'case_sensitive': self.case_sensitive,
            'match_partial': self.match_partial,
            'priority': self.priority,
            'usage_count': self.usage_count,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by
        }

    def matches(self, text: str) -> bool:
        """Check if this rule matches the given text"""
        if not self.enabled:
            return False
        
        search_text = text if self.case_sensitive else text.lower()
        rule_text = self.rule_value if self.case_sensitive else self.rule_value.lower()
        
        if self.match_partial:
            return rule_text in search_text
        else:
            return rule_text == search_text


@dataclass
class PerformanceMetrics:
    """Daily performance metrics for a zone"""
    id: Optional[int] = None
    zone_id: int = 0
    metric_date: str = ""  # YYYY-MM-DD format
    analyses_performed: int = 0
    tasks_created: int = 0
    tasks_completed: int = 0
    tasks_auto_completed: int = 0
    tasks_ignored: int = 0
    avg_cleanliness_score: float = 0.0
    min_cleanliness_score: int = 100
    max_cleanliness_score: int = 0
    completion_rate: float = 0.0
    auto_completion_rate: float = 0.0
    avg_analysis_duration: float = 0.0
    total_gemini_tokens: int = 0
    streak_days: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'zone_id': self.zone_id,
            'metric_date': self.metric_date,
            'analyses_performed': self.analyses_performed,
            'tasks_created': self.tasks_created,
            'tasks_completed': self.tasks_completed,
            'tasks_auto_completed': self.tasks_auto_completed,
            'tasks_ignored': self.tasks_ignored,
            'avg_cleanliness_score': self.avg_cleanliness_score,
            'min_cleanliness_score': self.min_cleanliness_score,
            'max_cleanliness_score': self.max_cleanliness_score,
            'completion_rate': self.completion_rate,
            'auto_completion_rate': self.auto_completion_rate,
            'avg_analysis_duration': self.avg_analysis_duration,
            'total_gemini_tokens': self.total_gemini_tokens,
            'streak_days': self.streak_days,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class AIAnalysisResult:
    """Result from AI analysis of an image"""
    cleanliness_score: int
    tasks: List[str]
    confidence_scores: List[float] = field(default_factory=list)
    analysis_duration: float = 0.0
    tokens_used: int = 0
    error_message: Optional[str] = None
    image_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'cleanliness_score': self.cleanliness_score,
            'tasks': self.tasks,
            'confidence_scores': self.confidence_scores,
            'analysis_duration': self.analysis_duration,
            'tokens_used': self.tokens_used,
            'error_message': self.error_message,
            'image_hash': self.image_hash
        }
