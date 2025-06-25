"""
Template Manager - Handles notification templates and formatting
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, time
from ..data.models import NotificationType, PersonalityMode


class TemplateManager:
    """Manages notification templates and formatting"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._initialize_templates()
    
    def _initialize_templates(self):
        """Initialize notification templates"""
        self.notification_templates = {
            NotificationType.TASK_REMINDER: {
                'title': 'Cleaning Reminder',
                'icon': 'mdi:broom',
                'priority': 'normal',
                'persistent': False,
                'actions': [
                    {'action': 'view_tasks', 'title': 'View Tasks'},
                    {'action': 'snooze', 'title': 'Remind Later'}
                ]
            },
            NotificationType.COMPLETION_CELEBRATION: {
                'title': 'Great Job!',
                'icon': 'mdi:check-circle',
                'priority': 'high',
                'persistent': False,
                'actions': [
                    {'action': 'view_zone', 'title': 'View Zone'},
                    {'action': 'share_achievement', 'title': 'Share'}
                ]
            },
            NotificationType.STREAK_MILESTONE: {
                'title': 'Streak Milestone!',
                'icon': 'mdi:fire',
                'priority': 'high',
                'persistent': True,
                'actions': [
                    {'action': 'view_stats', 'title': 'View Stats'},
                    {'action': 'celebrate', 'title': 'Celebrate'}
                ]
            },
            NotificationType.ANALYSIS_ERROR: {
                'title': 'Analysis Issue',
                'icon': 'mdi:alert-circle',
                'priority': 'high',
                'persistent': True,
                'actions': [
                    {'action': 'check_camera', 'title': 'Check Camera'},
                    {'action': 'retry_analysis', 'title': 'Retry'}
                ]
            }
        }
        
        # Time-based greeting templates
        self.time_greetings = {
            'morning': ['Good morning!', 'Rise and shine!', 'Morning!'],
            'afternoon': ['Good afternoon!', 'Hope your day is going well!', 'Afternoon!'],
            'evening': ['Good evening!', 'Hope you had a great day!', 'Evening!'],
            'night': ['Good night!', 'Time to wind down!', 'Night!']
        }
        
        # Emoji sets for different personalities
        self.emoji_sets = {
            PersonalityMode.CONCISE: {
                'success': '✅',
                'warning': '⚠️',
                'error': '❌',
                'info': 'ℹ️',
                'celebration': '🎉'
            },
            PersonalityMode.SNARKY: {
                'success': '😏',
                'warning': '🙄',
                'error': '🤦',
                'info': '🤖',
                'celebration': '🎭'
            },
            PersonalityMode.ENCOURAGING: {
                'success': '🌟',
                'warning': '💪',
                'error': '🤗',
                'info': '💡',
                'celebration': '🎉'
            }
        }
    
    def format_notification(self, notification_type: NotificationType, message: str,
                          zone_name: str, personality: PersonalityMode,
                          additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Format a complete notification with all metadata
        
        Args:
            notification_type: Type of notification
            message: The main message content
            zone_name: Name of the zone
            personality: Personality mode for styling
            additional_data: Additional context data
            
        Returns:
            Complete notification dictionary
        """
        try:
            template = self.notification_templates.get(notification_type, {})
            additional_data = additional_data or {}
            
            # Get time-based greeting
            greeting = self._get_time_greeting()
            
            # Get appropriate emoji
            emoji = self._get_emoji(personality, notification_type)
            
            # Build the notification
            notification = {
                'id': f"roo_{int(datetime.now().timestamp())}_{zone_name.lower().replace(' ', '_')}",
                'type': notification_type.value,
                'title': f"{emoji} {template.get('title', 'Roo Notification')}",
                'message': message,
                'zone_name': zone_name,
                'personality': personality.value,
                'timestamp': datetime.now().isoformat(),
                'greeting': greeting,
                'icon': template.get('icon', 'mdi:robot'),
                'priority': template.get('priority', 'normal'),
                'persistent': template.get('persistent', False),
                'actions': template.get('actions', []),
                'metadata': {
                    'zone_name': zone_name,
                    'notification_type': notification_type.value,
                    'personality_mode': personality.value,
                    **additional_data
                }
            }
            
            # Add type-specific formatting
            if notification_type == NotificationType.TASK_REMINDER:
                notification = self._format_task_reminder(notification, additional_data)
            elif notification_type == NotificationType.COMPLETION_CELEBRATION:
                notification = self._format_completion_celebration(notification, additional_data)
            elif notification_type == NotificationType.STREAK_MILESTONE:
                notification = self._format_streak_milestone(notification, additional_data)
            elif notification_type == NotificationType.ANALYSIS_ERROR:
                notification = self._format_analysis_error(notification, additional_data)
            
            return notification
            
        except Exception as e:
            self.logger.error(f"Failed to format notification: {e}")
            return {
                'id': f"roo_error_{int(datetime.now().timestamp())}",
                'type': 'error',
                'title': 'Notification Error',
                'message': 'Failed to format notification',
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_time_greeting(self) -> str:
        """Get appropriate greeting based on time of day"""
        current_hour = datetime.now().hour
        
        if 5 <= current_hour < 12:
            return 'morning'
        elif 12 <= current_hour < 17:
            return 'afternoon'
        elif 17 <= current_hour < 21:
            return 'evening'
        else:
            return 'night'
    
    def _get_emoji(self, personality: PersonalityMode, notification_type: NotificationType) -> str:
        """Get appropriate emoji for personality and notification type"""
        emoji_map = {
            NotificationType.TASK_REMINDER: 'warning',
            NotificationType.COMPLETION_CELEBRATION: 'celebration',
            NotificationType.STREAK_MILESTONE: 'celebration',
            NotificationType.ANALYSIS_ERROR: 'error'
        }
        
        emoji_type = emoji_map.get(notification_type, 'info')
        return self.emoji_sets.get(personality, {}).get(emoji_type, '📱')
    
    def _format_task_reminder(self, notification: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Format task reminder specific data"""
        task_count = data.get('task_count', 0)
        score = data.get('score', 0)
        
        notification['metadata'].update({
            'task_count': task_count,
            'cleanliness_score': score,
            'urgency': 'high' if score < 50 else 'medium' if score < 70 else 'low'
        })
        
        # Adjust priority based on score
        if score < 50:
            notification['priority'] = 'high'
        elif score < 70:
            notification['priority'] = 'normal'
        else:
            notification['priority'] = 'low'
        
        return notification
    
    def _format_completion_celebration(self, notification: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Format completion celebration specific data"""
        score = data.get('score', 100)
        tasks_completed = data.get('tasks_completed', 0)
        
        notification['metadata'].update({
            'final_score': score,
            'tasks_completed': tasks_completed,
            'achievement_level': 'perfect' if score >= 95 else 'excellent' if score >= 85 else 'good'
        })
        
        return notification
    
    def _format_streak_milestone(self, notification: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Format streak milestone specific data"""
        streak_days = data.get('streak_days', 0)
        
        notification['metadata'].update({
            'streak_days': streak_days,
            'milestone_type': self._get_milestone_type(streak_days)
        })
        
        return notification
    
    def _format_analysis_error(self, notification: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Format analysis error specific data"""
        error_type = data.get('error_type', 'unknown')
        retry_count = data.get('retry_count', 0)
        
        notification['metadata'].update({
            'error_type': error_type,
            'retry_count': retry_count,
            'requires_attention': retry_count >= 3
        })
        
        return notification
    
    def _get_milestone_type(self, streak_days: int) -> str:
        """Determine milestone type based on streak days"""
        if streak_days >= 30:
            return 'legendary'
        elif streak_days >= 14:
            return 'amazing'
        elif streak_days >= 7:
            return 'great'
        elif streak_days >= 3:
            return 'good'
        else:
            return 'start'
    
    def create_summary_notification(self, zones_data: List[Dict[str, Any]], 
                                  personality: PersonalityMode) -> Dict[str, Any]:
        """Create a summary notification for multiple zones"""
        try:
            total_zones = len(zones_data)
            clean_zones = len([z for z in zones_data if z.get('score', 0) >= z.get('threshold', 70)])
            total_tasks = sum(z.get('task_count', 0) for z in zones_data)
            
            # Generate summary message based on personality
            if personality == PersonalityMode.CONCISE:
                message = f"{clean_zones}/{total_zones} zones clean, {total_tasks} total tasks"
            elif personality == PersonalityMode.SNARKY:
                if clean_zones == total_zones:
                    message = f"Shocking! All {total_zones} zones are actually clean. I'm impressed."
                else:
                    message = f"Only {clean_zones} out of {total_zones} zones are clean. {total_tasks} tasks are staging a rebellion."
            else:  # ENCOURAGING
                if clean_zones == total_zones:
                    message = f"🌟 Amazing! All {total_zones} zones are beautifully maintained!"
                else:
                    message = f"Great progress! {clean_zones} zones clean, just {total_tasks} tasks to go!"
            
            return self.format_notification(
                NotificationType.TASK_REMINDER,
                message,
                "Home Summary",
                personality,
                {
                    'total_zones': total_zones,
                    'clean_zones': clean_zones,
                    'total_tasks': total_tasks,
                    'zones_data': zones_data
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create summary notification: {e}")
            return {}
    
    def should_send_notification(self, notification_type: NotificationType, 
                               last_sent: Optional[datetime], 
                               frequency_settings: Dict[str, Any]) -> bool:
        """Determine if a notification should be sent based on frequency settings"""
        if not last_sent:
            return True
        
        now = datetime.now()
        time_since_last = (now - last_sent).total_seconds() / 60  # minutes
        
        # Get minimum interval for notification type
        intervals = frequency_settings.get('intervals', {})
        min_interval = intervals.get(notification_type.value, 60)  # default 60 minutes
        
        # Check quiet hours
        quiet_hours = frequency_settings.get('quiet_hours', {})
        if quiet_hours.get('enabled', False):
            start_time = time.fromisoformat(quiet_hours.get('start', '22:00'))
            end_time = time.fromisoformat(quiet_hours.get('end', '07:00'))
            current_time = now.time()
            
            if start_time <= end_time:
                # Same day quiet hours
                if start_time <= current_time <= end_time:
                    return False
            else:
                # Overnight quiet hours
                if current_time >= start_time or current_time <= end_time:
                    return False
        
        return time_since_last >= min_interval
