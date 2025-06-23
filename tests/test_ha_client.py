import pytest
import requests
import logging
from unittest.mock import patch, MagicMock, mock_open
from aicleaner.ha_client import HomeAssistantClient

@pytest.fixture
def ha_client():
    """Pytest fixture for an initialized HomeAssistantClient."""
    return HomeAssistantClient(api_url="http://fake-ha.local:8123", token="fake-token")

def test_client_initialization():
    """Tests that the client initializes correctly."""
    client = HomeAssistantClient(api_url="http://test.com", token="test-token")
    assert client.api_url == "http://test.com"
    assert client.headers["Authorization"] == "Bearer test-token"

def test_client_initialization_fails():
    """Tests that initialization fails without required arguments."""
    with pytest.raises(ValueError, match="Home Assistant API URL and token are required."):
        HomeAssistantClient(api_url=None, token=None)

def test_get_camera_snapshot_success(ha_client):
    """Tests the get_camera_snapshot method for a successful API call."""
    mock_response = MagicMock()
    mock_response.content = b'fake_image_bytes'
    mock_response.raise_for_status.return_value = None

    with patch('requests.get', return_value=mock_response) as mock_get:
        with patch('builtins.open', mock_open()) as mock_file:
            snapshot_path = ha_client.get_camera_snapshot("camera.fake")

            expected_url = f"{ha_client.api_url}/api/camera_proxy/camera.fake"
            mock_get.assert_called_once_with(expected_url, headers=ha_client.headers, timeout=10)
            mock_file.assert_called_once_with("snapshot.jpg", 'wb')
            mock_file().write.assert_called_once_with(b'fake_image_bytes')
            assert snapshot_path == "snapshot.jpg"

def test_get_camera_snapshot_failure(ha_client, caplog):
    """Tests the get_camera_snapshot method for a failed API call."""
    with patch('requests.get', side_effect=requests.exceptions.RequestException("API Error")):
        snapshot_path = ha_client.get_camera_snapshot("camera.fake")

        assert snapshot_path is None
        assert "Error getting camera snapshot: API Error" in caplog.text

def test_update_sensor_success(ha_client):
    """Tests the update_sensor method for a successful API call."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch('requests.post', return_value=mock_response) as mock_post:
        ha_client.update_sensor("sensor.fake", 95)

        expected_url = f"{ha_client.api_url}/api/states/sensor.fake"
        expected_payload = {
            "state": 95,
            "attributes": {
                "unit_of_measurement": "%",
                "friendly_name": "Room Cleanliness Score"
            }
        }
        mock_post.assert_called_once_with(expected_url, headers=ha_client.headers, json=expected_payload, timeout=10)

def test_update_sensor_failure(ha_client, caplog):
    """Tests the update_sensor method for a failed API call."""
    with patch('requests.post', side_effect=requests.exceptions.RequestException("API Error")):
        with caplog.at_level(logging.ERROR):
            ha_client.update_sensor("sensor.fake", 95)
            assert "Error updating Home Assistant sensor: API Error" in caplog.text

def test_add_task_to_todolist_success(ha_client):
    """Tests the add_task_to_todolist method for a successful API call."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch('requests.post', return_value=mock_response) as mock_post:
        ha_client.add_task_to_todolist("todo.fake_list", "Test Task")

        expected_url = f"{ha_client.api_url}/api/services/todo/add_item"
        expected_payload = {
            "entity_id": "todo.fake_list",
            "item": "Test Task"
        }
        mock_post.assert_called_once_with(expected_url, headers=ha_client.headers, json=expected_payload, timeout=10)

def test_add_task_to_todolist_failure(ha_client, caplog):
    """Tests the add_task_to_todolist method for a failed API call."""
    with patch('requests.post', side_effect=requests.exceptions.RequestException("API Error")):
        with caplog.at_level(logging.ERROR):
            ha_client.add_task_to_todolist("todo.fake_list", "Test Task")
            assert "Error adding task 'Test Task' to Home Assistant to-do list: API Error" in caplog.text