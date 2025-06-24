# Multi-Zone Data Model - Roo AI Cleaning Assistant v2.0

## Overview

The multi-zone architecture allows users to monitor and manage multiple rooms or areas independently. Each zone operates as a self-contained unit with its own configuration, tasks, and performance metrics while sharing common infrastructure.

## Zone Configuration Model

### Core Zone Properties

```python
@dataclass
class Zone:
    id: int                          # Unique identifier
    name: str                        # Internal name (slug-like, e.g., "living_room")
    display_name: str                # User-friendly name (e.g., "Living Room")
    camera_entity_id: str            # Home Assistant camera entity
    todo_list_entity_id: str         # Home Assistant todo list entity (optional)
    sensor_entity_id: str            # Home Assistant sensor entity (optional)
    enabled: bool                    # Whether zone is active
    notification_enabled: bool       # Whether to send notifications
    personality_mode: PersonalityMode # Notification personality
    update_frequency: int            # Analysis frequency in minutes
    cleanliness_threshold: int       # Score below which triggers notifications
    max_tasks_per_analysis: int      # Maximum tasks to generate per analysis
```

### Zone Management Principles

1. **Independence**: Each zone operates independently with its own:
   - Camera source
   - Task list
   - Notification settings
   - Ignore rules
   - Performance metrics

2. **Flexibility**: Zones can be:
   - Enabled/disabled individually
   - Configured with different update frequencies
   - Set with different cleanliness thresholds
   - Assigned different personality modes

3. **Scalability**: The system supports:
   - Unlimited number of zones
   - Dynamic zone creation/deletion
   - Zone configuration updates without restart

## Task Management Model

### Task Lifecycle

```
[AI Detection] → [Pending] → [Completed/Auto-Completed/Ignored]
                     ↓
              [Similarity Check] → [Merge with existing]
```

### Task States

- **Pending**: Newly detected task awaiting completion
- **Completed**: Manually marked as complete by user
- **Auto-Completed**: Automatically marked complete when no longer detected
- **Ignored**: User chose to ignore this task
- **Cancelled**: Task was cancelled (e.g., zone disabled)

### Task Comparison Algorithm

```python
def compare_tasks(current_tasks: List[str], previous_tasks: List[Task]) -> TaskComparison:
    """
    Compare current AI-detected tasks with existing pending tasks
    
    Returns:
    - new_tasks: Tasks to create
    - existing_tasks: Tasks to update (increment detection count)
    - completed_tasks: Tasks to auto-complete (no longer detected)
    """
```

## State Management Model

### Stateful Analysis Process

1. **Pre-Analysis State Check**
   - Retrieve current pending tasks for zone
   - Get latest analysis history
   - Load ignore rules

2. **AI Analysis**
   - Capture image from camera
   - Apply ignore rules to filter results
   - Generate cleanliness score and task list

3. **Post-Analysis State Update**
   - Compare new tasks with existing pending tasks
   - Auto-complete tasks no longer detected
   - Create new tasks or update existing ones
   - Update performance metrics

### State Persistence

- **Database**: SQLite for structured data
- **File System**: Images stored temporarily for analysis
- **Memory**: Active zone configurations cached
- **Home Assistant**: Sensor states synchronized

## Performance Analytics Model

### Daily Metrics Aggregation

```python
@dataclass
class PerformanceMetrics:
    zone_id: int
    metric_date: str                 # YYYY-MM-DD
    analyses_performed: int          # Number of AI analyses
    tasks_created: int               # New tasks detected
    tasks_completed: int             # Tasks manually completed
    tasks_auto_completed: int        # Tasks auto-completed
    avg_cleanliness_score: float     # Average score for the day
    completion_rate: float           # Percentage of tasks completed
    streak_days: int                 # Consecutive days above threshold
```

### Trend Analysis

- **Weekly Patterns**: Identify which days have more/fewer tasks
- **Time-of-Day Patterns**: Track when rooms get messy/clean
- **Seasonal Trends**: Long-term cleanliness patterns
- **Completion Efficiency**: How quickly tasks get completed

## Ignore Rules Model

### Rule Types

1. **Object Rules**: Ignore specific objects
   - Example: "decorative basket", "dog toys"
   
2. **Area Rules**: Ignore specific areas in the image
   - Example: "corner by the door", "under the coffee table"
   
3. **Keyword Rules**: Ignore tasks containing keywords
   - Example: "shoes" (if shoes by door are intentional)
   
4. **Pattern Rules**: Advanced regex-based rules
   - Example: ".*book.*table.*" (books on table are okay)

### Rule Application

```python
def apply_ignore_rules(tasks: List[str], rules: List[IgnoreRule]) -> List[str]:
    """
    Filter tasks through ignore rules
    
    Rules are applied in priority order (highest first)
    Returns filtered task list
    """
```

## Notification Model

### Notification Triggers

1. **Task Reminders**: When cleanliness score drops below threshold
2. **Completion Celebrations**: When all tasks completed
3. **Streak Milestones**: When achieving consecutive clean days
4. **Analysis Errors**: When AI analysis fails

### Personality Modes

#### Concise Mode
- Focus on facts and numbers
- Example: "Living Room: 3 tasks remaining (Score: 65/100)"

#### Snarky Mode
- Humorous, slightly sarcastic tone
- Example: "The living room couch is staging a rebellion with those clothes. 3 tasks are plotting against your relaxation time."

#### Encouraging Mode
- Positive, motivational tone
- Example: "You're doing amazing! Just 3 more small tasks and your living room will be perfect for relaxing!"

### Notification Delivery

- **Home Assistant Services**: notify.mobile_app_*, notify.persistent_notification
- **Custom Integrations**: Slack, Discord, email
- **Timing Controls**: Quiet hours, frequency limits
- **User Preferences**: Per-zone notification settings

## Configuration Management

### Zone Configuration Schema

```yaml
zones:
  living_room:
    display_name: "Living Room"
    camera_entity: "camera.living_room"
    todo_list_entity: "todo.living_room_cleaning"
    sensor_entity: "sensor.living_room_cleanliness"
    enabled: true
    notification_enabled: true
    personality_mode: "encouraging"
    update_frequency: 60  # minutes
    cleanliness_threshold: 70
    max_tasks_per_analysis: 8
    ignore_rules:
      - type: "object"
        value: "decorative basket"
        description: "Wicker basket with blankets is decorative"
      - type: "keyword"
        value: "remote"
        description: "TV remotes on coffee table are okay"
  
  kitchen:
    display_name: "Kitchen"
    camera_entity: "camera.kitchen"
    enabled: true
    personality_mode: "snarky"
    update_frequency: 30
    cleanliness_threshold: 80
```

### Migration from v1.0

```python
def migrate_v1_config(old_config: dict) -> List[Zone]:
    """
    Convert v1.0 single-zone configuration to v2.0 multi-zone
    
    Creates a "default" zone with existing settings
    """
    return [Zone(
        name="default",
        display_name="Default Room",
        camera_entity_id=old_config.get('camera_entity'),
        todo_list_entity_id=old_config.get('todo_list_entity'),
        sensor_entity_id=old_config.get('sensor_entity_id', 'sensor.aicleaner_cleanliness_score'),
        update_frequency=old_config.get('update_frequency', 60)
    )]
```

## API Design for Multi-Zone

### REST Endpoints

```
# Zone Management
GET    /api/zones                    # List all zones
POST   /api/zones                    # Create new zone
GET    /api/zones/{id}               # Get zone details
PUT    /api/zones/{id}               # Update zone
DELETE /api/zones/{id}               # Delete zone

# Zone Tasks
GET    /api/zones/{id}/tasks         # Get zone tasks
POST   /api/zones/{id}/tasks/{task_id}/complete  # Complete task
DELETE /api/zones/{id}/tasks/{task_id}           # Delete task

# Zone Analytics
GET    /api/zones/{id}/metrics       # Get performance metrics
GET    /api/zones/{id}/history       # Get analysis history
GET    /api/zones/{id}/trends        # Get trend analysis

# Zone Configuration
GET    /api/zones/{id}/ignore-rules  # Get ignore rules
POST   /api/zones/{id}/ignore-rules  # Add ignore rule
DELETE /api/ignore-rules/{rule_id}   # Delete ignore rule

# System-wide
GET    /api/dashboard                # Multi-zone dashboard data
POST   /api/analyze-all              # Trigger analysis for all zones
```

### WebSocket Events

```javascript
// Zone-specific events
zone.{zone_id}.task_created
zone.{zone_id}.task_completed
zone.{zone_id}.analysis_complete
zone.{zone_id}.metrics_updated

// System-wide events
system.zone_created
system.zone_deleted
system.analysis_started
system.analysis_complete
```

## Implementation Considerations

### Performance Optimization

1. **Concurrent Analysis**: Multiple zones can be analyzed simultaneously
2. **Caching**: Zone configurations cached in memory
3. **Database Indexing**: Proper indexes for zone-based queries
4. **Image Processing**: Efficient image handling and cleanup

### Error Handling

1. **Zone Isolation**: Errors in one zone don't affect others
2. **Graceful Degradation**: System continues working with partial failures
3. **Retry Logic**: Automatic retry for transient failures
4. **Error Notifications**: Alert users to persistent issues

### Security Considerations

1. **Zone Access Control**: Future support for user-based zone access
2. **API Authentication**: Secure API endpoints
3. **Data Privacy**: Secure handling of camera images
4. **Configuration Validation**: Prevent invalid configurations

This multi-zone data model provides the foundation for a scalable, flexible, and user-friendly home management system that can grow with user needs while maintaining simplicity and reliability.
