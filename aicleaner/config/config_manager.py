"""
Configuration Manager - Handles system and zone configuration management
"""
import json
import yaml
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime
from ..data.models import Zone, PersonalityMode
from ..data.repositories import ZoneRepository
from .zone_templates import ZoneTemplates


class ConfigurationManager:
    """Manages system and zone configurations"""
    
    def __init__(self, config_path: str = "/data/config", zone_repository: ZoneRepository = None):
        self.logger = logging.getLogger(__name__)
        self.config_path = Path(config_path)
        self.config_path.mkdir(exist_ok=True)
        
        self.zone_repo = zone_repository
        self.zone_templates = ZoneTemplates()
        
        # Configuration files
        self.system_config_file = self.config_path / "system.yaml"
        self.zones_config_file = self.config_path / "zones.yaml"
        self.user_preferences_file = self.config_path / "preferences.yaml"
        
        # Load configurations
        self.system_config = self._load_system_config()
        self.user_preferences = self._load_user_preferences()
        
        self.logger.info(f"Configuration manager initialized: {self.config_path}")
    
    def _load_system_config(self) -> Dict[str, Any]:
        """Load system configuration"""
        default_config = {
            'version': '2.0',
            'database': {
                'path': '/data/roo.db',
                'backup_enabled': True,
                'backup_retention_days': 30,
                'auto_archive_enabled': True,
                'archive_after_days': 30
            },
            'ai_analysis': {
                'gemini_model': 'gemini-1.5-flash',
                'max_retries': 3,
                'timeout_seconds': 30,
                'confidence_threshold': 0.7
            },
            'notifications': {
                'enabled': True,
                'delivery_methods': ['persistent_notification', 'mobile_app'],
                'quiet_hours': {
                    'enabled': True,
                    'start': '22:00',
                    'end': '07:00'
                },
                'frequency_limits': {
                    'task_reminder': 60,
                    'completion_celebration': 0,
                    'streak_milestone': 0,
                    'analysis_error': 30
                }
            },
            'performance': {
                'max_concurrent_analyses': 3,
                'image_cache_size_mb': 100,
                'query_timeout_seconds': 30,
                'slow_query_threshold_ms': 1000
            },
            'security': {
                'api_rate_limit_per_minute': 60,
                'max_image_size_mb': 10,
                'allowed_image_formats': ['jpg', 'jpeg', 'png', 'webp']
            }
        }
        
        if self.system_config_file.exists():
            try:
                with open(self.system_config_file, 'r') as f:
                    loaded_config = yaml.safe_load(f)
                    # Merge with defaults
                    return self._deep_merge(default_config, loaded_config)
            except Exception as e:
                self.logger.error(f"Failed to load system config: {e}")
        
        # Save default config
        self._save_system_config(default_config)
        return default_config
    
    def _load_user_preferences(self) -> Dict[str, Any]:
        """Load user preferences"""
        default_preferences = {
            'ui': {
                'theme': 'auto',
                'default_view': 'dashboard',
                'show_advanced_options': False,
                'compact_mode': False
            },
            'notifications': {
                'default_personality': 'encouraging',
                'show_completion_animations': True,
                'sound_enabled': False,
                'desktop_notifications': True
            },
            'zones': {
                'default_update_frequency': 60,
                'default_cleanliness_threshold': 75,
                'auto_create_ignore_rules': True,
                'show_confidence_scores': True
            },
            'analytics': {
                'data_retention_days': 365,
                'track_usage_patterns': True,
                'share_anonymous_stats': False
            }
        }
        
        if self.user_preferences_file.exists():
            try:
                with open(self.user_preferences_file, 'r') as f:
                    loaded_prefs = yaml.safe_load(f)
                    return self._deep_merge(default_preferences, loaded_prefs)
            except Exception as e:
                self.logger.error(f"Failed to load user preferences: {e}")
        
        # Save default preferences
        self._save_user_preferences(default_preferences)
        return default_preferences
    
    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = base.copy()
        
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get_system_config(self, section: str = None) -> Union[Dict[str, Any], Any]:
        """Get system configuration or specific section"""
        if section:
            return self.system_config.get(section, {})
        return self.system_config.copy()
    
    def update_system_config(self, updates: Dict[str, Any], section: str = None) -> bool:
        """Update system configuration"""
        try:
            if section:
                if section not in self.system_config:
                    self.system_config[section] = {}
                self.system_config[section].update(updates)
            else:
                self.system_config = self._deep_merge(self.system_config, updates)
            
            self._save_system_config(self.system_config)
            self.logger.info(f"System config updated: {section or 'root'}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update system config: {e}")
            return False
    
    def get_user_preferences(self, section: str = None) -> Union[Dict[str, Any], Any]:
        """Get user preferences or specific section"""
        if section:
            return self.user_preferences.get(section, {})
        return self.user_preferences.copy()
    
    def update_user_preferences(self, updates: Dict[str, Any], section: str = None) -> bool:
        """Update user preferences"""
        try:
            if section:
                if section not in self.user_preferences:
                    self.user_preferences[section] = {}
                self.user_preferences[section].update(updates)
            else:
                self.user_preferences = self._deep_merge(self.user_preferences, updates)
            
            self._save_user_preferences(self.user_preferences)
            self.logger.info(f"User preferences updated: {section or 'root'}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update user preferences: {e}")
            return False
    
    def create_zone_from_template(self, template_name: str, zone_name: str, 
                                 camera_entity_id: str, overrides: Dict[str, Any] = None) -> Optional[Zone]:
        """Create a new zone from a template"""
        try:
            # Get template configuration
            zone_config = self.zone_templates.create_zone_from_template(
                template_name, zone_name, camera_entity_id, overrides
            )
            
            # Create zone object
            zone = Zone(
                name=zone_config['name'],
                display_name=zone_config['display_name'],
                camera_entity_id=zone_config['camera_entity_id'],
                personality_mode=zone_config['personality_mode'],
                enabled=zone_config.get('enabled', True),
                notification_enabled=zone_config.get('notification_enabled', True),
                update_frequency=zone_config.get('update_frequency', 60),
                cleanliness_threshold=zone_config.get('cleanliness_threshold', 75),
                max_tasks_per_analysis=zone_config.get('max_tasks_per_analysis', 10)
            )
            
            # Save to database if repository is available
            if self.zone_repo:
                zone_id = self.zone_repo.create_zone(zone)
                zone.id = zone_id
                
                # Create ignore rules from template
                ignore_patterns = zone_config.get('ignore_patterns', [])
                for pattern in ignore_patterns:
                    self.zone_repo.create_ignore_rule(zone_id, {
                        'rule_type': 'contains',
                        'rule_value': pattern,
                        'rule_description': f'Auto-created from {template_name} template'
                    })
            
            self.logger.info(f"Created zone '{zone_name}' from template '{template_name}'")
            return zone
            
        except Exception as e:
            self.logger.error(f"Failed to create zone from template: {e}")
            return None
    
    def export_zone_configuration(self, zone_id: int) -> Optional[Dict[str, Any]]:
        """Export zone configuration for backup or sharing"""
        if not self.zone_repo:
            return None
        
        try:
            zone = self.zone_repo.get_zone(zone_id)
            if not zone:
                return None
            
            # Get ignore rules
            ignore_rules = self.zone_repo.get_ignore_rules(zone_id)
            
            config = {
                'zone': {
                    'name': zone.name,
                    'display_name': zone.display_name,
                    'camera_entity_id': zone.camera_entity_id,
                    'personality_mode': zone.personality_mode.value,
                    'enabled': zone.enabled,
                    'notification_enabled': zone.notification_enabled,
                    'update_frequency': zone.update_frequency,
                    'cleanliness_threshold': zone.cleanliness_threshold,
                    'max_tasks_per_analysis': zone.max_tasks_per_analysis
                },
                'ignore_rules': [
                    {
                        'rule_type': rule.rule_type,
                        'rule_value': rule.rule_value,
                        'rule_description': rule.rule_description
                    }
                    for rule in ignore_rules
                ],
                'export_info': {
                    'exported_at': datetime.now().isoformat(),
                    'version': '2.0'
                }
            }
            
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to export zone configuration: {e}")
            return None
    
    def import_zone_configuration(self, config: Dict[str, Any], 
                                 new_zone_name: str = None) -> Optional[Zone]:
        """Import zone configuration from exported data"""
        if not self.zone_repo:
            return None
        
        try:
            zone_config = config.get('zone', {})
            
            # Create zone
            zone = Zone(
                name=new_zone_name or zone_config['name'],
                display_name=zone_config['display_name'],
                camera_entity_id=zone_config['camera_entity_id'],
                personality_mode=PersonalityMode(zone_config['personality_mode']),
                enabled=zone_config.get('enabled', True),
                notification_enabled=zone_config.get('notification_enabled', True),
                update_frequency=zone_config.get('update_frequency', 60),
                cleanliness_threshold=zone_config.get('cleanliness_threshold', 75),
                max_tasks_per_analysis=zone_config.get('max_tasks_per_analysis', 10)
            )
            
            zone_id = self.zone_repo.create_zone(zone)
            zone.id = zone_id
            
            # Import ignore rules
            ignore_rules = config.get('ignore_rules', [])
            for rule_config in ignore_rules:
                self.zone_repo.create_ignore_rule(zone_id, rule_config)
            
            self.logger.info(f"Imported zone configuration: {zone.name}")
            return zone
            
        except Exception as e:
            self.logger.error(f"Failed to import zone configuration: {e}")
            return None
    
    def get_zone_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get all available zone templates"""
        return self.zone_templates.get_all_templates()
    
    def get_template_recommendations(self, room_type_hint: str = None) -> List[Dict[str, Any]]:
        """Get template recommendations"""
        return self.zone_templates.get_template_recommendations(room_type_hint)
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate current configuration"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Validate system config
        system_errors = self._validate_system_config()
        validation_result['errors'].extend(system_errors)
        
        # Validate user preferences
        pref_warnings = self._validate_user_preferences()
        validation_result['warnings'].extend(pref_warnings)
        
        # Check for recommendations
        recommendations = self._generate_config_recommendations()
        validation_result['recommendations'].extend(recommendations)
        
        validation_result['valid'] = len(validation_result['errors']) == 0
        
        return validation_result
    
    def _validate_system_config(self) -> List[str]:
        """Validate system configuration"""
        errors = []
        
        # Check required sections
        required_sections = ['database', 'ai_analysis', 'notifications', 'performance']
        for section in required_sections:
            if section not in self.system_config:
                errors.append(f"Missing required section: {section}")
        
        # Validate specific settings
        if 'performance' in self.system_config:
            perf = self.system_config['performance']
            if perf.get('max_concurrent_analyses', 0) < 1:
                errors.append("max_concurrent_analyses must be at least 1")
        
        return errors
    
    def _validate_user_preferences(self) -> List[str]:
        """Validate user preferences"""
        warnings = []
        
        # Check for deprecated settings
        if 'deprecated_setting' in self.user_preferences:
            warnings.append("Found deprecated setting in user preferences")
        
        return warnings
    
    def _generate_config_recommendations(self) -> List[str]:
        """Generate configuration recommendations"""
        recommendations = []
        
        # Check if backup is enabled
        if not self.system_config.get('database', {}).get('backup_enabled', True):
            recommendations.append("Consider enabling database backups for data safety")
        
        # Check notification settings
        if not self.system_config.get('notifications', {}).get('enabled', True):
            recommendations.append("Notifications are disabled - you may miss important updates")
        
        return recommendations
    
    def _save_system_config(self, config: Dict[str, Any]):
        """Save system configuration to file"""
        with open(self.system_config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    def _save_user_preferences(self, preferences: Dict[str, Any]):
        """Save user preferences to file"""
        with open(self.user_preferences_file, 'w') as f:
            yaml.dump(preferences, f, default_flow_style=False, sort_keys=False)
    
    def backup_configuration(self, backup_path: str = None) -> str:
        """Create a backup of all configuration files"""
        if backup_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.config_path / f"config_backup_{timestamp}.tar.gz"
        
        import tarfile
        
        with tarfile.open(backup_path, 'w:gz') as tar:
            for config_file in [self.system_config_file, self.user_preferences_file]:
                if config_file.exists():
                    tar.add(config_file, arcname=config_file.name)
        
        self.logger.info(f"Configuration backup created: {backup_path}")
        return str(backup_path)
    
    def restore_configuration(self, backup_path: str) -> bool:
        """Restore configuration from backup"""
        try:
            import tarfile
            
            with tarfile.open(backup_path, 'r:gz') as tar:
                tar.extractall(self.config_path)
            
            # Reload configurations
            self.system_config = self._load_system_config()
            self.user_preferences = self._load_user_preferences()
            
            self.logger.info(f"Configuration restored from: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore configuration: {e}")
            return False

    def test_zone_configuration(self, zone_config: Dict[str, Any]) -> Dict[str, Any]:
        """Test a zone configuration for validity and connectivity"""
        test_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'connectivity_tests': {}
        }

        # Validate required fields
        required_fields = ['name', 'camera_entity_id', 'personality_mode']
        for field in required_fields:
            if field not in zone_config:
                test_result['errors'].append(f"Missing required field: {field}")

        # Validate field types and ranges
        if 'update_frequency' in zone_config:
            freq = zone_config['update_frequency']
            if not isinstance(freq, int) or freq < 5 or freq > 1440:
                test_result['errors'].append("update_frequency must be between 5 and 1440 minutes")

        if 'cleanliness_threshold' in zone_config:
            threshold = zone_config['cleanliness_threshold']
            if not isinstance(threshold, int) or threshold < 0 or threshold > 100:
                test_result['errors'].append("cleanliness_threshold must be between 0 and 100")

        # Test camera entity connectivity (if Home Assistant integration available)
        camera_entity = zone_config.get('camera_entity_id')
        if camera_entity:
            test_result['connectivity_tests']['camera'] = self._test_camera_entity(camera_entity)

        test_result['valid'] = len(test_result['errors']) == 0
        return test_result

    def _test_camera_entity(self, camera_entity_id: str) -> Dict[str, Any]:
        """Test camera entity connectivity"""
        # This would integrate with Home Assistant API in a real implementation
        return {
            'accessible': True,  # Placeholder
            'last_image_time': None,
            'resolution': None,
            'status': 'unknown'
        }

    def get_configuration_schema(self) -> Dict[str, Any]:
        """Get the configuration schema for validation"""
        return {
            'system_config': {
                'type': 'object',
                'required': ['version', 'database', 'ai_analysis', 'notifications'],
                'properties': {
                    'version': {'type': 'string'},
                    'database': {
                        'type': 'object',
                        'properties': {
                            'path': {'type': 'string'},
                            'backup_enabled': {'type': 'boolean'},
                            'backup_retention_days': {'type': 'integer', 'minimum': 1}
                        }
                    },
                    'ai_analysis': {
                        'type': 'object',
                        'properties': {
                            'gemini_model': {'type': 'string'},
                            'max_retries': {'type': 'integer', 'minimum': 1},
                            'timeout_seconds': {'type': 'integer', 'minimum': 5}
                        }
                    }
                }
            },
            'zone_config': {
                'type': 'object',
                'required': ['name', 'camera_entity_id', 'personality_mode'],
                'properties': {
                    'name': {'type': 'string', 'pattern': '^[a-z0-9_]+$'},
                    'display_name': {'type': 'string'},
                    'camera_entity_id': {'type': 'string'},
                    'personality_mode': {'enum': ['concise', 'snarky', 'encouraging']},
                    'update_frequency': {'type': 'integer', 'minimum': 5, 'maximum': 1440},
                    'cleanliness_threshold': {'type': 'integer', 'minimum': 0, 'maximum': 100}
                }
            }
        }
