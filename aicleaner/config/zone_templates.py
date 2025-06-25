"""
Zone Templates - Pre-configured zone templates for common room types
"""
from typing import Dict, Any, List
from ..data.models import PersonalityMode


class ZoneTemplates:
    """Provides pre-configured templates for common zone types"""
    
    def __init__(self):
        self.templates = self._initialize_templates()
    
    def _initialize_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize zone templates for common room types"""
        return {
            'living_room': {
                'display_name': 'Living Room',
                'description': 'Main living area with seating and entertainment',
                'personality_mode': PersonalityMode.ENCOURAGING,
                'update_frequency': 60,
                'cleanliness_threshold': 75,
                'max_tasks_per_analysis': 8,
                'common_tasks': [
                    'Arrange throw pillows on couch',
                    'Fold and put away blankets',
                    'Clear coffee table surface',
                    'Organize remote controls',
                    'Vacuum or sweep floor',
                    'Dust entertainment center',
                    'Organize books and magazines'
                ],
                'ignore_patterns': [
                    'pet toys',
                    'charging cables',
                    'decorative items'
                ],
                'optimal_settings': {
                    'analysis_sensitivity': 'medium',
                    'task_priority_weights': {
                        'surface_clutter': 0.8,
                        'floor_items': 0.9,
                        'furniture_arrangement': 0.6
                    }
                }
            },
            
            'kitchen': {
                'display_name': 'Kitchen',
                'description': 'Cooking and food preparation area',
                'personality_mode': PersonalityMode.SNARKY,
                'update_frequency': 45,
                'cleanliness_threshold': 80,
                'max_tasks_per_analysis': 10,
                'common_tasks': [
                    'Put dishes in dishwasher',
                    'Wipe down countertops',
                    'Clear sink of dishes',
                    'Put away items on counter',
                    'Clean stovetop',
                    'Organize spice rack',
                    'Empty trash if full',
                    'Put away clean dishes'
                ],
                'ignore_patterns': [
                    'coffee maker',
                    'toaster',
                    'knife block',
                    'fruit bowl'
                ],
                'optimal_settings': {
                    'analysis_sensitivity': 'high',
                    'task_priority_weights': {
                        'dirty_dishes': 1.0,
                        'counter_clutter': 0.9,
                        'appliance_cleanliness': 0.7
                    }
                }
            },
            
            'bedroom': {
                'display_name': 'Bedroom',
                'description': 'Sleeping and personal space',
                'personality_mode': PersonalityMode.CONCISE,
                'update_frequency': 90,
                'cleanliness_threshold': 70,
                'max_tasks_per_analysis': 6,
                'common_tasks': [
                    'Make the bed',
                    'Put clothes in hamper or closet',
                    'Clear nightstand surfaces',
                    'Organize dresser top',
                    'Put shoes in proper place',
                    'Hang up clothes'
                ],
                'ignore_patterns': [
                    'alarm clock',
                    'phone charger',
                    'reading materials',
                    'water glass'
                ],
                'optimal_settings': {
                    'analysis_sensitivity': 'medium',
                    'task_priority_weights': {
                        'bed_making': 0.8,
                        'clothing_organization': 0.9,
                        'surface_clearing': 0.6
                    }
                }
            },
            
            'bathroom': {
                'display_name': 'Bathroom',
                'description': 'Personal hygiene and grooming area',
                'personality_mode': PersonalityMode.ENCOURAGING,
                'update_frequency': 30,
                'cleanliness_threshold': 85,
                'max_tasks_per_analysis': 8,
                'common_tasks': [
                    'Put toiletries back in place',
                    'Hang up towels properly',
                    'Clear counter surfaces',
                    'Put dirty clothes in hamper',
                    'Replace toilet paper if needed',
                    'Organize medicine cabinet',
                    'Clean sink area',
                    'Empty wastebasket if full'
                ],
                'ignore_patterns': [
                    'toothbrush holder',
                    'soap dispenser',
                    'toilet brush',
                    'scale'
                ],
                'optimal_settings': {
                    'analysis_sensitivity': 'high',
                    'task_priority_weights': {
                        'hygiene_items': 0.9,
                        'towel_organization': 0.8,
                        'counter_cleanliness': 0.9
                    }
                }
            },
            
            'office': {
                'display_name': 'Home Office',
                'description': 'Work and study space',
                'personality_mode': PersonalityMode.CONCISE,
                'update_frequency': 120,
                'cleanliness_threshold': 75,
                'max_tasks_per_analysis': 7,
                'common_tasks': [
                    'Organize desk surface',
                    'File or organize papers',
                    'Put away office supplies',
                    'Organize computer cables',
                    'Clear chair of items',
                    'Organize bookshelf',
                    'Empty trash bin'
                ],
                'ignore_patterns': [
                    'computer equipment',
                    'desk lamp',
                    'office chair',
                    'filing cabinet'
                ],
                'optimal_settings': {
                    'analysis_sensitivity': 'medium',
                    'task_priority_weights': {
                        'desk_organization': 0.9,
                        'paper_management': 0.8,
                        'supply_organization': 0.7
                    }
                }
            },
            
            'dining_room': {
                'display_name': 'Dining Room',
                'description': 'Formal dining and entertaining space',
                'personality_mode': PersonalityMode.ENCOURAGING,
                'update_frequency': 180,
                'cleanliness_threshold': 70,
                'max_tasks_per_analysis': 5,
                'common_tasks': [
                    'Clear dining table surface',
                    'Push in dining chairs',
                    'Organize sideboard or buffet',
                    'Put away serving items',
                    'Dust dining table'
                ],
                'ignore_patterns': [
                    'centerpiece',
                    'placemats',
                    'candles',
                    'decorative items'
                ],
                'optimal_settings': {
                    'analysis_sensitivity': 'low',
                    'task_priority_weights': {
                        'table_clearing': 0.8,
                        'chair_arrangement': 0.6,
                        'surface_organization': 0.7
                    }
                }
            },
            
            'laundry_room': {
                'display_name': 'Laundry Room',
                'description': 'Washing and clothing care area',
                'personality_mode': PersonalityMode.SNARKY,
                'update_frequency': 60,
                'cleanliness_threshold': 75,
                'max_tasks_per_analysis': 8,
                'common_tasks': [
                    'Move clothes from washer to dryer',
                    'Fold and put away clean clothes',
                    'Sort dirty laundry',
                    'Clear folding surface',
                    'Organize laundry supplies',
                    'Empty lint trap',
                    'Put away cleaning supplies'
                ],
                'ignore_patterns': [
                    'washing machine',
                    'dryer',
                    'laundry basket',
                    'detergent bottles'
                ],
                'optimal_settings': {
                    'analysis_sensitivity': 'medium',
                    'task_priority_weights': {
                        'clothing_management': 0.9,
                        'surface_clearing': 0.8,
                        'supply_organization': 0.6
                    }
                }
            },
            
            'garage': {
                'display_name': 'Garage',
                'description': 'Storage and vehicle parking area',
                'personality_mode': PersonalityMode.CONCISE,
                'update_frequency': 240,
                'cleanliness_threshold': 60,
                'max_tasks_per_analysis': 6,
                'common_tasks': [
                    'Put tools back in place',
                    'Organize storage shelves',
                    'Clear walkways',
                    'Organize sports equipment',
                    'Put away seasonal items',
                    'Organize workbench'
                ],
                'ignore_patterns': [
                    'vehicles',
                    'large appliances',
                    'storage cabinets',
                    'garage door opener'
                ],
                'optimal_settings': {
                    'analysis_sensitivity': 'low',
                    'task_priority_weights': {
                        'tool_organization': 0.8,
                        'walkway_clearing': 0.9,
                        'storage_organization': 0.7
                    }
                }
            }
        }
    
    def get_template(self, template_name: str) -> Dict[str, Any]:
        """Get a specific zone template"""
        return self.templates.get(template_name, {})
    
    def get_all_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get all available templates"""
        return self.templates.copy()
    
    def get_template_names(self) -> List[str]:
        """Get list of available template names"""
        return list(self.templates.keys())
    
    def get_templates_by_personality(self, personality: PersonalityMode) -> Dict[str, Dict[str, Any]]:
        """Get templates filtered by personality mode"""
        return {
            name: template for name, template in self.templates.items()
            if template.get('personality_mode') == personality
        }
    
    def create_zone_from_template(self, template_name: str, zone_name: str, 
                                 camera_entity_id: str, overrides: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a zone configuration from a template"""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        # Start with template
        zone_config = template.copy()
        
        # Set required fields
        zone_config.update({
            'name': zone_name,
            'camera_entity_id': camera_entity_id,
            'enabled': True,
            'notification_enabled': True
        })
        
        # Apply any overrides
        if overrides:
            zone_config.update(overrides)
        
        return zone_config
    
    def get_template_recommendations(self, room_type_hint: str = None) -> List[Dict[str, Any]]:
        """Get template recommendations based on room type hint"""
        recommendations = []
        
        if room_type_hint:
            # Fuzzy matching for room type
            hint_lower = room_type_hint.lower()
            for name, template in self.templates.items():
                if (hint_lower in name.lower() or 
                    hint_lower in template.get('display_name', '').lower() or
                    hint_lower in template.get('description', '').lower()):
                    
                    recommendations.append({
                        'template_name': name,
                        'display_name': template['display_name'],
                        'description': template['description'],
                        'personality': template['personality_mode'].value,
                        'match_score': self._calculate_match_score(hint_lower, name, template)
                    })
        
        # Sort by match score
        recommendations.sort(key=lambda x: x['match_score'], reverse=True)
        
        # If no specific recommendations, return popular templates
        if not recommendations:
            popular_templates = ['living_room', 'kitchen', 'bedroom', 'bathroom']
            for template_name in popular_templates:
                template = self.templates[template_name]
                recommendations.append({
                    'template_name': template_name,
                    'display_name': template['display_name'],
                    'description': template['description'],
                    'personality': template['personality_mode'].value,
                    'match_score': 0.5
                })
        
        return recommendations[:5]  # Return top 5
    
    def _calculate_match_score(self, hint: str, template_name: str, template: Dict[str, Any]) -> float:
        """Calculate match score for template recommendation"""
        score = 0.0
        
        # Exact name match
        if hint == template_name:
            score += 1.0
        elif hint in template_name:
            score += 0.8
        
        # Display name match
        display_name = template.get('display_name', '').lower()
        if hint in display_name:
            score += 0.6
        
        # Description match
        description = template.get('description', '').lower()
        if hint in description:
            score += 0.4
        
        # Common task match
        common_tasks = template.get('common_tasks', [])
        for task in common_tasks:
            if hint in task.lower():
                score += 0.2
                break
        
        return min(score, 1.0)  # Cap at 1.0
    
    def validate_template(self, template: Dict[str, Any]) -> List[str]:
        """Validate a template configuration"""
        errors = []
        
        required_fields = [
            'display_name', 'personality_mode', 'update_frequency',
            'cleanliness_threshold', 'max_tasks_per_analysis'
        ]
        
        for field in required_fields:
            if field not in template:
                errors.append(f"Missing required field: {field}")
        
        # Validate personality mode
        if 'personality_mode' in template:
            if not isinstance(template['personality_mode'], PersonalityMode):
                errors.append("personality_mode must be a PersonalityMode enum")
        
        # Validate numeric ranges
        if 'update_frequency' in template:
            if not isinstance(template['update_frequency'], int) or template['update_frequency'] < 1:
                errors.append("update_frequency must be a positive integer")
        
        if 'cleanliness_threshold' in template:
            threshold = template['cleanliness_threshold']
            if not isinstance(threshold, int) or not 0 <= threshold <= 100:
                errors.append("cleanliness_threshold must be an integer between 0 and 100")
        
        if 'max_tasks_per_analysis' in template:
            max_tasks = template['max_tasks_per_analysis']
            if not isinstance(max_tasks, int) or max_tasks < 1:
                errors.append("max_tasks_per_analysis must be a positive integer")
        
        return errors
