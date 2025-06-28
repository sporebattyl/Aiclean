"""
Test configuration fixtures
"""
from typing import Dict, Any, List


def get_valid_zone_config() -> Dict[str, Any]:
    """Get a valid zone configuration for testing"""
    return {
        'name': 'Kitchen',
        'icon': 'mdi:chef-hat',
        'purpose': 'Keep everything Tidy and Clean',
        'camera_entity': 'camera.kitchen',
        'todo_list_entity': 'todo.kitchen_tasks',
        'update_frequency': 24,
        'notifications_enabled': True,
        'notification_service': 'notify.mobile_app',
        'notification_personality': 'default',
        'notify_on_create': True,
        'notify_on_complete': True
    }


def get_minimal_zone_config() -> Dict[str, Any]:
    """Get a minimal valid zone configuration"""
    return {
        'name': 'Living Room',
        'icon': 'mdi:sofa',
        'purpose': 'Keep tidy',
        'camera_entity': 'camera.living_room',
        'todo_list_entity': 'todo.living_room_tasks',
        'update_frequency': 12,
        'notifications_enabled': False,
        'notification_service': '',
        'notification_personality': 'default',
        'notify_on_create': False,
        'notify_on_complete': False
    }


def get_invalid_zone_configs() -> List[Dict[str, Any]]:
    """Get various invalid zone configurations for error testing"""
    return [
        # Missing required name
        {
            'icon': 'mdi:chef-hat',
            'purpose': 'Keep clean',
            'camera_entity': 'camera.kitchen',
            'todo_list_entity': 'todo.kitchen_tasks',
            'update_frequency': 24,
            'notifications_enabled': True,
            'notification_service': 'notify.mobile_app',
            'notification_personality': 'default',
            'notify_on_create': True,
            'notify_on_complete': True
        },
        # Missing camera entity
        {
            'name': 'Kitchen',
            'icon': 'mdi:chef-hat',
            'purpose': 'Keep clean',
            'todo_list_entity': 'todo.kitchen_tasks',
            'update_frequency': 24,
            'notifications_enabled': True,
            'notification_service': 'notify.mobile_app',
            'notification_personality': 'default',
            'notify_on_create': True,
            'notify_on_complete': True
        },
        # Invalid update frequency
        {
            'name': 'Kitchen',
            'icon': 'mdi:chef-hat',
            'purpose': 'Keep clean',
            'camera_entity': 'camera.kitchen',
            'todo_list_entity': 'todo.kitchen_tasks',
            'update_frequency': 0,  # Invalid: must be >= 1
            'notifications_enabled': True,
            'notification_service': 'notify.mobile_app',
            'notification_personality': 'default',
            'notify_on_create': True,
            'notify_on_complete': True
        },
        # Invalid notification personality
        {
            'name': 'Kitchen',
            'icon': 'mdi:chef-hat',
            'purpose': 'Keep clean',
            'camera_entity': 'camera.kitchen',
            'todo_list_entity': 'todo.kitchen_tasks',
            'update_frequency': 24,
            'notifications_enabled': True,
            'notification_service': 'notify.mobile_app',
            'notification_personality': 'invalid_personality',
            'notify_on_create': True,
            'notify_on_complete': True
        }
    ]


def get_valid_aicleaner_config() -> Dict[str, Any]:
    """Get a valid AICleaner configuration for testing"""
    return {
        'gemini_api_key': 'test_api_key_123',
        'display_name': 'Test User',
        'zones': [
            get_valid_zone_config(),
            get_minimal_zone_config()
        ]
    }


def get_addon_environment_config() -> Dict[str, str]:
    """Get environment variables for addon environment testing"""
    return {
        'SUPERVISOR_TOKEN': 'test_supervisor_token',
        'GEMINI_API_KEY': 'test_gemini_key',
        'DISPLAY_NAME': 'Test User',
        # Zone configurations would be loaded from /data/options.json in real addon
    }


def get_local_development_config() -> Dict[str, Any]:
    """Get configuration for local development testing"""
    return {
        'home_assistant': {
            'api_url': 'http://localhost:8123/api',
            'token': 'test_local_token',
        },
        'google_gemini': {
            'api_key': 'test_local_gemini_key'
        },
        'zones': [get_valid_zone_config()]
    }


def get_multi_zone_config() -> Dict[str, Any]:
    """Get configuration with multiple zones for testing"""
    return {
        'gemini_api_key': 'test_api_key_123',
        'display_name': 'Test User',
        'zones': [
            {
                'name': 'Kitchen',
                'icon': 'mdi:chef-hat',
                'purpose': 'Keep everything Tidy and Clean',
                'camera_entity': 'camera.kitchen',
                'todo_list_entity': 'todo.kitchen_tasks',
                'update_frequency': 24,
                'notifications_enabled': True,
                'notification_service': 'notify.mobile_app',
                'notification_personality': 'snarky',
                'notify_on_create': True,
                'notify_on_complete': True
            },
            {
                'name': 'Living Room',
                'icon': 'mdi:sofa',
                'purpose': 'Keep tidy and organized',
                'camera_entity': 'camera.living_room',
                'todo_list_entity': 'todo.living_room_tasks',
                'update_frequency': 12,
                'notifications_enabled': True,
                'notification_service': 'notify.mobile_app',
                'notification_personality': 'jarvis',
                'notify_on_create': False,
                'notify_on_complete': True
            },
            {
                'name': 'Bedroom',
                'icon': 'mdi:bed',
                'purpose': 'Keep peaceful and clean',
                'camera_entity': 'camera.bedroom',
                'todo_list_entity': 'todo.bedroom_tasks',
                'update_frequency': 48,
                'notifications_enabled': False,
                'notification_service': '',
                'notification_personality': 'default',
                'notify_on_create': False,
                'notify_on_complete': False
            }
        ]
    }


# Phase 2 Enhanced State Management Fixtures

def get_empty_zone_state():
    """Returns an empty zone state for testing"""
    return {
        'tasks': [],
        'ignore_rules': []
    }

def get_zone_with_duplicate_tasks():
    """Returns zone state with duplicate/similar tasks for testing merge functionality"""
    return {
        'tasks': [
            {
                'id': 'task_1687392000_kitchen_0',
                'description': 'Clean the countertops',
                'status': 'active',
                'created_at': '2023-06-21T20:00:00Z',
                'priority': 5
            },
            {
                'id': 'task_1687392060_kitchen_1',
                'description': 'Wipe down the counters',  # Similar to above
                'status': 'active',
                'created_at': '2023-06-21T20:01:00Z',
                'priority': 4
            },
            {
                'id': 'task_1687392120_kitchen_2',
                'description': 'Clean kitchen countertops',  # Similar to first
                'status': 'active',
                'created_at': '2023-06-21T20:02:00Z',
                'priority': 6
            },
            {
                'id': 'task_1687392180_kitchen_3',
                'description': 'Organize spice rack',  # Unique task
                'status': 'active',
                'created_at': '2023-06-21T20:03:00Z',
                'priority': 3
            }
        ]
    }


def get_zone_with_old_tasks():
    """Returns zone state with tasks of various ages for testing expiration"""
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)
    old_date = now - timedelta(days=10)
    recent_date = now - timedelta(days=2)

    return {
        'tasks': [
            {
                'id': 'task_old_1',
                'description': 'Old task that should expire',
                'status': 'active',
                'created_at': old_date.isoformat(),
                'priority': 5
            },
            {
                'id': 'task_old_2',
                'description': 'Another old task',
                'status': 'active',
                'created_at': old_date.isoformat(),
                'priority': 3
            },
            {
                'id': 'task_recent_1',
                'description': 'Recent task that should stay active',
                'status': 'active',
                'created_at': recent_date.isoformat(),
                'priority': 7
            }
        ]
    }


def get_zone_with_task_history():
    """Returns zone state with task completion history for context-aware generation"""
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)

    return {
        'tasks': [
            {
                'id': 'task_completed_1',
                'description': 'Cleaned stovetop after cooking pasta',
                'status': 'completed',
                'created_at': (now - timedelta(days=1)).isoformat(),
                'completed_at': (now - timedelta(hours=23)).isoformat(),
                'priority': 8
            },
            {
                'id': 'task_completed_2',
                'description': 'Put away cooking utensils',
                'status': 'completed',
                'created_at': (now - timedelta(days=2)).isoformat(),
                'completed_at': (now - timedelta(days=1, hours=12)).isoformat(),
                'priority': 5
            },
            {
                'id': 'task_active_1',
                'description': 'Wipe down cutting board',
                'status': 'active',
                'created_at': (now - timedelta(hours=2)).isoformat(),
                'priority': 6
            }
        ],
        'completion_patterns': {
            'cooking_related': 0.85,
            'organization': 0.70,
            'cleaning': 0.90
        }
    }


def get_zone_with_performance_history():
    """Returns zone state with performance metrics data"""
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)

    return {
        'tasks': [
            {
                'id': 'task_perf_1',
                'description': 'Task completed quickly',
                'status': 'completed',
                'created_at': (now - timedelta(days=1)).isoformat(),
                'completed_at': (now - timedelta(days=1) + timedelta(hours=2)).isoformat(),
                'priority': 5
            },
            {
                'id': 'task_perf_2',
                'description': 'Task completed slowly',
                'status': 'completed',
                'created_at': (now - timedelta(days=3)).isoformat(),
                'completed_at': (now - timedelta(days=1)).isoformat(),
                'priority': 3
            },
            {
                'id': 'task_perf_3',
                'description': 'Active task',
                'status': 'active',
                'created_at': (now - timedelta(hours=4)).isoformat(),
                'priority': 7
            }
        ],
        'performance_metrics': {
            'total_tasks_created': 15,
            'total_tasks_completed': 12,
            'average_completion_time_hours': 18.5,
            'last_updated': now.isoformat()
        }
    }


def get_zone_with_related_tasks():
    """Returns zone state with tasks that have logical dependencies"""
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)

    return {
        'tasks': [
            {
                'id': 'task_clear_counter',
                'description': 'Clear items from countertop',
                'status': 'active',
                'created_at': now.isoformat(),
                'priority': 7
            },
            {
                'id': 'task_wipe_counter',
                'description': 'Wipe down countertop',
                'status': 'active',
                'created_at': now.isoformat(),
                'priority': 6
            },
            {
                'id': 'task_load_dishwasher',
                'description': 'Load dirty dishes into dishwasher',
                'status': 'active',
                'created_at': now.isoformat(),
                'priority': 5
            },
            {
                'id': 'task_start_dishwasher',
                'description': 'Start dishwasher cycle',
                'status': 'active',
                'created_at': now.isoformat(),
                'priority': 4
            }
        ]
    }


def get_zone_with_mixed_priority_tasks():
    """Returns zone state with tasks of various priorities for scheduling optimization"""
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)

    return {
        'tasks': [
            {
                'id': 'task_low_priority',
                'description': 'Organize bookshelf',
                'status': 'active',
                'created_at': now.isoformat(),
                'priority': 2
            },
            {
                'id': 'task_high_priority',
                'description': 'Clean up spilled liquid on floor',
                'status': 'active',
                'created_at': now.isoformat(),
                'priority': 9
            },
            {
                'id': 'task_medium_priority',
                'description': 'Wipe down surfaces',
                'status': 'active',
                'created_at': now.isoformat(),
                'priority': 5
            },
            {
                'id': 'task_urgent',
                'description': 'Turn off stove burner',
                'status': 'active',
                'created_at': now.isoformat(),
                'priority': 10
            }
        ]
    }


def get_zone_with_analytics_data():
    """Returns zone state with analytics data for insights generation"""
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)

    return {
        'tasks': [
            {
                'id': 'task_analytics_1',
                'description': 'Wipe down counters',
                'status': 'completed',
                'created_at': (now - timedelta(days=1)).isoformat(),
                'completed_at': (now - timedelta(hours=20)).isoformat(),
                'priority': 6,
                'completion_time_minutes': 15
            },
            {
                'id': 'task_analytics_2',
                'description': 'Load dishwasher',
                'status': 'completed',
                'created_at': (now - timedelta(days=2)).isoformat(),
                'completed_at': (now - timedelta(days=1, hours=18)).isoformat(),
                'priority': 5,
                'completion_time_minutes': 10
            }
        ],
        'analytics': {
            'task_frequency': {
                'wipe counters': 5,
                'load dishwasher': 3,
                'organize items': 2
            },
            'completion_times': {
                'cleaning': 15.5,
                'organization': 25.0,
                'maintenance': 8.0
            },
            'peak_hours': [8, 18, 20]  # 8am, 6pm, 8pm
        }
    }


def get_zone_with_learning_data():
    """Returns zone state with learning data for adaptive improvements"""
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)

    return {
        'tasks': [
            {
                'id': 'task_learning_1',
                'description': 'Organize magazines',
                'status': 'dismissed',  # Frequently dismissed task
                'created_at': (now - timedelta(days=1)).isoformat(),
                'dismissed_at': (now - timedelta(hours=20)).isoformat(),
                'priority': 3,
                'dismissal_count': 5
            },
            {
                'id': 'task_learning_2',
                'description': 'Clean coffee maker',
                'status': 'completed',
                'created_at': (now - timedelta(days=2)).isoformat(),
                'completed_at': (now - timedelta(days=1)).isoformat(),
                'priority': 7,
                'completion_time_minutes': 5  # Completed very quickly
            }
        ],
        'learning_data': {
            'frequently_dismissed': [
                'organize magazines',
                'dust decorative items',
                'arrange throw pillows'
            ],
            'quickly_completed': [
                'clean coffee maker',
                'wipe down sink',
                'put away items'
            ],
            'user_preferences': {
                'prefers_cleaning_over_organizing': 0.8,
                'responds_well_to_urgent_tasks': 0.9,
                'dismisses_low_priority_tasks': 0.6
            }
        }
    }
