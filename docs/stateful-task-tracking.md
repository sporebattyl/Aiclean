# Stateful Task Tracking Algorithm - Roo AI Cleaning Assistant v2.0

## Overview

The stateful task tracking system is the core innovation of v2.0, enabling the AI to remember previous analyses and automatically mark tasks as completed when they are no longer detected in subsequent images. This creates a closed-loop feedback system that provides users with accurate, real-time task completion tracking.

## Core Algorithm

### Task Comparison Process

```python
@dataclass
class TaskComparison:
    new_tasks: List[str]              # Tasks to create as new
    updated_tasks: List[int]          # Existing task IDs to update
    completed_tasks: List[int]        # Task IDs to auto-complete
    similarity_matches: Dict[str, int] # New task -> existing task ID mapping

def compare_analysis_results(
    current_tasks: List[str],
    existing_tasks: List[Task],
    similarity_threshold: float = 0.75
) -> TaskComparison:
    """
    Compare current AI analysis results with existing pending tasks
    
    Algorithm:
    1. For each current task, find best match in existing tasks
    2. If similarity > threshold, update existing task
    3. If no match found, mark as new task
    4. Mark unmatched existing tasks as candidates for completion
    5. Apply completion confidence rules
    """
```

### Similarity Matching Algorithm

#### Text Similarity Methods

1. **Fuzzy String Matching**
   ```python
   from difflib import SequenceMatcher
   
   def calculate_similarity(task1: str, task2: str) -> float:
       """Calculate similarity ratio between two task descriptions"""
       return SequenceMatcher(None, task1.lower(), task2.lower()).ratio()
   ```

2. **Keyword-Based Matching**
   ```python
   def extract_keywords(task: str) -> Set[str]:
       """Extract meaningful keywords from task description"""
       # Remove common words, extract nouns and verbs
       stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
       words = set(task.lower().split()) - stopwords
       return words
   
   def keyword_similarity(task1: str, task2: str) -> float:
       """Calculate similarity based on shared keywords"""
       keywords1 = extract_keywords(task1)
       keywords2 = extract_keywords(task2)
       
       if not keywords1 or not keywords2:
           return 0.0
       
       intersection = keywords1.intersection(keywords2)
       union = keywords1.union(keywords2)
       
       return len(intersection) / len(union)  # Jaccard similarity
   ```

3. **Semantic Similarity (Future Enhancement)**
   ```python
   # Using sentence transformers for semantic understanding
   def semantic_similarity(task1: str, task2: str) -> float:
       """Calculate semantic similarity using embeddings"""
       # Implementation would use sentence-transformers library
       # to generate embeddings and calculate cosine similarity
       pass
   ```

### Auto-Completion Logic

#### Completion Confidence Rules

```python
@dataclass
class CompletionRule:
    name: str
    condition: Callable[[Task, List[str]], bool]
    confidence: float
    description: str

COMPLETION_RULES = [
    CompletionRule(
        name="not_detected_multiple_cycles",
        condition=lambda task, current_tasks: (
            task.detection_count >= 2 and  # Was detected multiple times
            not any(calculate_similarity(task.description, ct) > 0.6 for ct in current_tasks)
        ),
        confidence=0.9,
        description="Task was consistently detected before but not found in current analysis"
    ),
    
    CompletionRule(
        name="high_confidence_original",
        condition=lambda task, current_tasks: (
            task.confidence_score > 0.8 and
            not any(calculate_similarity(task.description, ct) > 0.5 for ct in current_tasks)
        ),
        confidence=0.8,
        description="High-confidence task no longer detected"
    ),
    
    CompletionRule(
        name="long_standing_task",
        condition=lambda task, current_tasks: (
            task.days_since_created() >= 7 and
            not any(calculate_similarity(task.description, ct) > 0.4 for ct in current_tasks)
        ),
        confidence=0.7,
        description="Long-standing task no longer detected"
    )
]

def should_auto_complete(task: Task, current_tasks: List[str]) -> tuple[bool, float, str]:
    """
    Determine if a task should be auto-completed
    
    Returns:
    - should_complete: Boolean decision
    - confidence: Confidence score (0.0-1.0)
    - reason: Human-readable reason
    """
    for rule in COMPLETION_RULES:
        if rule.condition(task, current_tasks):
            return True, rule.confidence, rule.description
    
    return False, 0.0, "Task still appears to be present"
```

### State Transition Management

#### Task State Machine

```
┌─────────┐    AI Detection    ┌─────────┐
│ Not     │ ──────────────────→│ Pending │
│ Exists  │                    │         │
└─────────┘                    └─────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
            ┌──────────────┐ ┌─────────────┐ ┌──────────────┐
            │ Auto-        │ │ Manually    │ │ Ignored      │
            │ Completed    │ │ Completed   │ │              │
            └──────────────┘ └─────────────┘ └──────────────┘
```

#### State Transition Rules

```python
class TaskStateManager:
    def process_analysis_results(self, zone_id: int, current_tasks: List[str]) -> AnalysisResult:
        """
        Process new analysis results and update task states
        
        Steps:
        1. Get existing pending tasks for zone
        2. Compare with current analysis
        3. Update existing tasks or create new ones
        4. Auto-complete tasks no longer detected
        5. Update performance metrics
        """
        existing_tasks = self.task_repo.get_pending_tasks(zone_id)
        comparison = compare_analysis_results(current_tasks, existing_tasks)
        
        # Create new tasks
        for task_desc in comparison.new_tasks:
            self._create_new_task(zone_id, task_desc)
        
        # Update existing tasks
        for task_id in comparison.updated_tasks:
            self.task_repo.increment_detection_count(task_id)
        
        # Auto-complete tasks
        for task_id in comparison.completed_tasks:
            task = self.task_repo.get_by_id(task_id)
            should_complete, confidence, reason = should_auto_complete(task, current_tasks)
            
            if should_complete:
                self.task_repo.update_status(task_id, TaskStatus.AUTO_COMPLETED)
                self._log_auto_completion(task, confidence, reason)
        
        return AnalysisResult(
            new_tasks_created=len(comparison.new_tasks),
            tasks_updated=len(comparison.updated_tasks),
            tasks_auto_completed=len(comparison.completed_tasks)
        )
```

### Confidence Scoring System

#### Task Detection Confidence

```python
def calculate_task_confidence(
    task_description: str,
    image_analysis_confidence: float,
    detection_history: List[float],
    context_factors: Dict[str, Any]
) -> float:
    """
    Calculate overall confidence score for a task
    
    Factors:
    - AI model confidence in detection
    - Consistency across multiple detections
    - Task specificity (specific tasks are more reliable)
    - Environmental context (lighting, image quality)
    """
    base_confidence = image_analysis_confidence
    
    # Consistency bonus
    if len(detection_history) > 1:
        consistency = 1.0 - np.std(detection_history)
        base_confidence *= (0.7 + 0.3 * consistency)
    
    # Specificity bonus
    specificity = calculate_task_specificity(task_description)
    base_confidence *= (0.8 + 0.2 * specificity)
    
    # Environmental factors
    image_quality = context_factors.get('image_quality', 1.0)
    base_confidence *= image_quality
    
    return min(1.0, base_confidence)

def calculate_task_specificity(task_description: str) -> float:
    """
    Calculate how specific/actionable a task description is
    
    More specific tasks are more reliable:
    - "Pick up the red shirt from the floor" (high specificity)
    - "Clean up the mess" (low specificity)
    """
    specific_indicators = [
        'pick up', 'put away', 'wipe down', 'organize', 'fold',
        'vacuum', 'dust', 'clean', 'wash', 'sort'
    ]
    
    object_indicators = [
        'shirt', 'book', 'cup', 'plate', 'toy', 'shoe', 'pillow',
        'remote', 'magazine', 'bottle', 'bag', 'jacket'
    ]
    
    location_indicators = [
        'floor', 'table', 'counter', 'couch', 'bed', 'shelf',
        'chair', 'desk', 'nightstand'
    ]
    
    desc_lower = task_description.lower()
    
    specificity_score = 0.0
    if any(indicator in desc_lower for indicator in specific_indicators):
        specificity_score += 0.4
    if any(indicator in desc_lower for indicator in object_indicators):
        specificity_score += 0.3
    if any(indicator in desc_lower for indicator in location_indicators):
        specificity_score += 0.3
    
    return min(1.0, specificity_score)
```

### Historical Analysis Integration

#### Learning from Patterns

```python
class TaskPatternAnalyzer:
    def analyze_completion_patterns(self, zone_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Analyze historical task completion patterns to improve future predictions
        
        Returns insights like:
        - Which tasks are commonly auto-completed vs manually completed
        - Time patterns for task completion
        - False positive rates for auto-completion
        """
        history = self.history_repo.get_recent_by_zone(zone_id, days)
        
        patterns = {
            'auto_completion_accuracy': self._calculate_auto_completion_accuracy(history),
            'common_false_positives': self._identify_false_positives(history),
            'completion_time_patterns': self._analyze_completion_timing(history),
            'task_persistence_patterns': self._analyze_task_persistence(history)
        }
        
        return patterns
    
    def adjust_similarity_threshold(self, zone_id: int) -> float:
        """
        Dynamically adjust similarity threshold based on historical accuracy
        
        If auto-completion accuracy is low, increase threshold (be more conservative)
        If accuracy is high, can be more aggressive with auto-completion
        """
        patterns = self.analyze_completion_patterns(zone_id)
        accuracy = patterns['auto_completion_accuracy']
        
        base_threshold = 0.75
        
        if accuracy > 0.9:
            return base_threshold - 0.1  # More aggressive
        elif accuracy < 0.7:
            return base_threshold + 0.1  # More conservative
        else:
            return base_threshold
```

### Error Handling and Recovery

#### Handling Edge Cases

1. **False Auto-Completions**
   - User can "undo" auto-completions
   - System learns from user corrections
   - Adjusts confidence thresholds

2. **Duplicate Task Detection**
   - Prevent creating duplicate tasks
   - Merge similar tasks when appropriate
   - Handle variations in task descriptions

3. **Image Analysis Failures**
   - Graceful degradation when AI analysis fails
   - Don't auto-complete tasks during analysis failures
   - Maintain task state consistency

```python
class TaskTrackingErrorHandler:
    def handle_analysis_failure(self, zone_id: int, error: Exception):
        """Handle AI analysis failures gracefully"""
        self.logger.error(f"Analysis failed for zone {zone_id}: {error}")
        
        # Don't auto-complete any tasks during failures
        # Log the failure for debugging
        # Notify user if failures persist
        
        self.failure_tracker.record_failure(zone_id, error)
        
        if self.failure_tracker.should_notify_user(zone_id):
            self.notification_engine.send_error_notification(zone_id, error)
    
    def handle_false_auto_completion(self, task_id: int, user_feedback: str):
        """Learn from user corrections of auto-completions"""
        task = self.task_repo.get_by_id(task_id)
        
        # Revert the auto-completion
        self.task_repo.update_status(task_id, TaskStatus.PENDING)
        
        # Record the false positive for learning
        self.learning_system.record_false_positive(task, user_feedback)
        
        # Adjust confidence thresholds if needed
        self.adjust_zone_thresholds(task.zone_id)
```

## Implementation Timeline

1. **Phase 1**: Basic similarity matching and auto-completion
2. **Phase 2**: Confidence scoring and pattern analysis
3. **Phase 3**: Machine learning integration for improved accuracy
4. **Phase 4**: User feedback integration and self-improvement

This stateful task tracking system provides the foundation for intelligent, automated task management that learns and improves over time while maintaining user control and transparency.
