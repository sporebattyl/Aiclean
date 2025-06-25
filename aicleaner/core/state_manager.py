"""
State Manager - Coordinates the overall system state and orchestrates analysis cycles
"""
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, date

from .zone_manager import ZoneManager
from .task_tracker import TaskTracker
from .ai_analyzer import AIAnalyzer
from ..data import (
    TaskHistoryRepository, PerformanceMetricsRepository,
    TaskHistory, PerformanceMetrics, Zone, get_database
)
from ..analytics import AnalyticsCollector


class StateManager:
    """Orchestrates the overall system state and analysis cycles"""
    
    def __init__(self, gemini_api_key: str):
        self.logger = logging.getLogger(__name__)

        # Initialize core components
        self.zone_manager = ZoneManager()
        self.task_tracker = TaskTracker()
        self.ai_analyzer = AIAnalyzer(gemini_api_key)

        # Initialize repositories
        self.history_repo = TaskHistoryRepository()
        self.metrics_repo = PerformanceMetricsRepository()

        # Initialize analytics
        self.analytics_collector = AnalyticsCollector(get_database())

        self.logger.info("State Manager initialized successfully")
    
    def run_analysis_cycle(self, zone_id: int = None) -> Dict[str, Any]:
        """
        Run a complete analysis cycle for one or all zones
        
        Args:
            zone_id: Specific zone to analyze, or None for all enabled zones
            
        Returns:
            Dictionary with analysis results and statistics
        """
        if zone_id:
            zones = [self.zone_manager.get_zone(zone_id)]
            zones = [z for z in zones if z is not None]
        else:
            zones = self.zone_manager.get_enabled_zones()
        
        if not zones:
            self.logger.warning("No zones available for analysis")
            return {
                'success': False,
                'error': 'No zones available for analysis',
                'zones_analyzed': 0
            }
        
        results = {
            'success': True,
            'zones_analyzed': 0,
            'total_zones': len(zones),
            'zone_results': {},
            'overall_stats': {
                'total_new_tasks': 0,
                'total_completed_tasks': 0,
                'total_updated_tasks': 0,
                'average_cleanliness_score': 0
            }
        }
        
        total_score = 0
        successful_analyses = 0
        
        for zone in zones:
            try:
                self.logger.info(f"Starting analysis cycle for zone: {zone.name}")
                zone_result = self._analyze_zone(zone)
                
                results['zone_results'][zone.id] = zone_result
                
                if zone_result['success']:
                    results['zones_analyzed'] += 1
                    successful_analyses += 1
                    total_score += zone_result.get('cleanliness_score', 0)
                    
                    # Update overall stats
                    results['overall_stats']['total_new_tasks'] += zone_result.get('new_tasks_created', 0)
                    results['overall_stats']['total_completed_tasks'] += zone_result.get('tasks_auto_completed', 0)
                    results['overall_stats']['total_updated_tasks'] += zone_result.get('tasks_updated', 0)
                
            except Exception as e:
                self.logger.error(f"Failed to analyze zone {zone.name}: {e}")
                results['zone_results'][zone.id] = {
                    'success': False,
                    'error': str(e),
                    'zone_name': zone.name
                }
        
        # Calculate average cleanliness score
        if successful_analyses > 0:
            results['overall_stats']['average_cleanliness_score'] = total_score / successful_analyses
        
        # Update daily metrics for all analyzed zones
        self._update_daily_metrics(results)
        
        self.logger.info(f"Analysis cycle complete: {results['zones_analyzed']}/{results['total_zones']} zones analyzed")
        return results
    
    def _analyze_zone(self, zone: Zone) -> Dict[str, Any]:
        """Analyze a single zone"""
        analysis_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            # Perform AI analysis
            ai_result = self.ai_analyzer.analyze_zone_image(zone)
            
            if ai_result.error_message:
                return {
                    'success': False,
                    'error': ai_result.error_message,
                    'zone_name': zone.name,
                    'analysis_id': analysis_id
                }
            
            # Process tasks with stateful tracking
            task_result = self.task_tracker.process_analysis_results(
                zone.id, 
                ai_result.tasks, 
                ai_result.confidence_scores
            )
            
            # Record analysis history
            history = TaskHistory(
                zone_id=zone.id,
                analysis_id=analysis_id,
                cleanliness_score=ai_result.cleanliness_score,
                image_hash=ai_result.image_hash,
                tasks_detected=len(ai_result.tasks),
                tasks_completed=task_result.get('tasks_updated', 0),
                tasks_auto_completed=task_result.get('tasks_auto_completed', 0),
                analysis_duration=ai_result.analysis_duration,
                gemini_tokens_used=ai_result.tokens_used
            )
            
            self.history_repo.create(history)
            
            # Update Home Assistant entities
            self._update_home_assistant_entities(zone, ai_result, task_result)
            
            result = {
                'success': True,
                'zone_id': zone.id,
                'zone_name': zone.name,
                'analysis_id': analysis_id,
                'cleanliness_score': ai_result.cleanliness_score,
                'tasks_detected': len(ai_result.tasks),
                'new_tasks_created': task_result.get('new_tasks_created', 0),
                'tasks_updated': task_result.get('tasks_updated', 0),
                'tasks_auto_completed': task_result.get('tasks_auto_completed', 0),
                'analysis_duration': ai_result.analysis_duration,
                'tokens_used': ai_result.tokens_used,
                'completed_tasks': task_result.get('completed_tasks', [])
            }
            
            self.logger.info(f"Zone {zone.name} analysis complete: "
                           f"score={ai_result.cleanliness_score}, "
                           f"new_tasks={result['new_tasks_created']}, "
                           f"completed={result['tasks_auto_completed']}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to analyze zone {zone.name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'zone_name': zone.name,
                'analysis_id': analysis_id
            }
    
    def _update_home_assistant_entities(self, zone: Zone, ai_result, task_result):
        """Update Home Assistant sensors and todo lists"""
        try:
            # Update sensor if configured
            if zone.sensor_entity_id:
                self._update_ha_sensor(zone.sensor_entity_id, ai_result.cleanliness_score, zone.display_name)
            
            # Add new tasks to todo list if configured
            if zone.todo_list_entity_id and task_result.get('new_task_ids'):
                # Get the actual task descriptions for new tasks
                new_tasks = []
                for task_id in task_result['new_task_ids']:
                    task = self.task_tracker.task_repo.get_by_id(task_id)
                    if task:
                        new_tasks.append(task.description)
                
                if new_tasks:
                    self._update_ha_todolist(zone.todo_list_entity_id, new_tasks)
            
        except Exception as e:
            self.logger.error(f"Failed to update Home Assistant entities for zone {zone.name}: {e}")
    
    def _update_ha_sensor(self, sensor_entity_id: str, score: int, zone_name: str):
        """Update Home Assistant sensor"""
        try:
            import requests
            import os
            
            ha_url = os.environ.get('HA_URL', 'http://supervisor/core')
            ha_token = os.environ.get('SUPERVISOR_TOKEN')
            
            if not ha_token:
                self.logger.warning("No Home Assistant token available")
                return
            
            url = f"{ha_url}/api/states/{sensor_entity_id}"
            headers = {
                "Authorization": f"Bearer {ha_token}",
                "Content-Type": "application/json"
            }
            payload = {
                "state": score,
                "attributes": {
                    "unit_of_measurement": "%",
                    "friendly_name": f"{zone_name} Cleanliness Score",
                    "last_updated": datetime.now().isoformat()
                }
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            
            self.logger.info(f"Updated sensor {sensor_entity_id} with score: {score}")
            
        except Exception as e:
            self.logger.error(f"Failed to update HA sensor {sensor_entity_id}: {e}")
    
    def _update_ha_todolist(self, todo_entity_id: str, tasks: List[str]):
        """Update Home Assistant todo list"""
        try:
            import requests
            import os
            
            ha_url = os.environ.get('HA_URL', 'http://supervisor/core')
            ha_token = os.environ.get('SUPERVISOR_TOKEN')
            
            if not ha_token:
                self.logger.warning("No Home Assistant token available")
                return
            
            url = f"{ha_url}/api/services/todo/add_item"
            headers = {
                "Authorization": f"Bearer {ha_token}",
                "Content-Type": "application/json"
            }
            
            for task in tasks:
                payload = {
                    "entity_id": todo_entity_id,
                    "item": task
                }
                
                response = requests.post(url, headers=headers, json=payload, timeout=10)
                response.raise_for_status()
                
                self.logger.info(f"Added task to {todo_entity_id}: {task}")
                
        except Exception as e:
            self.logger.error(f"Failed to update HA todo list {todo_entity_id}: {e}")
    
    def _update_daily_metrics(self, analysis_results: Dict[str, Any]):
        """Update daily performance metrics for all zones"""
        today = date.today().isoformat()
        
        for zone_id, zone_result in analysis_results['zone_results'].items():
            if not zone_result.get('success'):
                continue
            
            try:
                # Get existing metrics for today or create new
                existing_metrics = self.metrics_repo.get_recent_metrics(zone_id, 1)
                today_metrics = None
                
                for metric in existing_metrics:
                    if metric.metric_date == today:
                        today_metrics = metric
                        break
                
                if not today_metrics:
                    today_metrics = PerformanceMetrics(
                        zone_id=zone_id,
                        metric_date=today
                    )
                
                # Update metrics
                today_metrics.analyses_performed += 1
                today_metrics.tasks_created += zone_result.get('new_tasks_created', 0)
                today_metrics.tasks_completed += zone_result.get('tasks_updated', 0)
                today_metrics.tasks_auto_completed += zone_result.get('tasks_auto_completed', 0)
                
                # Update cleanliness score statistics
                current_score = zone_result.get('cleanliness_score', 0)
                if today_metrics.analyses_performed == 1:
                    today_metrics.avg_cleanliness_score = current_score
                    today_metrics.min_cleanliness_score = current_score
                    today_metrics.max_cleanliness_score = current_score
                else:
                    # Update running average
                    total_score = today_metrics.avg_cleanliness_score * (today_metrics.analyses_performed - 1) + current_score
                    today_metrics.avg_cleanliness_score = total_score / today_metrics.analyses_performed
                    today_metrics.min_cleanliness_score = min(today_metrics.min_cleanliness_score, current_score)
                    today_metrics.max_cleanliness_score = max(today_metrics.max_cleanliness_score, current_score)
                
                # Calculate completion rate
                total_tasks = today_metrics.tasks_created + today_metrics.tasks_completed
                if total_tasks > 0:
                    today_metrics.completion_rate = (today_metrics.tasks_completed / total_tasks) * 100
                    today_metrics.auto_completion_rate = (today_metrics.tasks_auto_completed / total_tasks) * 100
                
                # Update analysis duration
                if zone_result.get('analysis_duration'):
                    if today_metrics.analyses_performed == 1:
                        today_metrics.avg_analysis_duration = zone_result['analysis_duration']
                    else:
                        total_duration = today_metrics.avg_analysis_duration * (today_metrics.analyses_performed - 1) + zone_result['analysis_duration']
                        today_metrics.avg_analysis_duration = total_duration / today_metrics.analyses_performed
                
                # Update token usage
                today_metrics.total_gemini_tokens += zone_result.get('tokens_used', 0)
                
                # Save metrics
                self.metrics_repo.upsert_daily_metrics(today_metrics)
                
            except Exception as e:
                self.logger.error(f"Failed to update daily metrics for zone {zone_id}: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        try:
            zones = self.zone_manager.get_all_zones()
            enabled_zones = [z for z in zones if z.enabled]
            
            # Get recent activity
            recent_analyses = []
            for zone in enabled_zones[:5]:  # Limit to 5 zones for status
                recent = self.history_repo.get_recent_by_zone(zone.id, 1)
                if recent:
                    recent_analyses.append({
                        'zone_id': zone.id,
                        'zone_name': zone.name,
                        'last_analysis': recent[0].created_at.isoformat() if recent[0].created_at else None,
                        'cleanliness_score': recent[0].cleanliness_score
                    })
            
            return {
                'total_zones': len(zones),
                'enabled_zones': len(enabled_zones),
                'recent_analyses': recent_analyses,
                'system_healthy': True
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get system status: {e}")
            return {
                'system_healthy': False,
                'error': str(e)
            }

    def trigger_analytics_collection(self, zone_id: Optional[int] = None,
                                   target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Trigger analytics collection for historical data processing

        Args:
            zone_id: Specific zone to collect for, or None for all zones
            target_date: Date to collect for, or None for yesterday

        Returns:
            Collection results
        """
        try:
            if zone_id:
                success = self.analytics_collector.collect_daily_metrics(zone_id, target_date)
                return {
                    'success': success,
                    'zone_id': zone_id,
                    'date': target_date.isoformat() if target_date else 'yesterday'
                }
            else:
                results = self.analytics_collector.collect_all_zones_metrics(target_date)
                return {
                    'results': results,
                    'total_zones': len(results),
                    'successful_zones': sum(1 for success in results.values() if success),
                    'date': target_date.isoformat() if target_date else 'yesterday'
                }

        except Exception as e:
            self.logger.error(f"Failed to trigger analytics collection: {e}")
            return {'error': str(e)}

    def get_analytics_status(self) -> Dict[str, Any]:
        """Get analytics collection status"""
        try:
            return self.analytics_collector.get_collection_status()
        except Exception as e:
            self.logger.error(f"Failed to get analytics status: {e}")
            return {'error': str(e)}
