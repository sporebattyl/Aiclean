"""
NotificationEngine - Main orchestrator for the notification system
Component-based design following TDD principles
"""

import logging
from typing import Dict, Any, Optional
from .personality_formatter import PersonalityFormatter
from .message_template import MessageTemplate
from .notification_sender import NotificationSender

logger = logging.getLogger(__name__)


class NotificationEngine:
    """
    Main notification engine that orchestrates message formatting and sending.
    
    This component follows the Single Responsibility Principle and coordinates
    between the formatter, template, and sender components.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the notification engine with configuration.
        
        Args:
            config: Configuration dictionary containing notification settings
        """
        self.config = config
        self.personality = config.get('notification_personality', 'default')
        
        # Initialize components
        self.formatter = PersonalityFormatter(self.personality)
        self.template = MessageTemplate()
        self.sender = NotificationSender(config)
        
        logger.info(f"NotificationEngine initialized with personality: {self.personality}")
    
    def set_personality(self, personality: str) -> None:
        """
        Change the notification personality.
        
        Args:
            personality: New personality to use for notifications
        """
        self.personality = personality
        self.formatter = PersonalityFormatter(personality)
        logger.info(f"Notification personality changed to: {personality}")
    
    def send_task_notification(self, task_data: Dict[str, Any]) -> bool:
        """
        Send a notification about a new or updated task.
        
        Args:
            task_data: Dictionary containing task information
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        try:
            # Format the base message using template
            base_message = self.template.format_task_notification(task_data)
            
            # Apply personality formatting
            formatted_message = self.formatter.format_task_message(task_data, base_message)
            
            # Send the notification
            result = self.sender.send(formatted_message)
            
            if result:
                logger.info(f"Task notification sent successfully for zone: {task_data.get('zone')}")
            else:
                logger.error(f"Failed to send task notification for zone: {task_data.get('zone')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending task notification: {e}")
            return False
    
    def send_analysis_complete_notification(self, analysis_data: Dict[str, Any]) -> bool:
        """
        Send a notification when zone analysis is complete.
        
        Args:
            analysis_data: Dictionary containing analysis results
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        try:
            # Format the base message using template
            base_message = self.template.format_analysis_complete(analysis_data)
            
            # Apply personality formatting
            formatted_message = self.formatter.format_analysis_message(analysis_data, base_message)
            
            # Send the notification
            result = self.sender.send(formatted_message)
            
            if result:
                logger.info(f"Analysis complete notification sent for zone: {analysis_data.get('zone')}")
            else:
                logger.error(f"Failed to send analysis notification for zone: {analysis_data.get('zone')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending analysis notification: {e}")
            return False
    
    def send_system_status_notification(self, status_data: Dict[str, Any]) -> bool:
        """
        Send a notification about system status.
        
        Args:
            status_data: Dictionary containing system status information
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        try:
            # Format the base message using template
            base_message = self.template.format_system_status(status_data)
            
            # Apply personality formatting
            formatted_message = self.formatter.format_system_message(status_data, base_message)
            
            # Send the notification
            result = self.sender.send(formatted_message)
            
            if result:
                logger.info("System status notification sent successfully")
            else:
                logger.error("Failed to send system status notification")
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending system status notification: {e}")
            return False
    
    def test_notification(self, message: str = None) -> bool:
        """
        Send a test notification to verify the system is working.
        
        Args:
            message: Optional custom test message
            
        Returns:
            bool: True if test notification was sent successfully, False otherwise
        """
        try:
            test_message = message or "🧪 AICleaner notification test - system is working!"
            
            # Apply personality formatting to test message
            formatted_message = self.formatter.format_test_message(test_message)
            
            # Send the test notification
            result = self.sender.send(formatted_message)
            
            if result:
                logger.info("Test notification sent successfully")
            else:
                logger.error("Failed to send test notification")
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending test notification: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the notification engine.
        
        Returns:
            dict: Status information including personality and configuration
        """
        return {
            'personality': self.personality,
            'sender_configured': self.sender.is_configured(),
            'available_personalities': self.formatter.get_available_personalities()
        }
