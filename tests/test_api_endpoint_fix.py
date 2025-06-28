"""
Test suite for API endpoint fix using TDD and AAA principles.

This module tests that the AICleaner uses the correct API endpoints
that work with Long-Lived Access Tokens.
"""

import pytest
import os
import json
import tempfile
from unittest.mock import patch, mock_open
import sys

# Add the aicleaner directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'aicleaner'))


class TestAPIEndpointFix:
    """Test class for API endpoint fix verification."""
    
    def test_addon_env_with_ha_token(self):
        """
        Test addon environment configuration with HA_TOKEN.
        
        Arrange: Mock addon environment with HA_TOKEN
        Act: Load configuration from addon environment
        Assert: Uses direct HA API URL and HA_TOKEN
        """
        # Arrange
        from aicleaner import AICleaner
        
        test_options = {
            "gemini_api_key": "test_key",
            "display_name": "Test User",
            "zones": [{
                "name": "kitchen",
                "icon": "mdi:chef-hat",
                "purpose": "Test kitchen zone",
                "camera_entity": "camera.test",
                "todo_list_entity": "todo.test",
                "update_frequency": 30,
                "notifications_enabled": False,
                "notification_service": "",
                "notification_personality": "default",
                "notify_on_create": False,
                "notify_on_complete": False
            }]
        }
        
        # Mock environment with HA_TOKEN
        with patch.dict(os.environ, {
            'HA_TOKEN': 'test_ha_token',
            'SUPERVISOR_TOKEN': 'test_supervisor_token'
        }):
            with patch('os.path.exists', return_value=True):
                with patch('builtins.open', mock_open(read_data=json.dumps(test_options))):
                    with patch.object(AICleaner, '_create_gemini_client'):
                        with patch.object(AICleaner, '_load_persistent_state', return_value={}):
                            # Act
                            cleaner = AICleaner()
                            config = cleaner._load_from_addon_env()

                            # Assert
                            assert config['ha_api_url'] == 'http://localhost:8123/api', \
                                "Should use direct HA API URL"
                            assert config['ha_token'] == 'test_ha_token', \
                                "Should use HA_TOKEN when available"
    
    def test_addon_env_fallback_to_supervisor_token(self):
        """
        Test addon environment fallback to SUPERVISOR_TOKEN.
        
        Arrange: Mock addon environment without HA_TOKEN
        Act: Load configuration from addon environment
        Assert: Falls back to SUPERVISOR_TOKEN
        """
        # Arrange
        from aicleaner import AICleaner
        
        test_options = {
            "gemini_api_key": "test_key",
            "display_name": "Test User",
            "zones": []
        }
        
        # Mock environment without HA_TOKEN
        with patch.dict(os.environ, {
            'SUPERVISOR_TOKEN': 'test_supervisor_token'
        }, clear=True):
            # Remove HA_TOKEN if it exists
            if 'HA_TOKEN' in os.environ:
                del os.environ['HA_TOKEN']
                
            with patch('os.path.exists', return_value=True):
                with patch('builtins.open', mock_open(read_data=json.dumps(test_options))):
                    # Act
                    cleaner = AICleaner()
                    config = cleaner._load_from_addon_env()
                    
                    # Assert
                    assert config['ha_api_url'] == 'http://localhost:8123/api', \
                        "Should still use direct HA API URL"
                    assert config['ha_token'] == 'test_supervisor_token', \
                        "Should fallback to SUPERVISOR_TOKEN"
    
    def test_addon_env_no_tokens_error(self):
        """
        Test addon environment error when no tokens available.
        
        Arrange: Mock addon environment without any tokens
        Act: Attempt to load configuration
        Assert: Raises appropriate error
        """
        # Arrange
        from aicleaner import AICleaner
        
        test_options = {"gemini_api_key": "test_key"}
        
        # Mock environment without any tokens
        with patch.dict(os.environ, {}, clear=True):
            with patch('os.path.exists', return_value=True):
                with patch('builtins.open', mock_open(read_data=json.dumps(test_options))):
                    # Act & Assert
                    cleaner = AICleaner()
                    with pytest.raises(ValueError, match="Neither HA_TOKEN nor SUPERVISOR_TOKEN"):
                        cleaner._load_from_addon_env()
    
    def test_ha_client_url_construction(self):
        """
        Test that HAClient constructs URLs correctly with new API base.
        
        Arrange: HAClient with direct HA API URL
        Act: Test URL construction for camera and sensor endpoints
        Assert: URLs are constructed correctly
        """
        # Arrange
        from aicleaner import HAClient
        
        api_url = "http://localhost:8123/api"
        token = "test_token"
        client = HAClient(api_url, token)
        
        # Act
        camera_entity = "camera.test"
        sensor_entity = "sensor.test"
        
        # Test camera URL construction (this happens in get_camera_snapshot)
        expected_camera_url = f"{api_url}/camera_proxy/{camera_entity}"
        
        # Test sensor URL construction (this happens in update_sensor)
        expected_sensor_url = f"{api_url}/states/{sensor_entity}"
        
        # Assert
        assert expected_camera_url == "http://localhost:8123/api/camera_proxy/camera.test", \
            "Camera URL should be constructed correctly"
        assert expected_sensor_url == "http://localhost:8123/api/states/sensor.test", \
            "Sensor URL should be constructed correctly"
        
        # Verify no double /api
        assert "/api/api/" not in expected_camera_url, \
            "Camera URL should not contain double /api"
        assert "/api/api/" not in expected_sensor_url, \
            "Sensor URL should not contain double /api"


class TestAPIEndpointIntegration:
    """Integration tests for API endpoint fix."""
    
    def test_camera_snapshot_with_fixed_endpoints(self):
        """
        Test camera snapshot with fixed API endpoints.
        
        Arrange: Mock successful camera response
        Act: Get camera snapshot
        Assert: Correct endpoint is used and snapshot succeeds
        """
        # Arrange
        from aicleaner import HAClient
        
        api_url = "http://localhost:8123/api"
        token = "test_token"
        client = HAClient(api_url, token)
        
        # Mock successful response
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.content = b"fake_image_data"
            
            # Act
            result = client.get_camera_snapshot("camera.test", "/tmp/test.jpg")
            
            # Assert
            assert result is True, "Camera snapshot should succeed"
            mock_get.assert_called_once_with(
                "http://localhost:8123/api/camera_proxy/camera.test",
                headers=client.headers,
                timeout=10
            )
    
    def test_sensor_update_with_fixed_endpoints(self):
        """
        Test sensor update with fixed API endpoints.
        
        Arrange: Mock successful sensor response
        Act: Update sensor
        Assert: Correct endpoint is used and update succeeds
        """
        # Arrange
        from aicleaner import HAClient
        
        api_url = "http://localhost:8123/api"
        token = "test_token"
        client = HAClient(api_url, token)
        
        # Mock successful response
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            
            # Act
            result = client.update_sensor("sensor.test", "active", {"test": True})
            
            # Assert
            assert result is True, "Sensor update should succeed"
            mock_post.assert_called_once_with(
                "http://localhost:8123/api/states/sensor.test",
                headers=client.headers,
                json={"state": "active", "attributes": {"test": True}},
                timeout=10
            )
    
    def test_complete_configuration_flow(self):
        """
        Test complete configuration flow with API endpoint fix.
        
        Arrange: Complete addon environment setup
        Act: Initialize AICleaner with fixed configuration
        Assert: All components use correct API endpoints
        """
        # Arrange
        from aicleaner import AICleaner
        
        test_options = {
            "gemini_api_key": "test_key",
            "display_name": "Test User",
            "zones": [{
                "name": "kitchen",
                "camera_entity": "camera.test",
                "todo_list_entity": "todo.test",
                "update_frequency": 30
            }]
        }
        
        # Mock environment with HA_TOKEN
        with patch.dict(os.environ, {'HA_TOKEN': 'test_ha_token'}):
            with patch('os.path.exists', return_value=True):
                with patch('builtins.open', mock_open(read_data=json.dumps(test_options))):
                    with patch.object(AICleaner, '_create_gemini_client'):
                        with patch.object(AICleaner, '_load_persistent_state', return_value={}):
                            # Act
                            cleaner = AICleaner()
                            
                            # Assert
                            assert cleaner.config['ha_api_url'] == 'http://localhost:8123/api', \
                                "AICleaner should use direct HA API URL"
                            assert cleaner.config['ha_token'] == 'test_ha_token', \
                                "AICleaner should use HA_TOKEN"
                            
                            # Verify HAClient is created with correct URL
                            assert cleaner.ha_client.api_url == 'http://localhost:8123/api', \
                                "HAClient should be initialized with correct API URL"
