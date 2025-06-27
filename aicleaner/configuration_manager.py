"""
ConfigurationManager - Component for handling addon configuration
Component-based design following TDD principles
"""

import os
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """
    Manages configuration validation and loading for the AICleaner addon
    Following component-based design principles
    """
    
    def __init__(self):
        """Initialize the configuration manager"""
        self.validation_errors = []
        self.valid_personalities = ['default', 'snarky', 'jarvis', 'roaster', 'butler', 'coach', 'zen']
        
    def validate_configuration(self, config: Dict[str, Any]) -> bool:
        """
        Validate the provided configuration
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        self.validation_errors = []
        
        # Validate required top-level fields
        required_fields = ['gemini_api_key', 'display_name']
        for field in required_fields:
            if field not in config or not config[field]:
                self.validation_errors.append(f"Missing or empty required field: '{field}'")
        
        # Validate zones if present
        if 'zones' in config and isinstance(config['zones'], list):
            for i, zone in enumerate(config['zones']):
                self._validate_zone_config(zone, i)
        
        return len(self.validation_errors) == 0
    
    def _validate_zone_config(self, zone: Dict[str, Any], zone_index: int) -> None:
        """Validate individual zone configuration"""
        required_zone_fields = [
            'name', 'icon', 'purpose', 'camera_entity', 'todo_list_entity',
            'update_frequency', 'notifications_enabled', 'notification_service',
            'notification_personality', 'notify_on_create', 'notify_on_complete'
        ]
        
        for field in required_zone_fields:
            if field not in zone:
                self.validation_errors.append(f"Zone {zone_index}: Missing required field '{field}'")
            elif field == 'name' and not zone[field]:
                self.validation_errors.append(f"Zone {zone_index}: Zone name cannot be empty")
        
        # Validate update frequency range
        if 'update_frequency' in zone:
            freq = zone['update_frequency']
            if not isinstance(freq, int) or freq < 1 or freq > 168:
                self.validation_errors.append(f"Zone {zone_index}: update_frequency must be between 1 and 168 hours")
        
        # Validate notification personality
        if 'notification_personality' in zone:
            personality = zone['notification_personality']
            if personality not in self.valid_personalities:
                self.validation_errors.append(
                    f"Zone {zone_index}: Invalid notification_personality '{personality}'. "
                    f"Valid options: {', '.join(self.valid_personalities)}"
                )
    
    def get_validation_errors(self) -> List[str]:
        """Get list of validation errors from last validation"""
        return self.validation_errors.copy()
    
    def load_configuration(self) -> Dict[str, Any]:
        """
        Load configuration from environment variables (Home Assistant addon style)
        
        Returns:
            Dict containing configuration with defaults for missing values
        """
        config = {
            'gemini_api_key': os.getenv('GEMINI_API_KEY', ''),
            'display_name': os.getenv('DISPLAY_NAME', 'User'),
            'zones': []
        }
        
        # Try to load zones from environment if available
        # In a real addon, this would come from the addon options
        zones_count = int(os.getenv('ZONES_COUNT', '0'))
        for i in range(zones_count):
            zone_config = self._load_zone_from_env(i)
            if zone_config:
                config['zones'].append(zone_config)
        
        return config
    
    def _load_zone_from_env(self, zone_index: int) -> Optional[Dict[str, Any]]:
        """Load individual zone configuration from environment variables"""
        prefix = f'ZONE_{zone_index}_'
        
        zone_name = os.getenv(f'{prefix}NAME')
        if not zone_name:
            return None
        
        return {
            'name': zone_name,
            'icon': os.getenv(f'{prefix}ICON', 'mdi:home'),
            'purpose': os.getenv(f'{prefix}PURPOSE', 'Keep area clean'),
            'camera_entity': os.getenv(f'{prefix}CAMERA_ENTITY', ''),
            'todo_list_entity': os.getenv(f'{prefix}TODO_LIST_ENTITY', ''),
            'update_frequency': int(os.getenv(f'{prefix}UPDATE_FREQUENCY', '30')),
            'notifications_enabled': os.getenv(f'{prefix}NOTIFICATIONS_ENABLED', 'false').lower() == 'true',
            'notification_service': os.getenv(f'{prefix}NOTIFICATION_SERVICE', ''),
            'notification_personality': os.getenv(f'{prefix}NOTIFICATION_PERSONALITY', 'default'),
            'notify_on_create': os.getenv(f'{prefix}NOTIFY_ON_CREATE', 'true').lower() == 'true',
            'notify_on_complete': os.getenv(f'{prefix}NOTIFY_ON_COMPLETE', 'true').lower() == 'true'
        }
    
    def get_startup_guidance(self) -> str:
        """
        Provide helpful guidance for configuration issues
        
        Returns:
            String with helpful configuration guidance
        """
        if not self.validation_errors:
            return "Configuration is valid."
        
        guidance = [
            "AICleaner Configuration Issues:",
            "=" * 40,
            "",
            "The following configuration issues need to be resolved:",
            ""
        ]
        
        for error in self.validation_errors:
            guidance.append(f"• {error}")
        
        guidance.extend([
            "",
            "Configuration Help:",
            "=" * 20,
            "",
            "1. Gemini API Key: Get your API key from https://makersuite.google.com/app/apikey",
            "2. Display Name: Your preferred name for notifications",
            "3. Zones: Configure at least one zone with:",
            "   - Camera entity (e.g., camera.kitchen)",
            "   - Todo list entity (e.g., todo.kitchen_tasks)",
            "   - Update frequency (1-168 hours)",
            "   - Notification settings",
            "",
            "Please update your addon configuration and restart."
        ])
        
        return "\n".join(guidance)
    
    def is_configuration_complete(self, config: Dict[str, Any]) -> bool:
        """
        Check if configuration is complete enough to start the addon
        
        Args:
            config: Configuration to check
            
        Returns:
            bool: True if configuration is complete enough to start
        """
        # Minimum requirements for startup
        if not config.get('gemini_api_key'):
            return False
        
        if not config.get('display_name'):
            return False
        
        # Need at least one valid zone
        zones = config.get('zones', [])
        if not zones:
            return False
        
        for zone in zones:
            if not zone.get('name') or not zone.get('camera_entity') or not zone.get('todo_list_entity'):
                return False
        
        return True
    
    def get_configuration_status(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get detailed configuration status for debugging
        
        Args:
            config: Configuration to analyze
            
        Returns:
            Dict with configuration status details
        """
        is_valid = self.validate_configuration(config)
        is_complete = self.is_configuration_complete(config)
        
        return {
            'is_valid': is_valid,
            'is_complete': is_complete,
            'errors': self.get_validation_errors(),
            'zones_count': len(config.get('zones', [])),
            'has_api_key': bool(config.get('gemini_api_key')),
            'has_display_name': bool(config.get('display_name')),
            'guidance': self.get_startup_guidance() if not is_valid else None
        }
