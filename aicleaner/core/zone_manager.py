"""
Zone Manager - Handles multi-zone configuration and management
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..data import ZoneRepository, Zone, PersonalityMode


class ZoneManager:
    """Manages multiple zones and their configurations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.zone_repo = ZoneRepository()
        self._zone_cache = {}
        self._load_zones()
    
    def _load_zones(self):
        """Load all zones into cache"""
        try:
            zones = self.zone_repo.get_all()
            self._zone_cache = {zone.id: zone for zone in zones}
            self.logger.info(f"Loaded {len(zones)} zones into cache")
        except Exception as e:
            self.logger.error(f"Failed to load zones: {e}")
            self._zone_cache = {}
    
    def get_zone(self, zone_id: int) -> Optional[Zone]:
        """Get a zone by ID"""
        if zone_id in self._zone_cache:
            return self._zone_cache[zone_id]
        
        # Try to load from database if not in cache
        zone = self.zone_repo.get_by_id(zone_id)
        if zone:
            self._zone_cache[zone_id] = zone
        return zone
    
    def get_zone_by_name(self, name: str) -> Optional[Zone]:
        """Get a zone by name"""
        # Check cache first
        for zone in self._zone_cache.values():
            if zone.name == name:
                return zone
        
        # Try database
        zone = self.zone_repo.get_by_name(name)
        if zone:
            self._zone_cache[zone.id] = zone
        return zone
    
    def get_all_zones(self, enabled_only: bool = False) -> List[Zone]:
        """Get all zones"""
        zones = list(self._zone_cache.values())
        if enabled_only:
            zones = [zone for zone in zones if zone.enabled]
        return sorted(zones, key=lambda z: z.name)
    
    def get_enabled_zones(self) -> List[Zone]:
        """Get only enabled zones"""
        return self.get_all_zones(enabled_only=True)
    
    def create_zone(self, zone_data: Dict[str, Any]) -> Zone:
        """Create a new zone"""
        try:
            # Validate required fields
            required_fields = ['name', 'display_name', 'camera_entity_id']
            for field in required_fields:
                if field not in zone_data or not zone_data[field]:
                    raise ValueError(f"Missing required field: {field}")
            
            # Check for duplicate names
            if self.get_zone_by_name(zone_data['name']):
                raise ValueError(f"Zone with name '{zone_data['name']}' already exists")
            
            # Create zone object
            zone = Zone(
                name=zone_data['name'],
                display_name=zone_data['display_name'],
                camera_entity_id=zone_data['camera_entity_id'],
                todo_list_entity_id=zone_data.get('todo_list_entity_id'),
                sensor_entity_id=zone_data.get('sensor_entity_id'),
                enabled=zone_data.get('enabled', True),
                notification_enabled=zone_data.get('notification_enabled', True),
                personality_mode=PersonalityMode(zone_data.get('personality_mode', 'concise')),
                update_frequency=zone_data.get('update_frequency', 60),
                cleanliness_threshold=zone_data.get('cleanliness_threshold', 70),
                max_tasks_per_analysis=zone_data.get('max_tasks_per_analysis', 10)
            )
            
            # Save to database
            zone_id = self.zone_repo.create(zone)
            zone.id = zone_id
            
            # Update cache
            self._zone_cache[zone_id] = zone
            
            self.logger.info(f"Created new zone: {zone.name} (ID: {zone_id})")
            return zone
            
        except Exception as e:
            self.logger.error(f"Failed to create zone: {e}")
            raise
    
    def update_zone(self, zone_id: int, updates: Dict[str, Any]) -> bool:
        """Update an existing zone"""
        try:
            zone = self.get_zone(zone_id)
            if not zone:
                raise ValueError(f"Zone with ID {zone_id} not found")
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(zone, key):
                    if key == 'personality_mode' and isinstance(value, str):
                        setattr(zone, key, PersonalityMode(value))
                    else:
                        setattr(zone, key, value)
            
            # Save to database
            success = self.zone_repo.update(zone)
            
            if success:
                # Update cache
                self._zone_cache[zone_id] = zone
                self.logger.info(f"Updated zone: {zone.name} (ID: {zone_id})")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to update zone {zone_id}: {e}")
            return False
    
    def delete_zone(self, zone_id: int) -> bool:
        """Delete a zone"""
        try:
            zone = self.get_zone(zone_id)
            if not zone:
                raise ValueError(f"Zone with ID {zone_id} not found")
            
            # Delete from database (cascades to related data)
            success = self.zone_repo.delete(zone_id)
            
            if success:
                # Remove from cache
                if zone_id in self._zone_cache:
                    del self._zone_cache[zone_id]
                self.logger.info(f"Deleted zone: {zone.name} (ID: {zone_id})")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to delete zone {zone_id}: {e}")
            return False
    
    def enable_zone(self, zone_id: int) -> bool:
        """Enable a zone"""
        return self.update_zone(zone_id, {'enabled': True})
    
    def disable_zone(self, zone_id: int) -> bool:
        """Disable a zone"""
        return self.update_zone(zone_id, {'enabled': False})
    
    def get_zone_summary(self, zone_id: int) -> Dict[str, Any]:
        """Get a summary of zone status and metrics"""
        zone = self.get_zone(zone_id)
        if not zone:
            return {}
        
        try:
            # This would integrate with TaskRepository and PerformanceMetricsRepository
            # For now, return basic zone info
            return {
                'id': zone.id,
                'name': zone.name,
                'display_name': zone.display_name,
                'enabled': zone.enabled,
                'camera_entity_id': zone.camera_entity_id,
                'personality_mode': zone.personality_mode.value,
                'update_frequency': zone.update_frequency,
                'cleanliness_threshold': zone.cleanliness_threshold,
                'notification_enabled': zone.notification_enabled,
                'last_updated': zone.updated_at.isoformat() if zone.updated_at else None
            }
        except Exception as e:
            self.logger.error(f"Failed to get zone summary for {zone_id}: {e}")
            return {}
    
    def validate_zone_config(self, zone_data: Dict[str, Any]) -> List[str]:
        """Validate zone configuration and return list of errors"""
        errors = []
        
        # Required fields
        required_fields = ['name', 'display_name', 'camera_entity_id']
        for field in required_fields:
            if field not in zone_data or not zone_data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Name validation
        if 'name' in zone_data:
            name = zone_data['name']
            if not name.replace('_', '').replace('-', '').isalnum():
                errors.append("Zone name must contain only letters, numbers, hyphens, and underscores")
            if len(name) > 50:
                errors.append("Zone name must be 50 characters or less")
        
        # Numeric field validation
        numeric_fields = {
            'update_frequency': (1, 1440),  # 1 minute to 24 hours
            'cleanliness_threshold': (0, 100),
            'max_tasks_per_analysis': (1, 50)
        }
        
        for field, (min_val, max_val) in numeric_fields.items():
            if field in zone_data:
                try:
                    value = int(zone_data[field])
                    if not min_val <= value <= max_val:
                        errors.append(f"{field} must be between {min_val} and {max_val}")
                except (ValueError, TypeError):
                    errors.append(f"{field} must be a valid integer")
        
        # Personality mode validation
        if 'personality_mode' in zone_data:
            try:
                PersonalityMode(zone_data['personality_mode'])
            except ValueError:
                valid_modes = [mode.value for mode in PersonalityMode]
                errors.append(f"personality_mode must be one of: {', '.join(valid_modes)}")
        
        return errors
    
    def migrate_v1_config(self, v1_config: Dict[str, Any]) -> Zone:
        """Migrate v1.0 configuration to v2.0 zone"""
        try:
            zone_data = {
                'name': 'default',
                'display_name': 'Default Room',
                'camera_entity_id': v1_config.get('camera_entity'),
                'todo_list_entity_id': v1_config.get('todo_list_entity'),
                'sensor_entity_id': v1_config.get('sensor_entity_id', 'sensor.aicleaner_cleanliness_score'),
                'update_frequency': v1_config.get('update_frequency', 60),
                'enabled': True,
                'notification_enabled': True,
                'personality_mode': 'concise'
            }
            
            # Validate the migrated config
            errors = self.validate_zone_config(zone_data)
            if errors:
                raise ValueError(f"Migration validation failed: {'; '.join(errors)}")
            
            # Create the zone
            zone = self.create_zone(zone_data)
            self.logger.info("Successfully migrated v1.0 configuration to default zone")
            return zone
            
        except Exception as e:
            self.logger.error(f"Failed to migrate v1.0 configuration: {e}")
            raise
    
    def refresh_cache(self):
        """Refresh the zone cache from database"""
        self._load_zones()
