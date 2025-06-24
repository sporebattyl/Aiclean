"""
Task Tracker - Handles stateful task management and completion detection
"""
import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass
from difflib import SequenceMatcher
from ..data import TaskRepository, Task, TaskStatus


@dataclass
class TaskComparison:
    """Result of comparing current tasks with existing tasks"""
    new_tasks: List[str]              # Tasks to create as new
    updated_tasks: List[int]          # Existing task IDs to update
    completed_tasks: List[int]        # Task IDs to auto-complete
    similarity_matches: Dict[str, int] # New task -> existing task ID mapping


@dataclass
class CompletionRule:
    """Rule for determining if a task should be auto-completed"""
    name: str
    condition: callable
    confidence: float
    description: str


class TaskTracker:
    """Manages stateful task tracking and completion detection"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.task_repo = TaskRepository()
        self.similarity_threshold = 0.75
        self.completion_rules = self._initialize_completion_rules()
    
    def _initialize_completion_rules(self) -> List[CompletionRule]:
        """Initialize the rules for auto-completing tasks"""
        return [
            CompletionRule(
                name="not_detected_multiple_cycles",
                condition=lambda task, current_tasks: (
                    task.detection_count >= 2 and
                    not any(self._calculate_similarity(task.description, ct) > 0.6 for ct in current_tasks)
                ),
                confidence=0.9,
                description="Task was consistently detected before but not found in current analysis"
            ),
            
            CompletionRule(
                name="high_confidence_original",
                condition=lambda task, current_tasks: (
                    task.confidence_score > 0.8 and
                    not any(self._calculate_similarity(task.description, ct) > 0.5 for ct in current_tasks)
                ),
                confidence=0.8,
                description="High-confidence task no longer detected"
            ),
            
            CompletionRule(
                name="long_standing_task",
                condition=lambda task, current_tasks: (
                    task.days_since_created() >= 7 and
                    not any(self._calculate_similarity(task.description, ct) > 0.4 for ct in current_tasks)
                ),
                confidence=0.7,
                description="Long-standing task no longer detected"
            )
        ]
    
    def process_analysis_results(self, zone_id: int, current_tasks: List[str], 
                               confidence_scores: List[float] = None) -> Dict[str, Any]:
        """
        Process new analysis results and update task states
        
        Returns:
            Dictionary with analysis results and statistics
        """
        try:
            self.logger.info(f"Processing analysis results for zone {zone_id}: {len(current_tasks)} tasks detected")
            
            # Get existing pending tasks for this zone
            existing_tasks = self.task_repo.get_pending_tasks(zone_id)
            
            # Compare current analysis with existing tasks
            comparison = self._compare_analysis_results(current_tasks, existing_tasks, confidence_scores)
            
            # Create new tasks
            new_task_ids = []
            for i, task_desc in enumerate(comparison.new_tasks):
                confidence = confidence_scores[i] if confidence_scores and i < len(confidence_scores) else 0.8
                task_id = self._create_new_task(zone_id, task_desc, confidence)
                if task_id:
                    new_task_ids.append(task_id)
            
            # Update existing tasks (increment detection count)
            updated_count = 0
            for task_id in comparison.updated_tasks:
                if self.task_repo.increment_detection_count(task_id):
                    updated_count += 1
            
            # Auto-complete tasks no longer detected
            completed_count = 0
            completed_tasks = []
            for task_id in comparison.completed_tasks:
                task = self.task_repo.get_by_id(task_id)
                if task:
                    should_complete, confidence, reason = self._should_auto_complete(task, current_tasks)
                    
                    if should_complete:
                        if self.task_repo.update_status(task_id, TaskStatus.AUTO_COMPLETED):
                            completed_count += 1
                            completed_tasks.append({
                                'id': task_id,
                                'description': task.description,
                                'confidence': confidence,
                                'reason': reason
                            })
                            self.logger.info(f"Auto-completed task {task_id}: {task.description} (confidence: {confidence:.2f})")
            
            result = {
                'zone_id': zone_id,
                'new_tasks_created': len(new_task_ids),
                'tasks_updated': updated_count,
                'tasks_auto_completed': completed_count,
                'total_current_tasks': len(current_tasks),
                'total_existing_tasks': len(existing_tasks),
                'new_task_ids': new_task_ids,
                'completed_tasks': completed_tasks,
                'similarity_matches': comparison.similarity_matches
            }
            
            self.logger.info(f"Analysis processing complete for zone {zone_id}: "
                           f"{len(new_task_ids)} new, {updated_count} updated, {completed_count} completed")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to process analysis results for zone {zone_id}: {e}")
            return {
                'zone_id': zone_id,
                'error': str(e),
                'new_tasks_created': 0,
                'tasks_updated': 0,
                'tasks_auto_completed': 0
            }
    
    def _compare_analysis_results(self, current_tasks: List[str], existing_tasks: List[Task], 
                                confidence_scores: List[float] = None) -> TaskComparison:
        """Compare current analysis results with existing pending tasks"""
        new_tasks = []
        updated_tasks = []
        similarity_matches = {}
        
        # For each current task, find the best match in existing tasks
        for i, current_task in enumerate(current_tasks):
            best_match = None
            best_similarity = 0.0
            
            for existing_task in existing_tasks:
                similarity = self._calculate_similarity(current_task, existing_task.description)
                if similarity > best_similarity and similarity >= self.similarity_threshold:
                    best_similarity = similarity
                    best_match = existing_task
            
            if best_match:
                # Found a match - update existing task
                updated_tasks.append(best_match.id)
                similarity_matches[current_task] = best_match.id
                self.logger.debug(f"Matched '{current_task}' with existing task {best_match.id} "
                                f"(similarity: {best_similarity:.2f})")
            else:
                # No match found - create new task
                new_tasks.append(current_task)
                self.logger.debug(f"New task detected: '{current_task}'")
        
        # Find existing tasks that weren't matched (candidates for completion)
        matched_task_ids = set(updated_tasks)
        completed_tasks = [task.id for task in existing_tasks if task.id not in matched_task_ids]
        
        return TaskComparison(
            new_tasks=new_tasks,
            updated_tasks=updated_tasks,
            completed_tasks=completed_tasks,
            similarity_matches=similarity_matches
        )
    
    def _calculate_similarity(self, task1: str, task2: str) -> float:
        """Calculate similarity ratio between two task descriptions"""
        # Use fuzzy string matching
        similarity = SequenceMatcher(None, task1.lower(), task2.lower()).ratio()
        
        # Boost similarity for keyword matches
        keywords1 = self._extract_keywords(task1)
        keywords2 = self._extract_keywords(task2)
        
        if keywords1 and keywords2:
            keyword_similarity = len(keywords1.intersection(keywords2)) / len(keywords1.union(keywords2))
            # Weighted combination: 70% fuzzy matching, 30% keyword matching
            similarity = 0.7 * similarity + 0.3 * keyword_similarity
        
        return similarity
    
    def _extract_keywords(self, task: str) -> set:
        """Extract meaningful keywords from task description"""
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from'}
        words = set(task.lower().split()) - stopwords
        return words
    
    def _should_auto_complete(self, task: Task, current_tasks: List[str]) -> Tuple[bool, float, str]:
        """Determine if a task should be auto-completed"""
        for rule in self.completion_rules:
            if rule.condition(task, current_tasks):
                return True, rule.confidence, rule.description
        
        return False, 0.0, "Task still appears to be present"
    
    def _create_new_task(self, zone_id: int, description: str, confidence: float = 0.8) -> Optional[int]:
        """Create a new task"""
        try:
            task = Task(
                zone_id=zone_id,
                description=description,
                status=TaskStatus.PENDING,
                confidence_score=confidence,
                priority=self._calculate_task_priority(description),
                estimated_duration=self._estimate_task_duration(description),
                detection_count=1,
                last_detected_at=datetime.now()
            )
            
            task_id = self.task_repo.create(task)
            self.logger.info(f"Created new task {task_id}: {description}")
            return task_id
            
        except Exception as e:
            self.logger.error(f"Failed to create task '{description}': {e}")
            return None
    
    def _calculate_task_priority(self, description: str) -> int:
        """Calculate task priority based on description"""
        high_priority_keywords = ['spill', 'broken', 'dirty', 'stain', 'mess', 'urgent']
        medium_priority_keywords = ['organize', 'clean', 'wipe', 'vacuum']
        
        desc_lower = description.lower()
        
        if any(keyword in desc_lower for keyword in high_priority_keywords):
            return 3  # High priority
        elif any(keyword in desc_lower for keyword in medium_priority_keywords):
            return 2  # Medium priority
        else:
            return 1  # Low priority
    
    def _estimate_task_duration(self, description: str) -> int:
        """Estimate task duration in minutes based on description"""
        quick_tasks = ['pick up', 'put away', 'close', 'turn off']
        medium_tasks = ['wipe', 'clean', 'organize', 'fold']
        long_tasks = ['vacuum', 'mop', 'deep clean', 'scrub']
        
        desc_lower = description.lower()
        
        if any(keyword in desc_lower for keyword in quick_tasks):
            return 2  # 2 minutes
        elif any(keyword in desc_lower for keyword in long_tasks):
            return 15  # 15 minutes
        elif any(keyword in desc_lower for keyword in medium_tasks):
            return 5  # 5 minutes
        else:
            return 3  # Default 3 minutes
    
    def get_zone_task_summary(self, zone_id: int) -> Dict[str, Any]:
        """Get a summary of tasks for a zone"""
        try:
            all_tasks = self.task_repo.get_by_zone(zone_id)
            pending_tasks = [t for t in all_tasks if t.status == TaskStatus.PENDING]
            completed_tasks = [t for t in all_tasks if t.status in [TaskStatus.COMPLETED, TaskStatus.AUTO_COMPLETED]]
            
            return {
                'zone_id': zone_id,
                'total_tasks': len(all_tasks),
                'pending_tasks': len(pending_tasks),
                'completed_tasks': len(completed_tasks),
                'completion_rate': len(completed_tasks) / len(all_tasks) * 100 if all_tasks else 0,
                'high_priority_pending': len([t for t in pending_tasks if t.priority == 3]),
                'oldest_pending_task': min(pending_tasks, key=lambda t: t.created_at).created_at if pending_tasks else None
            }
        except Exception as e:
            self.logger.error(f"Failed to get task summary for zone {zone_id}: {e}")
            return {'zone_id': zone_id, 'error': str(e)}
    
    def complete_task_manually(self, task_id: int, user_id: str = None) -> bool:
        """Manually complete a task"""
        try:
            success = self.task_repo.update_status(task_id, TaskStatus.COMPLETED, user_id)
            if success:
                self.logger.info(f"Task {task_id} manually completed by {user_id or 'system'}")
            return success
        except Exception as e:
            self.logger.error(f"Failed to complete task {task_id}: {e}")
            return False
    
    def ignore_task(self, task_id: int, user_id: str = None) -> bool:
        """Mark a task as ignored"""
        try:
            success = self.task_repo.update_status(task_id, TaskStatus.IGNORED, user_id)
            if success:
                self.logger.info(f"Task {task_id} ignored by {user_id or 'system'}")
            return success
        except Exception as e:
            self.logger.error(f"Failed to ignore task {task_id}: {e}")
            return False

    def adjust_similarity_threshold(self, zone_id: int, accuracy_feedback: Optional[float] = None):
        """Adjust similarity threshold based on historical accuracy"""
        if accuracy_feedback is not None:
            if accuracy_feedback > 0.9:
                self.similarity_threshold = max(0.6, self.similarity_threshold - 0.05)  # More aggressive
            elif accuracy_feedback < 0.7:
                self.similarity_threshold = min(0.9, self.similarity_threshold + 0.05)  # More conservative

            self.logger.info(f"Adjusted similarity threshold to {self.similarity_threshold:.2f} "
                           f"based on accuracy feedback: {accuracy_feedback:.2f}")
