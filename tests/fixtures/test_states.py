"""
Test state fixtures
"""
from typing import Dict, Any, List
from datetime import datetime, timezone


def get_empty_state() -> Dict[str, Any]:
    """Get an empty state for testing"""
    return {}


def get_single_zone_empty_state() -> Dict[str, Any]:
    """Get state with single zone but no tasks"""
    return {
        'Kitchen': {
            'tasks': []
        }
    }


def get_single_zone_with_active_tasks() -> Dict[str, Any]:
    """Get state with single zone containing active tasks"""
    return {
        'Kitchen': {
            'tasks': [
                {
                    'id': 'task_1687392000_kitchen_0',
                    'description': 'Load the dirty dishes from the counter into the dishwasher.',
                    'status': 'active',
                    'created_at': '2023-06-21T18:00:00Z',
                    'completed_at': None
                },
                {
                    'id': 'task_1687392060_kitchen_1',
                    'description': 'Return the cooking oil bottles from the counter into their cabinet.',
                    'status': 'active',
                    'created_at': '2023-06-21T18:01:00Z',
                    'completed_at': None
                },
                {
                    'id': 'task_1687392120_kitchen_2',
                    'description': 'Wipe down the kitchen counter and stovetop.',
                    'status': 'active',
                    'created_at': '2023-06-21T18:02:00Z',
                    'completed_at': None
                }
            ]
        }
    }


def get_single_zone_with_mixed_tasks() -> Dict[str, Any]:
    """Get state with single zone containing both active and completed tasks"""
    return {
        'Kitchen': {
            'tasks': [
                {
                    'id': 'task_1687392000_kitchen_0',
                    'description': 'Load the dirty dishes from the counter into the dishwasher.',
                    'status': 'completed',
                    'created_at': '2023-06-21T18:00:00Z',
                    'completed_at': '2023-06-21T19:30:00Z'
                },
                {
                    'id': 'task_1687392060_kitchen_1',
                    'description': 'Return the cooking oil bottles from the counter into their cabinet.',
                    'status': 'active',
                    'created_at': '2023-06-21T18:01:00Z',
                    'completed_at': None
                },
                {
                    'id': 'task_1687392120_kitchen_2',
                    'description': 'Wipe down the kitchen counter and stovetop.',
                    'status': 'completed',
                    'created_at': '2023-06-21T18:02:00Z',
                    'completed_at': '2023-06-21T19:45:00Z'
                }
            ]
        }
    }


def get_multi_zone_state() -> Dict[str, Any]:
    """Get state with multiple zones"""
    return {
        'Kitchen': {
            'tasks': [
                {
                    'id': 'task_1687392000_kitchen_0',
                    'description': 'Load the dirty dishes from the counter into the dishwasher.',
                    'status': 'active',
                    'created_at': '2023-06-21T18:00:00Z',
                    'completed_at': None
                }
            ]
        },
        'Living Room': {
            'tasks': [
                {
                    'id': 'task_1687392000_living_room_0',
                    'description': 'Fold and put away the blankets on the couch.',
                    'status': 'active',
                    'created_at': '2023-06-21T18:00:00Z',
                    'completed_at': None
                },
                {
                    'id': 'task_1687392060_living_room_1',
                    'description': 'Organize the magazines on the coffee table.',
                    'status': 'completed',
                    'created_at': '2023-06-21T18:01:00Z',
                    'completed_at': '2023-06-21T18:30:00Z'
                }
            ]
        },
        'Bedroom': {
            'tasks': []
        }
    }


def get_corrupted_state_examples() -> List[Dict[str, Any]]:
    """Get examples of corrupted state data for error testing"""
    return [
        # Missing task ID
        {
            'Kitchen': {
                'tasks': [
                    {
                        'description': 'Load the dirty dishes from the counter into the dishwasher.',
                        'status': 'active',
                        'created_at': '2023-06-21T18:00:00Z',
                        'completed_at': None
                    }
                ]
            }
        },
        # Invalid task status
        {
            'Kitchen': {
                'tasks': [
                    {
                        'id': 'task_1687392000_kitchen_0',
                        'description': 'Load the dirty dishes from the counter into the dishwasher.',
                        'status': 'invalid_status',
                        'created_at': '2023-06-21T18:00:00Z',
                        'completed_at': None
                    }
                ]
            }
        },
        # Missing required fields
        {
            'Kitchen': {
                'tasks': [
                    {
                        'id': 'task_1687392000_kitchen_0',
                        'status': 'active'
                        # Missing description and created_at
                    }
                ]
            }
        },
        # Invalid date format
        {
            'Kitchen': {
                'tasks': [
                    {
                        'id': 'task_1687392000_kitchen_0',
                        'description': 'Load the dirty dishes from the counter into the dishwasher.',
                        'status': 'active',
                        'created_at': 'invalid_date_format',
                        'completed_at': None
                    }
                ]
            }
        }
    ]


def get_active_tasks_for_zone(zone_name: str) -> List[Dict[str, Any]]:
    """Get list of active tasks for a specific zone"""
    all_states = [
        get_single_zone_with_active_tasks(),
        get_single_zone_with_mixed_tasks(),
        get_multi_zone_state()
    ]
    
    for state in all_states:
        if zone_name in state:
            return [task for task in state[zone_name]['tasks'] if task['status'] == 'active']
    
    return []


def get_completed_tasks_for_zone(zone_name: str) -> List[Dict[str, Any]]:
    """Get list of completed tasks for a specific zone"""
    all_states = [
        get_single_zone_with_mixed_tasks(),
        get_multi_zone_state()
    ]
    
    for state in all_states:
        if zone_name in state:
            return [task for task in state[zone_name]['tasks'] if task['status'] == 'completed']
    
    return []


def create_test_task(zone_name: str, index: int, description: str, status: str = 'active') -> Dict[str, Any]:
    """Create a test task with proper ID format"""
    timestamp = int(datetime.now(timezone.utc).timestamp())
    task_id = f"task_{timestamp}_{zone_name.lower().replace(' ', '_')}_{index}"
    
    task = {
        'id': task_id,
        'description': description,
        'status': status,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'completed_at': None
    }
    
    if status == 'completed':
        task['completed_at'] = datetime.now(timezone.utc).isoformat()
    
    return task
