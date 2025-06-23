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

@pytest.fixture
def cleaner_instance(mock_config):
    """Pytest fixture for an initialized AICleaner instance."""
    # Patch the config loading and the Gemini API configuration
    with patch.object(aicleaner.AICleaner, '_load_config', return_value=mock_config):
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel'):
                 instance = aicleaner.AICleaner()
    return instance


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

def test_get_camera_snapshot_success(cleaner_instance):
    """
    Tests the get_camera_snapshot method for a successful API call.
    """
    mock_response = MagicMock()
    mock_response.content = b'fake_image_bytes'
    mock_response.raise_for_status.return_value = None

    with patch('requests.get', return_value=mock_response) as mock_get:
        with patch('builtins.open', mock_open()) as mock_file:
            snapshot_path = cleaner_instance.get_camera_snapshot()

            expected_url = f"{cleaner_instance.ha_url}/api/camera_proxy/{cleaner_instance.camera_entity_id}"
            mock_get.assert_called_once_with(expected_url, headers=cleaner_instance.ha_headers, timeout=10)
            mock_file.assert_called_once_with("snapshot.jpg", 'wb')
            mock_file().write.assert_called_once_with(b'fake_image_bytes')
            assert snapshot_path == "snapshot.jpg"

def test_get_camera_snapshot_failure(cleaner_instance, caplog):
    """
    Tests the get_camera_snapshot method for a failed API call.
    """
    with patch('requests.get', side_effect=requests.exceptions.RequestException("API Error")):
        snapshot_path = cleaner_instance.get_camera_snapshot()

        assert snapshot_path is None
        assert "Error getting camera snapshot: API Error" in caplog.text

def test_analyze_image_with_gemini_success(cleaner_instance, caplog):
    """
    Tests the analyze_image_with_gemini method for a successful analysis.
    """
    # Mock the response from the Gemini API
    mock_gemini_response = MagicMock()
    mock_gemini_response.text = '```json\n{"score": 85, "tasks": ["Clean the floor"]}\n```'
    
    # Mock the model's generate_content method
    cleaner_instance.gemini_model.generate_content.return_value = mock_gemini_response

    with patch('os.path.exists', return_value=True):
        with patch('google.generativeai.upload_file') as mock_upload:
            with caplog.at_level(logging.INFO):
                analysis = cleaner_instance.analyze_image_with_gemini('fake/path.jpg')

                mock_upload.assert_called_once_with(path='fake/path.jpg')
                assert analysis['score'] == 85
                assert analysis['tasks'] == ["Clean the floor"]
                assert "Successfully parsed Gemini response. Score: 85" in caplog.text

def test_analyze_image_with_gemini_invalid_path(cleaner_instance, caplog):
    """
    Tests analyze_image_with_gemini with an invalid file path.
    """
    with patch('os.path.exists', return_value=False):
        analysis = cleaner_instance.analyze_image_with_gemini('nonexistent/path.jpg')
        assert analysis is None
        assert "Invalid image path provided: nonexistent/path.jpg" in caplog.text

def test_analyze_image_with_gemini_api_error(cleaner_instance, caplog):
    """
    Tests analyze_image_with_gemini when the Gemini API call fails.
    """
    cleaner_instance.gemini_model.generate_content.side_effect = Exception("API Failure")

    with patch('os.path.exists', return_value=True):
        with patch('google.generativeai.upload_file'):
            analysis = cleaner_instance.analyze_image_with_gemini('fake/path.jpg')
            assert analysis is None
            assert "Error analyzing image with Gemini: API Failure" in caplog.text

def test_analyze_image_with_gemini_bad_response(cleaner_instance, caplog):
    """
    Tests analyze_image_with_gemini with a malformed response from the API.
    """
    mock_gemini_response = MagicMock()
    mock_gemini_response.text = '{"score": 90, "missing_tasks_key": []}'
    cleaner_instance.gemini_model.generate_content.return_value = mock_gemini_response

    with patch('os.path.exists', return_value=True):
        with patch('google.generativeai.upload_file'):
            analysis = cleaner_instance.analyze_image_with_gemini('fake/path.jpg')
            assert analysis is None
            assert "Gemini response missing 'score' or 'tasks' key." in caplog.text

def test_update_ha_sensor_success(cleaner_instance):
    """
    Tests the update_ha_sensor method for a successful API call.
    """
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch('requests.post', return_value=mock_response) as mock_post:
        cleaner_instance.update_ha_sensor(95)

        expected_url = f"{cleaner_instance.ha_url}/api/states/{cleaner_instance.sensor_entity_id}"
        expected_payload = {
            "state": 95,
            "attributes": {
                "unit_of_measurement": "%",
                "friendly_name": "Room Cleanliness Score"
            }
        }
        mock_post.assert_called_once_with(expected_url, headers=cleaner_instance.ha_headers, json=expected_payload, timeout=10)

def test_update_ha_sensor_failure(cleaner_instance, caplog):
    """
    Tests the update_ha_sensor method for a failed API call.
    """
    with patch('requests.post', side_effect=requests.exceptions.RequestException("API Error")):
        with caplog.at_level(logging.ERROR):
            cleaner_instance.update_ha_sensor(95)
            assert "Error updating Home Assistant sensor: API Error" in caplog.text

def test_update_ha_sensor_no_score(cleaner_instance, caplog):
    """
    Tests that update_ha_sensor does nothing if the score is None.
    """
    with patch('requests.post') as mock_post:
        with caplog.at_level(logging.WARNING):
            cleaner_instance.update_ha_sensor(None)
            mock_post.assert_not_called()
            assert "No score provided to update HA sensor." in caplog.text

def test_update_ha_todolist_success(cleaner_instance):
    """
    Tests the update_ha_todolist method for successful API calls.
    """
    tasks = ["Task 1", "Task 2"]
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch('requests.post', return_value=mock_response) as mock_post:
        cleaner_instance.update_ha_todolist(tasks)

        assert mock_post.call_count == 2
        # More detailed assertions could be added here for each call

def test_update_ha_todolist_api_error(cleaner_instance, caplog):
    """
    Tests the update_ha_todolist method when an API call fails.
    """
    tasks = ["Task 1", "Task 2"]
    with patch('requests.post', side_effect=requests.exceptions.RequestException("API Error")):
        with caplog.at_level(logging.ERROR):
            cleaner_instance.update_ha_todolist(tasks)
            assert "Error adding task 'Task 1' to Home Assistant to-do list: API Error" in caplog.text
            assert "Error adding task 'Task 2' to Home Assistant to-do list: API Error" in caplog.text

def test_update_ha_todolist_no_tasks(cleaner_instance, caplog):
    """
    Tests that update_ha_todolist does nothing if tasks list is empty.
    """
    with patch('requests.post') as mock_post:
        with caplog.at_level(logging.INFO):
            cleaner_instance.update_ha_todolist([])
            mock_post.assert_not_called()
            assert "No tasks to add to the to-do list." in caplog.text