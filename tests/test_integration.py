import pytest
import os
from unittest.mock import patch, MagicMock
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
    """Pytest fixture for an initialized AICleaner instance for integration tests."""
    with patch.object(aicleaner.AICleaner, '_load_config', return_value=mock_config):
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel'):
                instance = aicleaner.AICleaner()
    return instance

def test_run_cycle_success(cleaner_instance):
    """
    Tests a full, successful run cycle of the application.
    """
    # Mock the individual methods that perform external calls
    with patch.object(cleaner_instance, 'get_camera_snapshot', return_value='fake_snapshot.jpg') as mock_snapshot, \
         patch.object(cleaner_instance, 'analyze_image_with_gemini', return_value={'score': 90, 'tasks': ['Do this', 'Do that']}) as mock_analyze, \
         patch.object(cleaner_instance, 'update_ha_sensor') as mock_update_sensor, \
         patch.object(cleaner_instance, 'update_ha_todolist') as mock_update_list, \
         patch('os.remove') as mock_remove, \
         patch('time.sleep', side_effect=InterruptedError):  # Use InterruptedError to break the loop

        # Run the method, expecting it to break after one loop
        with pytest.raises(InterruptedError):
            cleaner_instance.run()

        # Assert that each step in the orchestration was called correctly
        mock_snapshot.assert_called_once()
        mock_analyze.assert_called_once_with('fake_snapshot.jpg')
        mock_update_sensor.assert_called_once_with(90)
        mock_update_list.assert_called_once_with(['Do this', 'Do that'])
        mock_remove.assert_called_once_with('fake_snapshot.jpg')

def test_run_cycle_snapshot_fails(cleaner_instance):
    """
    Tests the run cycle when getting a camera snapshot fails.
    """
    with patch.object(cleaner_instance, 'get_camera_snapshot', return_value=None) as mock_snapshot, \
         patch.object(cleaner_instance, 'analyze_image_with_gemini') as mock_analyze, \
         patch('os.remove') as mock_remove, \
         patch('time.sleep', side_effect=InterruptedError):

        with pytest.raises(InterruptedError):
            cleaner_instance.run()

        mock_snapshot.assert_called_once()
        mock_analyze.assert_not_called()
        mock_remove.assert_not_called()

def test_run_cycle_analysis_fails(cleaner_instance):
    """
    Tests the run cycle when the image analysis fails.
    """
    with patch.object(cleaner_instance, 'get_camera_snapshot', return_value='fake_snapshot.jpg') as mock_snapshot, \
         patch.object(cleaner_instance, 'analyze_image_with_gemini', return_value=None) as mock_analyze, \
         patch.object(cleaner_instance, 'update_ha_sensor') as mock_update_sensor, \
         patch.object(cleaner_instance, 'update_ha_todolist') as mock_update_list, \
         patch('os.remove') as mock_remove, \
         patch('time.sleep', side_effect=InterruptedError):

        with pytest.raises(InterruptedError):
            cleaner_instance.run()

        mock_snapshot.assert_called_once()
        mock_analyze.assert_called_once_with('fake_snapshot.jpg')
        mock_update_sensor.assert_not_called()
        mock_update_list.assert_not_called()
        mock_remove.assert_called_once_with('fake_snapshot.jpg')