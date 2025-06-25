"""
Notification Engine - Main notification delivery system
"""
import logging
import requests
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from ..data import Zone, NotificationType, PersonalityMode
from ..data.repositories import BaseRepository
from .personalities import PersonalityEngine
from .templates import TemplateManager


class NotificationEngine(BaseRepository):
    """Main notification engine for delivering personality-based notifications"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.personality_engine = PersonalityEngine()
        self.template_manager = TemplateManager()
        
        # Home Assistant configuration
        self.ha_url = os.environ.get('HA_URL', 'http://supervisor/core')
        self.ha_token = os.environ.get('SUPERVISOR_TOKEN')
        self.ha_headers = {
            "Authorization": f"Bearer {self.ha_token}",
            "Content-Type": "application/json"
        } if self.ha_token else {}
        
        # Notification settings
        self.default_settings = {
            'enabled': True,
            'frequency': 'normal',  # minimal, normal, frequent
            'quiet_hours': {
                'enabled': True,
                'start': '22:00',
                'end': '07:00'
            },
            'intervals': {
                'task_reminder': 60,      # minutes
                'completion_celebration': 0,  # immediate
                'streak_milestone': 0,    # immediate
                'analysis_error': 30      # minutes
            },
            'delivery_methods': ['persistent_notification', 'mobile_app']
        }
    
    def send_task_reminder(self, zone: Zone, task_count: int, score: int, 
                          tasks: List[str] = None) -> bool:
        """Send a task reminder notification"""
        try:
            if not zone.notification_enabled:
                self.logger.debug(f"Notifications disabled for zone {zone.name}")
                return False
            
            # Check if we should send based on frequency settings
            if not self._should_send_notification(zone.id, NotificationType.TASK_REMINDER):
                return False
            
            # Generate personality-based message
            message = self.personality_engine.generate_task_reminder(zone, task_count, score)
            
            # Format notification
            notification = self.template_manager.format_notification(
                NotificationType.TASK_REMINDER,
                message,
                zone.display_name,
                zone.personality_mode,
                {
                    'task_count': task_count,
                    'score': score,
                    'tasks': tasks or []
                }
            )
            
            # Send notification
            success = self._deliver_notification(notification)
            
            if success:
                self._log_notification(notification, zone.id)
                self.logger.info(f"Sent task reminder for {zone.name}: {task_count} tasks, score {score}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to send task reminder for zone {zone.name}: {e}")
            return False
    
    def send_completion_celebration(self, zone: Zone, score: int, 
                                  tasks_completed: int = 0) -> bool:
        """Send a completion celebration notification"""
        try:
            if not zone.notification_enabled:
                return False
            
            # Generate personality-based message
            message = self.personality_engine.generate_completion_celebration(zone, score)
            
            # Format notification
            notification = self.template_manager.format_notification(
                NotificationType.COMPLETION_CELEBRATION,
                message,
                zone.display_name,
                zone.personality_mode,
                {
                    'score': score,
                    'tasks_completed': tasks_completed
                }
            )
            
            # Send notification
            success = self._deliver_notification(notification)
            
            if success:
                self._log_notification(notification, zone.id)
                self.logger.info(f"Sent completion celebration for {zone.name}: score {score}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to send completion celebration for zone {zone.name}: {e}")
            return False
    
    def send_streak_milestone(self, zone: Zone, streak_days: int) -> bool:
        """Send a streak milestone notification"""
        try:
            if not zone.notification_enabled:
                return False
            
            # Only send for significant milestones
            if streak_days not in [3, 7, 14, 30, 60, 90, 365]:
                return False
            
            # Generate personality-based message
            message = self.personality_engine.generate_streak_milestone(zone, streak_days)
            
            # Format notification
            notification = self.template_manager.format_notification(
                NotificationType.STREAK_MILESTONE,
                message,
                zone.display_name,
                zone.personality_mode,
                {
                    'streak_days': streak_days
                }
            )
            
            # Send notification
            success = self._deliver_notification(notification)
            
            if success:
                self._log_notification(notification, zone.id)
                self.logger.info(f"Sent streak milestone for {zone.name}: {streak_days} days")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to send streak milestone for zone {zone.name}: {e}")
            return False
    
    def send_analysis_error(self, zone: Zone, error_message: str, 
                          retry_count: int = 0) -> bool:
        """Send an analysis error notification"""
        try:
            # Check if we should send based on frequency settings
            if not self._should_send_notification(zone.id, NotificationType.ANALYSIS_ERROR):
                return False
            
            # Generate personality-based message
            message = self.personality_engine.generate_analysis_error(zone, error_message)
            
            # Format notification
            notification = self.template_manager.format_notification(
                NotificationType.ANALYSIS_ERROR,
                message,
                zone.display_name,
                zone.personality_mode,
                {
                    'error_message': error_message,
                    'retry_count': retry_count,
                    'error_type': self._classify_error(error_message)
                }
            )
            
            # Send notification
            success = self._deliver_notification(notification)
            
            if success:
                self._log_notification(notification, zone.id)
                self.logger.info(f"Sent analysis error for {zone.name}: {error_message}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to send analysis error for zone {zone.name}: {e}")
            return False
    
    def send_auto_completion_notification(self, zone: Zone, completed_tasks: List[str]) -> bool:
        """Send notification about auto-completed tasks"""
        try:
            if not zone.notification_enabled or not completed_tasks:
                return False
            
            # Generate personality-based message
            message = self.personality_engine.generate_auto_completion(zone, len(completed_tasks), completed_tasks)
            
            # Format notification
            notification = self.template_manager.format_notification(
                NotificationType.COMPLETION_CELEBRATION,
                message,
                zone.display_name,
                zone.personality_mode,
                {
                    'task_count': len(completed_tasks),
                    'completed_tasks': completed_tasks,
                    'auto_completed': True
                }
            )
            
            # Send notification
            success = self._deliver_notification(notification)
            
            if success:
                self._log_notification(notification, zone.id)
                self.logger.info(f"Sent auto-completion notification for {zone.name}: {len(completed_tasks)} tasks")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to send auto-completion notification for zone {zone.name}: {e}")
            return False
    
    def send_summary_notification(self, zones_data: List[Dict[str, Any]], 
                                personality: PersonalityMode = PersonalityMode.CONCISE) -> bool:
        """Send a summary notification for multiple zones"""
        try:
            # Create summary notification
            notification = self.template_manager.create_summary_notification(zones_data, personality)
            
            if not notification:
                return False
            
            # Send notification
            success = self._deliver_notification(notification)
            
            if success:
                self._log_notification(notification, None)  # No specific zone
                self.logger.info(f"Sent summary notification for {len(zones_data)} zones")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to send summary notification: {e}")
            return False
    
    def _deliver_notification(self, notification: Dict[str, Any]) -> bool:
        """Deliver notification through configured methods"""
        success = False
        
        # Try persistent notification first
        if self._send_persistent_notification(notification):
            success = True
        
        # Try mobile app notification
        if self._send_mobile_notification(notification):
            success = True
        
        return success
    
    def _send_persistent_notification(self, notification: Dict[str, Any]) -> bool:
        """Send persistent notification to Home Assistant"""
        try:
            if not self.ha_token:
                self.logger.warning("No Home Assistant token available")
                return False
            
            url = f"{self.ha_url}/api/services/persistent_notification/create"
            payload = {
                "notification_id": notification['id'],
                "title": notification['title'],
                "message": notification['message']
            }
            
            response = requests.post(url, headers=self.ha_headers, json=payload, timeout=10)
            response.raise_for_status()
            
            self.logger.debug(f"Sent persistent notification: {notification['id']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send persistent notification: {e}")
            return False
    
    def _send_mobile_notification(self, notification: Dict[str, Any]) -> bool:
        """Send mobile app notification"""
        try:
            if not self.ha_token:
                return False
            
            # This would be configured based on user's mobile app setup
            # For now, we'll use a generic mobile app service
            url = f"{self.ha_url}/api/services/notify/mobile_app"
            payload = {
                "title": notification['title'],
                "message": notification['message'],
                "data": {
                    "notification_id": notification['id'],
                    "actions": notification.get('actions', [])
                }
            }
            
            response = requests.post(url, headers=self.ha_headers, json=payload, timeout=10)
            response.raise_for_status()
            
            self.logger.debug(f"Sent mobile notification: {notification['id']}")
            return True
            
        except Exception as e:
            self.logger.debug(f"Mobile notification not available: {e}")
            return False
    
    def _should_send_notification(self, zone_id: int, notification_type: NotificationType) -> bool:
        """Check if notification should be sent based on frequency settings"""
        try:
            # Get last notification of this type for this zone
            query = """
                SELECT created_at FROM notifications_log 
                WHERE zone_id = ? AND notification_type = ? 
                ORDER BY created_at DESC LIMIT 1
            """
            result = self.db.execute_single(query, (zone_id, notification_type.value))
            
            last_sent = None
            if result:
                last_sent = datetime.fromisoformat(result['created_at'])
            
            # Use template manager to check frequency rules
            return self.template_manager.should_send_notification(
                notification_type, 
                last_sent, 
                self.default_settings
            )
            
        except Exception as e:
            self.logger.error(f"Failed to check notification frequency: {e}")
            return True  # Default to sending if check fails
    
    def _log_notification(self, notification: Dict[str, Any], zone_id: Optional[int]):
        """Log notification to database"""
        try:
            query = """
                INSERT INTO notifications_log (
                    zone_id, notification_type, personality_mode, message, 
                    recipient, delivery_status, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                zone_id,
                notification['type'],
                notification['personality'],
                notification['message'],
                'home_assistant',
                'sent',
                str(notification.get('metadata', {}))
            )
            
            self.db.execute_insert(query, params)
            
        except Exception as e:
            self.logger.error(f"Failed to log notification: {e}")
    
    def _classify_error(self, error_message: str) -> str:
        """Classify error type based on error message"""
        error_lower = error_message.lower()
        
        if 'camera' in error_lower or 'snapshot' in error_lower:
            return 'camera_error'
        elif 'timeout' in error_lower or 'connection' in error_lower:
            return 'connection_error'
        elif 'gemini' in error_lower or 'api' in error_lower:
            return 'ai_error'
        elif 'permission' in error_lower or 'auth' in error_lower:
            return 'auth_error'
        else:
            return 'unknown_error'
    
    def get_notification_history(self, zone_id: int = None, days: int = 7) -> List[Dict[str, Any]]:
        """Get notification history for a zone or all zones"""
        try:
            query = """
                SELECT * FROM notifications_log 
                WHERE created_at >= datetime('now', '-{} days')
            """.format(days)
            params = ()
            
            if zone_id:
                query += " AND zone_id = ?"
                params = (zone_id,)
            
            query += " ORDER BY created_at DESC"
            
            rows = self.db.execute_query(query, params)
            return [dict(row) for row in rows]
            
        except Exception as e:
            self.logger.error(f"Failed to get notification history: {e}")
            return []
