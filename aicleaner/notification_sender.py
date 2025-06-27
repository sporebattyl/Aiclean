"""
NotificationSender - Handles the actual delivery of notifications
Component-based design following TDD principles
"""

import logging
import requests
import json
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class NotificationSender:
    """
    Handles the actual sending of notifications to various endpoints.
    
    This component is responsible for the delivery mechanism of notifications,
    supporting multiple delivery methods like webhooks, Home Assistant services, etc.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the notification sender with configuration.
        
        Args:
            config: Configuration dictionary containing notification settings
        """
        self.config = config
        self.webhook_url = config.get('webhook_url')
        self.ha_service = config.get('ha_service')
        self.timeout = config.get('timeout', 10)
        self.retry_count = config.get('retry_count', 3)
        
        logger.info(f"NotificationSender initialized with config: {list(config.keys())}")
    
    def is_configured(self) -> bool:
        """
        Check if the sender is properly configured.
        
        Returns:
            bool: True if at least one delivery method is configured
        """
        return bool(self.webhook_url or self.ha_service)
    
    def send(self, message: str, priority: str = 'normal') -> bool:
        """
        Send a notification message.
        
        Args:
            message: The message to send
            priority: Priority level (low, normal, high)
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        if not self.is_configured():
            logger.warning("No notification delivery method configured")
            return False
        
        success = False
        
        # Try webhook delivery
        if self.webhook_url:
            success = self._send_webhook(message, priority) or success
        
        # Try Home Assistant service delivery
        if self.ha_service:
            success = self._send_ha_service(message, priority) or success
        
        return success
    
    def _send_webhook(self, message: str, priority: str) -> bool:
        """
        Send notification via webhook.
        
        Args:
            message: The message to send
            priority: Priority level
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            payload = {
                'message': message,
                'priority': priority,
                'timestamp': datetime.now().isoformat(),
                'source': 'aicleaner'
            }
            
            # Add additional webhook-specific formatting
            if 'discord' in self.webhook_url.lower():
                payload = self._format_discord_payload(message, priority)
            elif 'slack' in self.webhook_url.lower():
                payload = self._format_slack_payload(message, priority)
            elif 'teams' in self.webhook_url.lower():
                payload = self._format_teams_payload(message, priority)
            
            for attempt in range(self.retry_count):
                try:
                    response = requests.post(
                        self.webhook_url,
                        json=payload,
                        timeout=self.timeout,
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    if response.status_code in [200, 201, 202, 204]:
                        logger.info(f"Webhook notification sent successfully (attempt {attempt + 1})")
                        return True
                    else:
                        logger.warning(f"Webhook returned status {response.status_code} (attempt {attempt + 1})")
                        
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Webhook request failed (attempt {attempt + 1}): {e}")
                    
                if attempt < self.retry_count - 1:
                    # Wait before retry (exponential backoff)
                    import time
                    time.sleep(2 ** attempt)
            
            logger.error(f"Failed to send webhook notification after {self.retry_count} attempts")
            return False
            
        except Exception as e:
            logger.error(f"Error sending webhook notification: {e}")
            return False
    
    def _send_ha_service(self, message: str, priority: str) -> bool:
        """
        Send notification via Home Assistant service.
        
        Args:
            message: The message to send
            priority: Priority level
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            # This would integrate with Home Assistant's notification services
            # For now, we'll log it as a placeholder
            logger.info(f"HA Service notification: {message} (priority: {priority})")
            
            # In a real implementation, this would call:
            # self.hass.services.call('notify', self.ha_service, {'message': message})
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending HA service notification: {e}")
            return False
    
    def _format_discord_payload(self, message: str, priority: str) -> Dict[str, Any]:
        """Format payload for Discord webhook."""
        color_map = {
            'low': 0x00ff00,      # Green
            'normal': 0xffff00,   # Yellow
            'high': 0xff0000      # Red
        }
        
        return {
            'embeds': [{
                'title': '🏠 AICleaner Notification',
                'description': message,
                'color': color_map.get(priority, 0xffff00),
                'timestamp': datetime.now().isoformat(),
                'footer': {
                    'text': f'Priority: {priority.upper()}'
                }
            }]
        }
    
    def _format_slack_payload(self, message: str, priority: str) -> Dict[str, Any]:
        """Format payload for Slack webhook."""
        color_map = {
            'low': 'good',
            'normal': 'warning',
            'high': 'danger'
        }
        
        return {
            'text': '🏠 AICleaner Notification',
            'attachments': [{
                'color': color_map.get(priority, 'warning'),
                'text': message,
                'footer': f'Priority: {priority.upper()}',
                'ts': int(datetime.now().timestamp())
            }]
        }
    
    def _format_teams_payload(self, message: str, priority: str) -> Dict[str, Any]:
        """Format payload for Microsoft Teams webhook."""
        color_map = {
            'low': '00ff00',
            'normal': 'ffff00',
            'high': 'ff0000'
        }
        
        return {
            '@type': 'MessageCard',
            '@context': 'http://schema.org/extensions',
            'themeColor': color_map.get(priority, 'ffff00'),
            'summary': 'AICleaner Notification',
            'sections': [{
                'activityTitle': '🏠 AICleaner Notification',
                'activitySubtitle': f'Priority: {priority.upper()}',
                'text': message,
                'markdown': True
            }]
        }
    
    def test_connection(self) -> Dict[str, bool]:
        """
        Test all configured notification methods.
        
        Returns:
            dict: Results of connection tests for each method
        """
        results = {}
        
        if self.webhook_url:
            test_message = "🧪 AICleaner connection test"
            results['webhook'] = self._send_webhook(test_message, 'normal')
        
        if self.ha_service:
            test_message = "🧪 AICleaner HA service test"
            results['ha_service'] = self._send_ha_service(test_message, 'normal')
        
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the notification sender.
        
        Returns:
            dict: Status information including configuration and connectivity
        """
        return {
            'configured': self.is_configured(),
            'webhook_configured': bool(self.webhook_url),
            'ha_service_configured': bool(self.ha_service),
            'timeout': self.timeout,
            'retry_count': self.retry_count
        }
