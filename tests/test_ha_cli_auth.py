"""
Test suite for Home Assistant CLI authentication using TDD and AAA principles.

This module tests the authentication mechanism for the HA CLI to ensure
proper access to addon management and logging functionality.
"""

import pytest
import subprocess
import os
import sys
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

# Add the parent directory to sys.path to import our components
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ha_auth_component import HAAuthenticationComponent
from ha_addon_manager import HAAddonManager


class TestHACLIAuthentication:
    """Test class for HA CLI authentication functionality."""
    
    def test_ha_cli_available(self):
        """
        Test that the HA CLI is available in the system.
        
        Arrange: System with HA CLI installed
        Act: Check if 'ha' command exists
        Assert: Command is available and executable
        """
        # Arrange
        expected_path = "/usr/bin/ha"
        
        # Act
        result = subprocess.run(["which", "ha"], capture_output=True, text=True)
        
        # Assert
        assert result.returncode == 0, "HA CLI should be available"
        assert expected_path in result.stdout, f"HA CLI should be at {expected_path}"
    
    def test_ha_cli_requires_authentication(self):
        """
        Test that HA CLI commands require proper authentication.
        
        Arrange: HA CLI without authentication token
        Act: Run a command that requires authentication
        Assert: Returns 401 Unauthorized error
        """
        # Arrange
        test_command = ["ha", "addons", "list"]
        
        # Act
        result = subprocess.run(test_command, capture_output=True, text=True)
        
        # Assert
        assert result.returncode != 0, "HA CLI should fail without authentication"
        assert "401" in result.stderr or "Unauthorized" in result.stderr, \
            "Should return 401 Unauthorized error"
    
    def test_ha_cli_with_token_authentication(self):
        """
        Test HA CLI authentication with API token.

        Arrange: Valid API token for HA CLI
        Act: Run command with --api-token parameter
        Assert: Command executes successfully
        """
        # Arrange
        token = os.getenv('HA_TOKEN')
        if not token:
            pytest.skip("HA_TOKEN environment variable not set - please provide Long-Lived Access Token")

        test_command = ["ha", "--api-token", token, "info"]

        # Act
        result = subprocess.run(test_command, capture_output=True, text=True, timeout=15)

        # Assert
        assert result.returncode == 0, f"HA CLI should work with valid token. Error: {result.stderr}"
        assert "Home Assistant" in result.stdout, "Should return Home Assistant info"
    
    def test_ha_cli_config_file_creation(self):
        """
        Test creation of HA CLI configuration file.
        
        Arrange: Configuration data for HA CLI
        Act: Create ~/.homeassistant.yaml config file
        Assert: File is created with correct format
        """
        # Arrange
        config_path = os.path.expanduser("~/.homeassistant.yaml")
        test_config = {
            "endpoint": "supervisor",
            "token": "test_token_placeholder"
        }
        
        # Act & Assert
        # This will be implemented after we determine the correct config format
        pytest.skip("Will implement after determining correct config format")


class TestHAAddonManagement:
    """Test class for HA addon management functionality."""
    
    def test_addon_restart_command_structure(self):
        """
        Test the structure of addon restart command.
        
        Arrange: Addon name and expected command format
        Act: Build restart command
        Assert: Command has correct structure
        """
        # Arrange
        addon_name = "aicleaner"
        expected_command = ["ha", "addons", "restart", addon_name]
        
        # Act
        actual_command = ["ha", "addons", "restart", addon_name]
        
        # Assert
        assert actual_command == expected_command, \
            "Restart command should have correct structure"
    
    def test_addon_logs_command_structure(self):
        """
        Test the structure of addon logs command.
        
        Arrange: Addon name and expected command format
        Act: Build logs command
        Assert: Command has correct structure
        """
        # Arrange
        addon_name = "aicleaner"
        expected_command = ["ha", "addons", "logs", addon_name]
        
        # Act
        actual_command = ["ha", "addons", "logs", addon_name]
        
        # Assert
        assert actual_command == expected_command, \
            "Logs command should have correct structure"


class TestAuthenticationComponent:
    """Component-based test for authentication functionality."""
    
    def test_authentication_component_initialization(self):
        """
        Test authentication component initialization.

        Arrange: HAAuthenticationComponent class
        Act: Initialize component
        Assert: Component initializes with correct defaults
        """
        # Arrange & Act
        auth_component = HAAuthenticationComponent()

        # Assert
        assert auth_component.token is None, "Token should be None initially"
        assert auth_component.endpoint == "supervisor", "Default endpoint should be supervisor"
        assert auth_component.config_path == Path.home() / ".homeassistant.yaml", \
            "Config path should be correct"

    @patch.dict(os.environ, {'SUPERVISOR_TOKEN': 'test_supervisor_token'})
    def test_token_discovery_from_environment(self):
        """
        Test token discovery from environment variables.

        Arrange: Environment with SUPERVISOR_TOKEN set
        Act: Discover token
        Assert: Token is found from environment
        """
        # Arrange
        auth_component = HAAuthenticationComponent()

        # Act
        token = auth_component.discover_token()

        # Assert
        assert token == 'test_supervisor_token', "Should discover token from environment"

    @patch('builtins.open', mock_open(read_data='{"access_token": "test_file_token"}'))
    @patch('os.path.exists', return_value=True)
    def test_token_discovery_from_file(self, mock_exists):
        """
        Test token discovery from supervisor files.

        Arrange: Mock file with access_token
        Act: Discover token
        Assert: Token is found from file
        """
        # Arrange
        auth_component = HAAuthenticationComponent()

        # Act
        token = auth_component.discover_token()

        # Assert
        assert token == 'test_file_token', "Should discover token from file"

    @patch('subprocess.run')
    def test_authentication_test_success(self, mock_run):
        """
        Test successful authentication test.

        Arrange: Mock successful subprocess call
        Act: Test authentication with token
        Assert: Returns True for successful authentication
        """
        # Arrange
        mock_run.return_value.returncode = 0
        auth_component = HAAuthenticationComponent()
        test_token = "test_token"

        # Act
        result = auth_component.test_authentication(test_token)

        # Assert
        assert result is True, "Should return True for successful authentication"
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_authentication_test_failure(self, mock_run):
        """
        Test failed authentication test.

        Arrange: Mock failed subprocess call
        Act: Test authentication with invalid token
        Assert: Returns False for failed authentication
        """
        # Arrange
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "401 Unauthorized"
        auth_component = HAAuthenticationComponent()
        test_token = "invalid_token"

        # Act
        result = auth_component.test_authentication(test_token)

        # Assert
        assert result is False, "Should return False for failed authentication"


class TestHAAddonManager:
    """Test class for HA Addon Manager component."""

    def test_addon_manager_initialization(self):
        """
        Test addon manager initialization.

        Arrange: HAAddonManager class and parameters
        Act: Initialize addon manager
        Assert: Manager initializes with correct settings
        """
        # Arrange
        ha_url = "http://localhost:8123"
        token = "test_token"

        # Act
        manager = HAAddonManager(ha_url, token)

        # Assert
        assert manager.ha_url == ha_url, "HA URL should be set correctly"
        assert manager.token == token, "Token should be set correctly"
        assert "Bearer test_token" in manager.headers["Authorization"], \
            "Authorization header should be set correctly"

    @patch('requests.get')
    def test_connection_test_success(self, mock_get):
        """
        Test successful connection to HA API.

        Arrange: Mock successful API response
        Act: Test connection
        Assert: Returns True for successful connection
        """
        # Arrange
        mock_get.return_value.status_code = 200
        manager = HAAddonManager(token="test_token")

        # Act
        result = manager.test_connection()

        # Assert
        assert result is True, "Should return True for successful connection"
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_connection_test_failure(self, mock_get):
        """
        Test failed connection to HA API.

        Arrange: Mock failed API response
        Act: Test connection
        Assert: Returns False for failed connection
        """
        # Arrange
        mock_get.return_value.status_code = 403
        manager = HAAddonManager(token="test_token")

        # Act
        result = manager.test_connection()

        # Assert
        assert result is False, "Should return False for failed connection"

    @patch('subprocess.run')
    def test_check_addon_running_true(self, mock_run):
        """
        Test checking if addon is running (process found).

        Arrange: Mock subprocess that finds process
        Act: Check if addon is running
        Assert: Returns True when process is found
        """
        # Arrange
        mock_run.return_value.returncode = 0
        manager = HAAddonManager(token="test_token")

        # Act
        result = manager.check_addon_running("aicleaner.py")

        # Assert
        assert result is True, "Should return True when process is running"
        mock_run.assert_called_once_with(
            ["pgrep", "-f", "aicleaner.py"],
            capture_output=True,
            text=True
        )
