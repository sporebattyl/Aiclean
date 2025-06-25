"""
Configuration Migration - Handles migration from v1.0 to v2.0 configurations
"""
import json
import yaml
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
from ..data.models import Zone, PersonalityMode
from ..data.repositories import ZoneRepository
from .zone_templates import ZoneTemplates


class ConfigurationMigrator:
    """Handles migration of configurations from v1.0 to v2.0"""
    
    def __init__(self, zone_repository: ZoneRepository = None):
        self.logger = logging.getLogger(__name__)
        self.zone_repo = zone_repository
        self.zone_templates = ZoneTemplates()
        
        # Migration mappings
        self.personality_mapping = {
            'normal': PersonalityMode.CONCISE,
            'friendly': PersonalityMode.ENCOURAGING,
            'sarcastic': PersonalityMode.SNARKY,
            'professional': PersonalityMode.CONCISE
        }
        
        self.logger.info("Configuration migrator initialized")
    
    def detect_v1_configuration(self, config_path: str = "/data") -> Dict[str, Any]:
        """Detect and analyze v1.0 configuration"""
        config_path = Path(config_path)
        detection_result = {
            'v1_detected': False,
            'config_files': [],
            'zones_found': [],
            'migration_needed': False,
            'estimated_complexity': 'simple'
        }
        
        # Look for v1.0 configuration files
        v1_config_files = [
            'roo_config.yaml',
            'roo_config.json',
            'config.yaml',
            'config.json'
        ]
        
        for config_file in v1_config_files:
            file_path = config_path / config_file
            if file_path.exists():
                detection_result['config_files'].append(str(file_path))
                detection_result['v1_detected'] = True
                
                # Analyze the configuration
                try:
                    config_data = self._load_config_file(file_path)
                    zones = self._extract_v1_zones(config_data)
                    detection_result['zones_found'].extend(zones)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to analyze {file_path}: {e}")
        
        # Check for v1.0 database
        v1_db_path = config_path / "roo_v1.db"
        if v1_db_path.exists():
            detection_result['v1_detected'] = True
            detection_result['config_files'].append(str(v1_db_path))
            
            # Try to extract zones from database
            try:
                db_zones = self._extract_zones_from_v1_db(v1_db_path)
                detection_result['zones_found'].extend(db_zones)
            except Exception as e:
                self.logger.warning(f"Failed to analyze v1 database: {e}")
        
        # Determine migration complexity
        if len(detection_result['zones_found']) > 5:
            detection_result['estimated_complexity'] = 'complex'
        elif len(detection_result['zones_found']) > 2:
            detection_result['estimated_complexity'] = 'moderate'
        
        detection_result['migration_needed'] = detection_result['v1_detected']
        
        return detection_result
    
    def _load_config_file(self, file_path: Path) -> Dict[str, Any]:
        """Load configuration file (JSON or YAML)"""
        with open(file_path, 'r') as f:
            if file_path.suffix.lower() == '.json':
                return json.load(f)
            else:
                return yaml.safe_load(f)
    
    def _extract_v1_zones(self, config_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract zone information from v1.0 configuration"""
        zones = []
        
        # Look for different v1.0 configuration structures
        if 'zones' in config_data:
            zones.extend(self._process_v1_zones_list(config_data['zones']))
        
        if 'rooms' in config_data:
            zones.extend(self._process_v1_rooms_list(config_data['rooms']))
        
        # Single zone configuration
        if 'camera_entity' in config_data and 'zone_name' in config_data:
            zones.append(self._process_v1_single_zone(config_data))
        
        return zones
    
    def _process_v1_zones_list(self, zones_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process v1.0 zones list"""
        processed_zones = []
        
        for zone_data in zones_data:
            processed_zone = {
                'name': zone_data.get('name', 'unknown_zone'),
                'display_name': zone_data.get('display_name', zone_data.get('name', 'Unknown Zone')),
                'camera_entity_id': zone_data.get('camera_entity', zone_data.get('camera_entity_id')),
                'personality_mode': self._map_v1_personality(zone_data.get('personality', 'normal')),
                'update_frequency': zone_data.get('update_frequency', 60),
                'cleanliness_threshold': zone_data.get('threshold', 75),
                'enabled': zone_data.get('enabled', True),
                'v1_source': 'zones_list'
            }
            processed_zones.append(processed_zone)
        
        return processed_zones
    
    def _process_v1_rooms_list(self, rooms_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process v1.0 rooms list"""
        processed_zones = []
        
        for room_data in rooms_data:
            processed_zone = {
                'name': room_data.get('room_name', 'unknown_room'),
                'display_name': room_data.get('display_name', room_data.get('room_name', 'Unknown Room')),
                'camera_entity_id': room_data.get('camera', room_data.get('camera_entity')),
                'personality_mode': self._map_v1_personality(room_data.get('mode', 'normal')),
                'update_frequency': room_data.get('check_interval', 60),
                'cleanliness_threshold': room_data.get('cleanliness_level', 75),
                'enabled': room_data.get('active', True),
                'v1_source': 'rooms_list'
            }
            processed_zones.append(processed_zone)
        
        return processed_zones
    
    def _process_v1_single_zone(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process v1.0 single zone configuration"""
        return {
            'name': config_data.get('zone_name', 'main_zone'),
            'display_name': config_data.get('display_name', config_data.get('zone_name', 'Main Zone')),
            'camera_entity_id': config_data.get('camera_entity', config_data.get('camera_entity_id')),
            'personality_mode': self._map_v1_personality(config_data.get('personality', 'normal')),
            'update_frequency': config_data.get('update_frequency', 60),
            'cleanliness_threshold': config_data.get('threshold', 75),
            'enabled': config_data.get('enabled', True),
            'v1_source': 'single_zone'
        }
    
    def _extract_zones_from_v1_db(self, db_path: Path) -> List[Dict[str, Any]]:
        """Extract zones from v1.0 database"""
        import sqlite3
        
        zones = []
        
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            
            # Try different v1.0 table structures
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            if 'zones' in tables:
                cursor = conn.execute("SELECT * FROM zones")
                for row in cursor.fetchall():
                    zones.append(self._convert_v1_db_zone(dict(row)))
            
            elif 'rooms' in tables:
                cursor = conn.execute("SELECT * FROM rooms")
                for row in cursor.fetchall():
                    zones.append(self._convert_v1_db_room(dict(row)))
            
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to extract from v1 database: {e}")
        
        return zones
    
    def _convert_v1_db_zone(self, zone_row: Dict[str, Any]) -> Dict[str, Any]:
        """Convert v1.0 database zone row to v2.0 format"""
        return {
            'name': zone_row.get('name', zone_row.get('zone_name', 'unknown')),
            'display_name': zone_row.get('display_name', zone_row.get('name', 'Unknown')),
            'camera_entity_id': zone_row.get('camera_entity_id', zone_row.get('camera_entity')),
            'personality_mode': self._map_v1_personality(zone_row.get('personality_mode', 'normal')),
            'update_frequency': zone_row.get('update_frequency', 60),
            'cleanliness_threshold': zone_row.get('cleanliness_threshold', 75),
            'enabled': bool(zone_row.get('enabled', 1)),
            'v1_source': 'database_zones'
        }
    
    def _convert_v1_db_room(self, room_row: Dict[str, Any]) -> Dict[str, Any]:
        """Convert v1.0 database room row to v2.0 format"""
        return {
            'name': room_row.get('room_name', room_row.get('name', 'unknown')),
            'display_name': room_row.get('display_name', room_row.get('room_name', 'Unknown')),
            'camera_entity_id': room_row.get('camera_entity', room_row.get('camera')),
            'personality_mode': self._map_v1_personality(room_row.get('mode', 'normal')),
            'update_frequency': room_row.get('check_interval', 60),
            'cleanliness_threshold': room_row.get('threshold', 75),
            'enabled': bool(room_row.get('active', 1)),
            'v1_source': 'database_rooms'
        }
    
    def _map_v1_personality(self, v1_personality: str) -> PersonalityMode:
        """Map v1.0 personality to v2.0 PersonalityMode"""
        return self.personality_mapping.get(v1_personality.lower(), PersonalityMode.CONCISE)
    
    def migrate_zones(self, v1_zones: List[Dict[str, Any]], 
                     auto_template_matching: bool = True) -> Dict[str, Any]:
        """Migrate v1.0 zones to v2.0 format"""
        migration_result = {
            'success': True,
            'migrated_zones': [],
            'failed_zones': [],
            'warnings': [],
            'template_matches': {}
        }
        
        for v1_zone in v1_zones:
            try:
                # Validate required fields
                if not v1_zone.get('camera_entity_id'):
                    migration_result['failed_zones'].append({
                        'zone': v1_zone,
                        'error': 'Missing camera_entity_id'
                    })
                    continue
                
                # Auto-match template if enabled
                template_match = None
                if auto_template_matching:
                    template_match = self._find_best_template_match(v1_zone)
                    if template_match:
                        migration_result['template_matches'][v1_zone['name']] = template_match
                
                # Create v2.0 zone
                v2_zone = self._create_v2_zone(v1_zone, template_match)
                
                # Save to database if repository is available
                if self.zone_repo:
                    zone_id = self.zone_repo.create_zone(v2_zone)
                    v2_zone.id = zone_id
                    
                    # Create default ignore rules if template matched
                    if template_match:
                        self._create_template_ignore_rules(zone_id, template_match)
                
                migration_result['migrated_zones'].append({
                    'v1_zone': v1_zone,
                    'v2_zone': v2_zone,
                    'template_used': template_match
                })
                
                self.logger.info(f"Migrated zone: {v1_zone['name']}")
                
            except Exception as e:
                migration_result['failed_zones'].append({
                    'zone': v1_zone,
                    'error': str(e)
                })
                self.logger.error(f"Failed to migrate zone {v1_zone.get('name', 'unknown')}: {e}")
        
        migration_result['success'] = len(migration_result['failed_zones']) == 0
        
        return migration_result
    
    def _find_best_template_match(self, v1_zone: Dict[str, Any]) -> Optional[str]:
        """Find the best template match for a v1.0 zone"""
        zone_name = v1_zone.get('name', '').lower()
        display_name = v1_zone.get('display_name', '').lower()
        
        # Simple keyword matching
        template_keywords = {
            'living_room': ['living', 'lounge', 'family', 'sitting'],
            'kitchen': ['kitchen', 'cook', 'dining'],
            'bedroom': ['bedroom', 'bed', 'sleep', 'master', 'guest'],
            'bathroom': ['bathroom', 'bath', 'toilet', 'washroom'],
            'office': ['office', 'study', 'work', 'desk'],
            'garage': ['garage', 'workshop', 'storage']
        }
        
        best_match = None
        best_score = 0
        
        for template_name, keywords in template_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in zone_name or keyword in display_name:
                    score += 1
            
            if score > best_score:
                best_score = score
                best_match = template_name
        
        return best_match if best_score > 0 else None
    
    def _create_v2_zone(self, v1_zone: Dict[str, Any], template_match: str = None) -> Zone:
        """Create a v2.0 Zone object from v1.0 data"""
        # Use template defaults if available
        template_config = {}
        if template_match:
            template_config = self.zone_templates.get_template(template_match)
        
        return Zone(
            name=v1_zone['name'],
            display_name=v1_zone.get('display_name', v1_zone['name']),
            camera_entity_id=v1_zone['camera_entity_id'],
            personality_mode=v1_zone.get('personality_mode', template_config.get('personality_mode', PersonalityMode.CONCISE)),
            enabled=v1_zone.get('enabled', True),
            notification_enabled=True,  # New in v2.0
            update_frequency=v1_zone.get('update_frequency', template_config.get('update_frequency', 60)),
            cleanliness_threshold=v1_zone.get('cleanliness_threshold', template_config.get('cleanliness_threshold', 75)),
            max_tasks_per_analysis=template_config.get('max_tasks_per_analysis', 10)  # New in v2.0
        )
    
    def _create_template_ignore_rules(self, zone_id: int, template_name: str):
        """Create ignore rules from template for migrated zone"""
        if not self.zone_repo:
            return
        
        template = self.zone_templates.get_template(template_name)
        ignore_patterns = template.get('ignore_patterns', [])
        
        for pattern in ignore_patterns:
            self.zone_repo.create_ignore_rule(zone_id, {
                'rule_type': 'contains',
                'rule_value': pattern,
                'rule_description': f'Auto-created during v1.0 migration from {template_name} template'
            })
    
    def create_migration_report(self, detection_result: Dict[str, Any], 
                               migration_result: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a comprehensive migration report"""
        report = {
            'migration_timestamp': datetime.now().isoformat(),
            'v1_detection': detection_result,
            'migration_summary': {
                'total_zones_found': len(detection_result.get('zones_found', [])),
                'migration_attempted': migration_result is not None,
                'zones_migrated': 0,
                'zones_failed': 0,
                'templates_matched': 0
            },
            'recommendations': [],
            'next_steps': []
        }
        
        if migration_result:
            report['migration_summary'].update({
                'zones_migrated': len(migration_result.get('migrated_zones', [])),
                'zones_failed': len(migration_result.get('failed_zones', [])),
                'templates_matched': len(migration_result.get('template_matches', {}))
            })
            
            report['migration_details'] = migration_result
        
        # Generate recommendations
        if detection_result['v1_detected'] and not migration_result:
            report['recommendations'].append("Run migration to upgrade to v2.0 multi-zone system")
        
        if migration_result and migration_result.get('failed_zones'):
            report['recommendations'].append("Review failed zone migrations and fix configuration issues")
        
        # Generate next steps
        if migration_result and migration_result['success']:
            report['next_steps'] = [
                "Review migrated zone configurations",
                "Test camera entity IDs are working",
                "Customize zone settings as needed",
                "Set up notification preferences",
                "Create additional ignore rules if needed"
            ]
        
        return report
    
    def backup_v1_configuration(self, config_path: str = "/data") -> str:
        """Create a backup of v1.0 configuration before migration"""
        config_path = Path(config_path)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = config_path / f"v1_backup_{timestamp}.tar.gz"
        
        import tarfile
        
        with tarfile.open(backup_path, 'w:gz') as tar:
            # Backup configuration files
            for pattern in ['*.yaml', '*.json', '*.db']:
                for file_path in config_path.glob(pattern):
                    if file_path.is_file():
                        tar.add(file_path, arcname=file_path.name)
        
        self.logger.info(f"v1.0 configuration backup created: {backup_path}")
        return str(backup_path)
