import pytest
from unittest.mock import patch
from aicleaner import aicleaner
import copy

@pytest.fixture
def valid_config():
    """A fixture for a complete and valid configuration."""
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

def test_validation_success(valid_config):
    """Tests that a valid configuration passes validation."""
    with patch.object(aicleaner.AICleaner, '_load_config', return_value=valid_config):
        with patch('google.generativeai.configure'), patch('google.generativeai.GenerativeModel'):
            try:
                aicleaner.AICleaner()
            except ValueError:
                pytest.fail("AICleaner initialization failed with a valid config.")

@pytest.mark.parametrize("missing_key", [
    "api_url", "token", "camera_entity_id", "todolist_entity_id", "sensor_entity_id"
])
def test_missing_ha_key(valid_config, missing_key):
    """Tests that a ValueError is raised if a Home Assistant key is missing."""
    invalid_config = copy.deepcopy(valid_config)
    del invalid_config['home_assistant'][missing_key]
    
    with patch.object(aicleaner.AICleaner, '_load_config', return_value=invalid_config):
        with pytest.raises(ValueError, match=f"Missing required Home Assistant configuration key: '{missing_key}'"):
            aicleaner.AICleaner()

def test_missing_gemini_key(valid_config):
    """Tests that a ValueError is raised if the Gemini API key is missing."""
    invalid_config = copy.deepcopy(valid_config)
    del invalid_config['google_gemini']['api_key']
    
    with patch.object(aicleaner.AICleaner, '_load_config', return_value=invalid_config):
        with pytest.raises(ValueError, match="Missing required Google Gemini configuration key: 'api_key'"):
            aicleaner.AICleaner()

def test_missing_ha_block(valid_config):
    """Tests that a ValueError is raised if the entire Home Assistant block is missing."""
    invalid_config = copy.deepcopy(valid_config)
    del invalid_config['home_assistant']
    
    with patch.object(aicleaner.AICleaner, '_load_config', return_value=invalid_config):
        with pytest.raises(ValueError, match="Missing 'home_assistant' configuration block."):
            aicleaner.AICleaner()