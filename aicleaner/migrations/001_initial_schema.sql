-- Roo AI Cleaning Assistant v2.0 - Initial Database Schema
-- Migration 001: Create initial tables for multi-zone architecture

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Zones table: Core configuration for each monitored area
CREATE TABLE zones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    camera_entity_id TEXT NOT NULL,
    todo_list_entity_id TEXT,
    sensor_entity_id TEXT,
    enabled BOOLEAN DEFAULT 1,
    notification_enabled BOOLEAN DEFAULT 1,
    personality_mode TEXT DEFAULT 'concise' CHECK (personality_mode IN ('concise', 'snarky', 'encouraging')),
    update_frequency INTEGER DEFAULT 60, -- minutes
    cleanliness_threshold INTEGER DEFAULT 70, -- below this triggers notifications
    max_tasks_per_analysis INTEGER DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tasks table: Individual cleaning tasks for each zone
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zone_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'auto_completed', 'ignored', 'cancelled')),
    confidence_score REAL DEFAULT 0.0, -- AI confidence in task detection (0.0-1.0)
    priority INTEGER DEFAULT 1, -- 1=low, 2=medium, 3=high
    estimated_duration INTEGER, -- estimated minutes to complete
    detection_count INTEGER DEFAULT 1, -- how many times this task was detected
    last_detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    auto_completed_at TIMESTAMP,
    user_id TEXT, -- who completed the task (if manually completed)
    completion_method TEXT DEFAULT 'pending' CHECK (completion_method IN ('pending', 'manual', 'auto', 'ignored')),
    FOREIGN KEY (zone_id) REFERENCES zones (id) ON DELETE CASCADE
);

-- Task history: Record of all AI analyses performed
CREATE TABLE task_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zone_id INTEGER NOT NULL,
    analysis_id TEXT NOT NULL UNIQUE, -- UUID for this analysis session
    cleanliness_score INTEGER NOT NULL CHECK (cleanliness_score >= 0 AND cleanliness_score <= 100),
    image_path TEXT, -- path to analyzed image (optional, for debugging)
    image_hash TEXT, -- hash of image for duplicate detection
    tasks_detected INTEGER DEFAULT 0,
    tasks_completed INTEGER DEFAULT 0,
    tasks_auto_completed INTEGER DEFAULT 0,
    analysis_duration REAL DEFAULT 0.0, -- seconds taken for AI analysis
    gemini_tokens_used INTEGER DEFAULT 0, -- for cost tracking
    error_message TEXT, -- if analysis failed
    weather_condition TEXT, -- external factors that might affect cleanliness
    day_of_week INTEGER, -- 0=Sunday, 6=Saturday for pattern analysis
    hour_of_day INTEGER, -- 0-23 for pattern analysis
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (zone_id) REFERENCES zones (id) ON DELETE CASCADE
);

-- Ignore rules: User-defined rules for what the AI should ignore
CREATE TABLE ignore_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zone_id INTEGER NOT NULL,
    rule_type TEXT NOT NULL CHECK (rule_type IN ('object', 'area', 'keyword', 'pattern')),
    rule_value TEXT NOT NULL, -- the actual rule (e.g., "decorative basket", "shoes by door")
    rule_description TEXT, -- human-readable description of what this rule does
    enabled BOOLEAN DEFAULT 1,
    case_sensitive BOOLEAN DEFAULT 0,
    match_partial BOOLEAN DEFAULT 1, -- whether to match partial strings
    priority INTEGER DEFAULT 1, -- higher priority rules are applied first
    usage_count INTEGER DEFAULT 0, -- how many times this rule has been applied
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT, -- user who created the rule
    FOREIGN KEY (zone_id) REFERENCES zones (id) ON DELETE CASCADE
);

-- Performance metrics: Daily aggregated statistics per zone
CREATE TABLE performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zone_id INTEGER NOT NULL,
    metric_date DATE NOT NULL,
    analyses_performed INTEGER DEFAULT 0,
    tasks_created INTEGER DEFAULT 0,
    tasks_completed INTEGER DEFAULT 0,
    tasks_auto_completed INTEGER DEFAULT 0,
    tasks_ignored INTEGER DEFAULT 0,
    avg_cleanliness_score REAL DEFAULT 0.0,
    min_cleanliness_score INTEGER DEFAULT 100,
    max_cleanliness_score INTEGER DEFAULT 0,
    completion_rate REAL DEFAULT 0.0, -- percentage of tasks completed
    auto_completion_rate REAL DEFAULT 0.0, -- percentage auto-completed
    avg_analysis_duration REAL DEFAULT 0.0,
    total_gemini_tokens INTEGER DEFAULT 0,
    streak_days INTEGER DEFAULT 0, -- consecutive days above threshold
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (zone_id) REFERENCES zones (id) ON DELETE CASCADE,
    UNIQUE(zone_id, metric_date)
);

-- Notifications log: Track all notifications sent
CREATE TABLE notifications_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zone_id INTEGER NOT NULL,
    notification_type TEXT NOT NULL CHECK (notification_type IN ('task_reminder', 'completion_celebration', 'streak_milestone', 'analysis_error')),
    personality_mode TEXT NOT NULL,
    message TEXT NOT NULL,
    recipient TEXT, -- Home Assistant service/entity that received notification
    delivery_status TEXT DEFAULT 'pending' CHECK (delivery_status IN ('pending', 'sent', 'failed', 'acknowledged')),
    error_message TEXT,
    metadata TEXT, -- JSON string for additional data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP,
    acknowledged_at TIMESTAMP,
    FOREIGN KEY (zone_id) REFERENCES zones (id) ON DELETE CASCADE
);

-- User preferences: Store user-specific settings
CREATE TABLE user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL UNIQUE, -- Home Assistant user ID
    default_personality TEXT DEFAULT 'concise',
    notification_frequency TEXT DEFAULT 'normal' CHECK (notification_frequency IN ('minimal', 'normal', 'frequent')),
    preferred_notification_time TEXT, -- HH:MM format
    weekend_mode BOOLEAN DEFAULT 0, -- different behavior on weekends
    vacation_mode BOOLEAN DEFAULT 0, -- pause notifications during vacation
    theme_preference TEXT DEFAULT 'auto' CHECK (theme_preference IN ('light', 'dark', 'auto')),
    language TEXT DEFAULT 'en',
    timezone TEXT DEFAULT 'UTC',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_tasks_zone_status ON tasks(zone_id, status);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);
CREATE INDEX idx_task_history_zone_date ON task_history(zone_id, created_at);
CREATE INDEX idx_task_history_analysis_id ON task_history(analysis_id);
CREATE INDEX idx_ignore_rules_zone_enabled ON ignore_rules(zone_id, enabled);
CREATE INDEX idx_performance_metrics_zone_date ON performance_metrics(zone_id, metric_date);
CREATE INDEX idx_notifications_zone_type ON notifications_log(zone_id, notification_type);

-- Create triggers for automatic timestamp updates
CREATE TRIGGER update_zones_timestamp 
    AFTER UPDATE ON zones
    BEGIN
        UPDATE zones SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER update_performance_metrics_timestamp 
    AFTER UPDATE ON performance_metrics
    BEGIN
        UPDATE performance_metrics SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER update_user_preferences_timestamp 
    AFTER UPDATE ON user_preferences
    BEGIN
        UPDATE user_preferences SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- Insert default zone for migration from v1.0
INSERT INTO zones (name, display_name, camera_entity_id, sensor_entity_id, todo_list_entity_id) 
VALUES ('default', 'Default Room', 'camera.default', 'sensor.aicleaner_cleanliness_score', 'todo.default')
ON CONFLICT(name) DO NOTHING;

-- Insert default user preferences
INSERT INTO user_preferences (user_id, default_personality) 
VALUES ('system', 'concise')
ON CONFLICT(user_id) DO NOTHING;
