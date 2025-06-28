"""
Home Assistant CLI Authentication Component

This component handles authentication for the Home Assistant CLI following
component-based design principles. It discovers and manages API tokens
for accessing Home Assistant supervisor functionality.
"""

import os
import json
import subprocess
import logging
from typing import Optional, Dict, Any
from pathlib import Path


class HAAuthenticationComponent:
    """
    Component for managing Home Assistant CLI authentication.
    
    This component follows component-based design principles by:
    - Having a single responsibility (authentication)
    - Providing a clear interface
    - Being testable and mockable
    - Handling errors gracefully
    """
    
    def __init__(self):
        """Initialize the authentication component."""
        self.logger = logging.getLogger(__name__)
        self.token: Optional[str] = None
        self.endpoint: str = "supervisor"
        self.config_path = Path.home() / ".homeassistant.yaml"
    
    def discover_token(self) -> Optional[str]:
        """
        Discover Home Assistant API token from various sources.
        
        Returns:
            str: API token if found, None otherwise
        """
        # Try multiple token discovery methods
        token_sources = [
            self._get_token_from_environment,
            self._get_token_from_supervisor_files,
            self._get_token_from_addon_environment,
            self._get_token_from_homeassistant_config
        ]
        
        for source in token_sources:
            try:
                token = source()
                if token:
                    self.logger.info(f"Token discovered from {source.__name__}")
                    return token
            except Exception as e:
                self.logger.debug(f"Token discovery failed for {source.__name__}: {e}")
        
        self.logger.warning("No API token found in any source")
        return None
    
    def _get_token_from_environment(self) -> Optional[str]:
        """Get token from environment variables."""
        env_vars = [
            'SUPERVISOR_TOKEN',
            'HA_TOKEN',
            'HOMEASSISTANT_TOKEN',
            'HA_API_TOKEN'
        ]
        
        for var in env_vars:
            token = os.getenv(var)
            if token:
                return token
        return None
    
    def _get_token_from_supervisor_files(self) -> Optional[str]:
        """Get token from supervisor configuration files."""
        supervisor_paths = [
            '/data/supervisor/homeassistant.json',
            '/data/homeassistant.json',
            '/supervisor/homeassistant.json'
        ]
        
        for path in supervisor_paths:
            try:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        data = json.load(f)
                        if 'access_token' in data:
                            return data['access_token']
                        if 'token' in data:
                            return data['token']
            except (json.JSONDecodeError, IOError) as e:
                self.logger.debug(f"Failed to read {path}: {e}")
        
        return None
    
    def _get_token_from_addon_environment(self) -> Optional[str]:
        """Get token from addon environment (when running inside addon)."""
        # Check if we're running inside a Home Assistant addon
        addon_paths = [
            '/data/options.json',
            '/addon_configs/options.json'
        ]
        
        for path in addon_paths:
            try:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        data = json.load(f)
                        if 'ha_token' in data:
                            return data['ha_token']
            except (json.JSONDecodeError, IOError) as e:
                self.logger.debug(f"Failed to read addon config {path}: {e}")
        
        return None
    
    def _get_token_from_homeassistant_config(self) -> Optional[str]:
        """Get token from Home Assistant configuration directory."""
        ha_config_paths = [
            '/homeassistant/.storage/auth',
            '/config/.storage/auth',
            '/homeassistant/auth.json'
        ]
        
        for path in ha_config_paths:
            try:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        data = json.load(f)
                        # Look for refresh tokens or access tokens
                        if 'data' in data and 'refresh_tokens' in data['data']:
                            tokens = data['data']['refresh_tokens']
                            if tokens:
                                # Return the first available token
                                first_token = next(iter(tokens.values()))
                                if 'token' in first_token:
                                    return first_token['token']
            except (json.JSONDecodeError, IOError) as e:
                self.logger.debug(f"Failed to read HA config {path}: {e}")
        
        return None
    
    def create_config_file(self, token: str) -> bool:
        """
        Create HA CLI configuration file.
        
        Args:
            token: API token to use
            
        Returns:
            bool: True if config file created successfully
        """
        try:
            config_content = f"""endpoint: {self.endpoint}
token: {token}
"""
            with open(self.config_path, 'w') as f:
                f.write(config_content)
            
            self.logger.info(f"Created HA CLI config at {self.config_path}")
            return True
        except IOError as e:
            self.logger.error(f"Failed to create config file: {e}")
            return False
    
    def test_authentication(self, token: Optional[str] = None) -> bool:
        """
        Test if authentication works with the given or discovered token.
        
        Args:
            token: Optional token to test, uses discovered token if None
            
        Returns:
            bool: True if authentication successful
        """
        test_token = token or self.token
        if not test_token:
            return False
        
        try:
            # Test with a simple command that requires authentication
            cmd = ["ha", "--api-token", test_token, "info"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.logger.info("Authentication test successful")
                return True
            else:
                self.logger.warning(f"Authentication test failed: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            self.logger.error("Authentication test timed out")
            return False
        except Exception as e:
            self.logger.error(f"Authentication test error: {e}")
            return False
    
    def setup_authentication(self) -> bool:
        """
        Set up authentication for HA CLI.
        
        Returns:
            bool: True if authentication setup successful
        """
        # Discover token
        self.token = self.discover_token()
        if not self.token:
            self.logger.error("No API token found")
            return False
        
        # Test authentication
        if not self.test_authentication(self.token):
            self.logger.error("Token authentication failed")
            return False
        
        # Create config file
        if not self.create_config_file(self.token):
            self.logger.error("Failed to create config file")
            return False
        
        self.logger.info("HA CLI authentication setup complete")
        return True
    
    def get_authenticated_command(self, base_command: list) -> list:
        """
        Get command with authentication parameters.
        
        Args:
            base_command: Base HA CLI command
            
        Returns:
            list: Command with authentication parameters
        """
        if self.token:
            # Insert token parameter after 'ha'
            return base_command[:1] + ["--api-token", self.token] + base_command[1:]
        return base_command
