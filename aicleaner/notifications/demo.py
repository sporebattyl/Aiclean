"""
Notification System Demo - Showcases all personality modes and notification types
"""
import json
from typing import Dict, Any
from ..data.models import Zone, PersonalityMode, NotificationType
from .personalities import PersonalityEngine
from .templates import TemplateManager
from .engine import NotificationEngine


class NotificationDemo:
    """Demonstrates the notification system capabilities"""
    
    def __init__(self):
        self.personality_engine = PersonalityEngine()
        self.template_manager = TemplateManager()
        
        # Create sample zones for demo
        self.sample_zones = {
            'living_room': Zone(
                id=1,
                name='living_room',
                display_name='Living Room',
                camera_entity_id='camera.living_room',
                personality_mode=PersonalityMode.ENCOURAGING
            ),
            'kitchen': Zone(
                id=2,
                name='kitchen',
                display_name='Kitchen',
                camera_entity_id='camera.kitchen',
                personality_mode=PersonalityMode.SNARKY
            ),
            'bedroom': Zone(
                id=3,
                name='bedroom',
                display_name='Bedroom',
                camera_entity_id='camera.bedroom',
                personality_mode=PersonalityMode.CONCISE
            )
        }
    
    def demo_all_personalities(self) -> Dict[str, Any]:
        """Demonstrate all personality modes with different scenarios"""
        demo_results = {}
        
        for personality in PersonalityMode:
            demo_results[personality.value] = {
                'description': self.personality_engine.get_personality_description(personality),
                'examples': self.personality_engine.preview_personality(personality, "Living Room")
            }
        
        return demo_results
    
    def demo_task_reminders(self) -> Dict[str, Any]:
        """Demonstrate task reminder notifications for different scenarios"""
        scenarios = [
            {'zone': 'living_room', 'task_count': 3, 'score': 65, 'scenario': 'moderate_mess'},
            {'zone': 'kitchen', 'task_count': 7, 'score': 45, 'scenario': 'high_mess'},
            {'zone': 'bedroom', 'task_count': 1, 'score': 85, 'scenario': 'light_mess'}
        ]
        
        results = {}
        
        for scenario in scenarios:
            zone = self.sample_zones[scenario['zone']]
            
            # Generate personality message
            message = self.personality_engine.generate_task_reminder(
                zone, scenario['task_count'], scenario['score']
            )
            
            # Format complete notification
            notification = self.template_manager.format_notification(
                NotificationType.TASK_REMINDER,
                message,
                zone.display_name,
                zone.personality_mode,
                {
                    'task_count': scenario['task_count'],
                    'score': scenario['score']
                }
            )
            
            results[f"{scenario['zone']}_{scenario['scenario']}"] = {
                'zone': zone.display_name,
                'personality': zone.personality_mode.value,
                'scenario': scenario['scenario'],
                'raw_message': message,
                'formatted_notification': notification
            }
        
        return results
    
    def demo_completion_celebrations(self) -> Dict[str, Any]:
        """Demonstrate completion celebration notifications"""
        scenarios = [
            {'zone': 'living_room', 'score': 95, 'scenario': 'perfect_clean'},
            {'zone': 'kitchen', 'score': 87, 'scenario': 'excellent_clean'},
            {'zone': 'bedroom', 'score': 78, 'scenario': 'good_clean'}
        ]
        
        results = {}
        
        for scenario in scenarios:
            zone = self.sample_zones[scenario['zone']]
            
            message = self.personality_engine.generate_completion_celebration(
                zone, scenario['score']
            )
            
            notification = self.template_manager.format_notification(
                NotificationType.COMPLETION_CELEBRATION,
                message,
                zone.display_name,
                zone.personality_mode,
                {
                    'score': scenario['score']
                }
            )
            
            results[f"{scenario['zone']}_{scenario['scenario']}"] = {
                'zone': zone.display_name,
                'personality': zone.personality_mode.value,
                'scenario': scenario['scenario'],
                'raw_message': message,
                'formatted_notification': notification
            }
        
        return results
    
    def demo_streak_milestones(self) -> Dict[str, Any]:
        """Demonstrate streak milestone notifications"""
        milestones = [3, 7, 14, 30]
        results = {}
        
        for milestone in milestones:
            for zone_name, zone in self.sample_zones.items():
                message = self.personality_engine.generate_streak_milestone(zone, milestone)
                
                notification = self.template_manager.format_notification(
                    NotificationType.STREAK_MILESTONE,
                    message,
                    zone.display_name,
                    zone.personality_mode,
                    {
                        'streak_days': milestone
                    }
                )
                
                results[f"{zone_name}_{milestone}_days"] = {
                    'zone': zone.display_name,
                    'personality': zone.personality_mode.value,
                    'milestone': milestone,
                    'raw_message': message,
                    'formatted_notification': notification
                }
        
        return results
    
    def demo_error_notifications(self) -> Dict[str, Any]:
        """Demonstrate error notification handling"""
        error_scenarios = [
            {'error': 'Camera connection timeout', 'type': 'connection_error'},
            {'error': 'Gemini API rate limit exceeded', 'type': 'ai_error'},
            {'error': 'Camera entity not found', 'type': 'camera_error'},
            {'error': 'Authentication failed', 'type': 'auth_error'}
        ]
        
        results = {}
        
        for error_scenario in error_scenarios:
            for zone_name, zone in self.sample_zones.items():
                message = self.personality_engine.generate_analysis_error(
                    zone, error_scenario['error']
                )
                
                notification = self.template_manager.format_notification(
                    NotificationType.ANALYSIS_ERROR,
                    message,
                    zone.display_name,
                    zone.personality_mode,
                    {
                        'error_message': error_scenario['error'],
                        'error_type': error_scenario['type']
                    }
                )
                
                results[f"{zone_name}_{error_scenario['type']}"] = {
                    'zone': zone.display_name,
                    'personality': zone.personality_mode.value,
                    'error_type': error_scenario['type'],
                    'raw_message': message,
                    'formatted_notification': notification
                }
        
        return results
    
    def demo_auto_completion(self) -> Dict[str, Any]:
        """Demonstrate auto-completion notifications"""
        scenarios = [
            {
                'zone': 'living_room',
                'completed_tasks': ['Pick up the throw pillows', 'Fold the blanket on the couch'],
                'scenario': 'light_auto_completion'
            },
            {
                'zone': 'kitchen',
                'completed_tasks': [
                    'Put away the dishes on the counter',
                    'Wipe down the coffee maker',
                    'Close the cabinet doors',
                    'Put the cutting board away'
                ],
                'scenario': 'heavy_auto_completion'
            }
        ]
        
        results = {}
        
        for scenario in scenarios:
            zone = self.sample_zones[scenario['zone']]
            
            message = self.personality_engine.generate_auto_completion(
                zone, len(scenario['completed_tasks']), scenario['completed_tasks']
            )
            
            notification = self.template_manager.format_notification(
                NotificationType.COMPLETION_CELEBRATION,
                message,
                zone.display_name,
                zone.personality_mode,
                {
                    'task_count': len(scenario['completed_tasks']),
                    'completed_tasks': scenario['completed_tasks'],
                    'auto_completed': True
                }
            )
            
            results[f"{scenario['zone']}_{scenario['scenario']}"] = {
                'zone': zone.display_name,
                'personality': zone.personality_mode.value,
                'scenario': scenario['scenario'],
                'completed_tasks': scenario['completed_tasks'],
                'raw_message': message,
                'formatted_notification': notification
            }
        
        return results
    
    def demo_summary_notifications(self) -> Dict[str, Any]:
        """Demonstrate summary notifications for multiple zones"""
        zones_data = [
            {'zone_name': 'Living Room', 'score': 85, 'task_count': 2, 'threshold': 70},
            {'zone_name': 'Kitchen', 'score': 65, 'task_count': 4, 'threshold': 70},
            {'zone_name': 'Bedroom', 'score': 92, 'task_count': 0, 'threshold': 70}
        ]
        
        results = {}
        
        for personality in PersonalityMode:
            notification = self.template_manager.create_summary_notification(zones_data, personality)
            
            results[personality.value] = {
                'personality': personality.value,
                'zones_data': zones_data,
                'notification': notification
            }
        
        return results
    
    def generate_full_demo(self) -> Dict[str, Any]:
        """Generate a complete demonstration of all notification features"""
        return {
            'personality_overview': self.demo_all_personalities(),
            'task_reminders': self.demo_task_reminders(),
            'completion_celebrations': self.demo_completion_celebrations(),
            'streak_milestones': self.demo_streak_milestones(),
            'error_notifications': self.demo_error_notifications(),
            'auto_completion': self.demo_auto_completion(),
            'summary_notifications': self.demo_summary_notifications()
        }
    
    def print_demo_summary(self):
        """Print a formatted summary of the notification system"""
        print("🤖 Roo AI Cleaning Assistant v2.0 - Notification System Demo")
        print("=" * 60)
        
        print("\n📢 Personality Modes:")
        for personality in PersonalityMode:
            description = self.personality_engine.get_personality_description(personality)
            print(f"  • {personality.value.title()}: {description}")
        
        print("\n🔔 Notification Types:")
        notification_types = [
            ("Task Reminder", "Alerts when tasks need attention"),
            ("Completion Celebration", "Celebrates when zones are cleaned"),
            ("Streak Milestone", "Recognizes consecutive clean days"),
            ("Analysis Error", "Reports technical issues"),
            ("Auto-Completion", "Confirms automatically completed tasks")
        ]
        
        for name, description in notification_types:
            print(f"  • {name}: {description}")
        
        print("\n🎯 Sample Messages:")
        
        # Show one example from each personality for task reminders
        living_room = self.sample_zones['living_room']
        kitchen = self.sample_zones['kitchen']
        bedroom = self.sample_zones['bedroom']
        
        print(f"\n  Encouraging ({living_room.display_name}):")
        print(f"    '{self.personality_engine.generate_task_reminder(living_room, 3, 65)}'")
        
        print(f"\n  Snarky ({kitchen.display_name}):")
        print(f"    '{self.personality_engine.generate_task_reminder(kitchen, 5, 45)}'")
        
        print(f"\n  Concise ({bedroom.display_name}):")
        print(f"    '{self.personality_engine.generate_task_reminder(bedroom, 1, 85)}'")
        
        print("\n✨ Features:")
        features = [
            "🎭 Three distinct personality modes",
            "⏰ Smart frequency management with quiet hours",
            "📱 Multiple delivery methods (persistent, mobile)",
            "📊 Complete notification history and analytics",
            "🎯 Context-aware message generation",
            "🔄 Auto-completion notifications",
            "📈 Streak milestone celebrations",
            "⚠️ Intelligent error reporting"
        ]
        
        for feature in features:
            print(f"  {feature}")
        
        print("\n" + "=" * 60)
        print("Ready to make cleaning fun and engaging! 🧹✨")


if __name__ == "__main__":
    demo = NotificationDemo()
    demo.print_demo_summary()
    
    # Generate and save full demo data
    full_demo = demo.generate_full_demo()
    with open('notification_demo_output.json', 'w') as f:
        json.dump(full_demo, f, indent=2, default=str)
