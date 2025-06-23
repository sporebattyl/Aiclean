import pytest
import os
import requests
import logging
from unittest.mock import patch, MagicMock, mock_open
from aicleaner import aicleaner

@pytest.fixture
def mock_config():
    """Pytest fixture for mock configuration data."""
    return {
        'home_assistant': {
            'api_url': 'http://fake-ha.local:8123',
            'token': 'fake-token',
            'camera_entity_id': 'camera.fake_cam',
            'todolist_entity_id': 'todo.fake_list',
            'sensor_entity_id': 'sensor.fake_sensor'
        },
        'google_gemini': {
            'api_key': 'fake-gemini-key'
        },
        'application': {
            'analysis_interval_minutes': 30
        }
    }

# This space is intentionally left blank.


def test_load_from_yaml(mock_config):
    """
    Tests that the _load_from_yaml method correctly loads a YAML file.
    """
    # Create an instance of the class to test its method
    cleaner = aicleaner.AICleaner.__new__(aicleaner.AICleaner)

    # Mock the YAML content
    yaml_content = """
home_assistant:
  api_url: http://fake-ha.local:8123
  token: fake-token
  camera_entity_id: camera.fake_cam
  todolist_entity_id: todo.fake_list
  sensor_entity_id: sensor.fake_sensor
google_gemini:
  api_key: fake-gemini-key
application:
  analysis_interval_minutes: 30
"""
    # Use mock_open to simulate the file
    with patch('builtins.open', mock_open(read_data=yaml_content)) as mock_file:
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            
            # Call the method
            loaded_config = cleaner._load_from_yaml('dummy/path/config.yaml')
            
            # Assertions
            mock_file.assert_called_with('dummy/path/config.yaml', 'r')
            assert loaded_config == mock_config

@patch.dict(os.environ, {
    "SUPERVISOR_API": "http://supervisor/api",
    "SUPERVISOR_TOKEN": "fake-supervisor-token",
    "CAMERA_ENTITY": "camera.fake_env_cam",
    "TODO_LIST": "todo.fake_env_list",
    "SENSOR_ENTITY": "sensor.fake_env_sensor",
    "API_KEY": "fake-env-gemini-key",
    "FREQUENCY": "48"
})
def test_load_from_env():
    """
    Tests that the _load_from_env method correctly loads configuration
    from environment variables.
    """
    # Create an instance of the class to test its method
    cleaner = aicleaner.AICleaner.__new__(aicleaner.AICleaner)
    
    # Call the method
    loaded_config = cleaner._load_from_env()
    
    # Expected config
    expected_config = {
        "home_assistant": {
            "api_url": "http://supervisor",
            "token": "fake-supervisor-token",
            "camera_entity_id": "camera.fake_env_cam",
            "todolist_entity_id": "todo.fake_env_list",
            "sensor_entity_id": "sensor.fake_env_sensor",
        },
        "google_gemini": {
            "api_key": "fake-env-gemini-key",
        },
        "application": {
            "analysis_interval_minutes": 48
        }
    }
    
    # Assertion
    assert loaded_config == expected_config

# This space is intentionally left blank.