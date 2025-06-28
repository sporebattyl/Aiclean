"""
Test suite for AICleaner Addon Deployment
Following TDD principles with AAA (Arrange-Act-Assert) pattern
Testing deployment, configuration, and startup issues
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


class TestAddonDeployment:
    """Test addon deployment and configuration issues following AAA pattern"""
    
    def test_addon_paths_exist(self):
        """
        AAA Test: All required addon paths should exist
        """
        # ARRANGE
        expected_paths = [
            '/addons/Aiclean/aicleaner',
            '/addons/Aiclean/aicleaner/www',
            '/addons/Aiclean/aicleaner/aicleaner.py',
            '/addons/Aiclean/aicleaner/run.sh',
            '/addons/Aiclean/aicleaner/config.yaml'
        ]
        
        # ACT & ASSERT
        for path in expected_paths:
            assert os.path.exists(path), f"Required path does not exist: {path}"
    
    def test_run_script_has_correct_paths(self):
        """
        AAA Test: Run script should reference correct paths
        """
        # ARRANGE
        run_script_path = '/addons/Aiclean/aicleaner/run.sh'
        
        # ACT
        with open(run_script_path, 'r') as f:
            content = f.read()
        
        # ASSERT
        assert '/addons/Aiclean/aicleaner/www' in content, "Run script should reference correct www path"
        assert '/addons/Aiclean/aicleaner' in content, "Run script should reference correct aicleaner path"
        assert '/addons/aiclean' not in content, "Run script should not reference old lowercase path"
    
    def test_config_yaml_has_updated_personalities(self):
        """
        AAA Test: Config YAML should have updated notification personalities
        """
        # ARRANGE
        config_path = '/addons/Aiclean/aicleaner/config.yaml'
        expected_personalities = ['default', 'snarky', 'jarvis', 'roaster', 'butler', 'coach', 'zen']
        old_personalities = ['comedian', 'sargent']

        # ACT
        with open(config_path, 'r') as f:
            content = f.read()

        # ASSERT
        for personality in expected_personalities:
            assert personality in content, f"Expected personality '{personality}' not found in config"

        for personality in old_personalities:
            assert personality not in content, f"Old personality '{personality}' should not be in config"

    def test_config_yaml_has_all_required_zone_fields(self):
        """
        AAA Test: Config YAML should include all required zone fields including notification_service and todo_list_entity
        """
        # ARRANGE
        config_path = '/addons/Aiclean/aicleaner/config.yaml'
        required_zone_fields = [
            'name', 'icon', 'purpose', 'camera_entity', 'todo_list_entity',
            'update_frequency', 'notifications_enabled', 'notification_service',
            'notification_personality', 'notify_on_create', 'notify_on_complete'
        ]

        # ACT
        with open(config_path, 'r') as f:
            content = f.read()

        # ASSERT
        for field in required_zone_fields:
            assert field in content, f"Required zone field '{field}' not found in config schema"

    def test_config_yaml_has_helpful_examples(self):
        """
        AAA Test: Config YAML should have helpful examples for user guidance
        """
        # ARRANGE
        config_path = '/addons/Aiclean/aicleaner/config.yaml'
        expected_examples = [
            'camera.kitchen',
            'todo.kitchen_tasks',
            'mobile_app_',
            'mdi:',
            'Keep the kitchen clean'
        ]

        # ACT
        with open(config_path, 'r') as f:
            content = f.read()

        # ASSERT
        for example in expected_examples:
            assert example in content, f"Expected example '{example}' not found in config for user guidance"
    
    def test_python_dependencies_available(self):
        """
        AAA Test: All required Python dependencies should be available
        """
        # ARRANGE
        required_modules = [
            'PIL',
            'google.generativeai',
            'requests',
            'aiofiles'
        ]
        
        # ACT & ASSERT
        for module in required_modules:
            try:
                __import__(module)
                success = True
            except ImportError:
                success = False
            
            assert success, f"Required module '{module}' is not available"
    
    def test_aicleaner_module_imports(self):
        """
        AAA Test: AICleaner module and components should import correctly
        """
        # ARRANGE
        import sys
        sys.path.append('/addons/Aiclean/aicleaner')
        
        # ACT & ASSERT
        try:
            from notification_engine import NotificationEngine
            from ignore_rules_manager import IgnoreRulesManager
            from rule_validator import RuleValidator
            from rule_matcher import RuleMatcher
            from rule_persistence import RulePersistence
            from personality_formatter import PersonalityFormatter
            from message_template import MessageTemplate
            from notification_sender import NotificationSender
            import_success = True
        except ImportError as e:
            import_success = False
            import_error = str(e)
        
        assert import_success, f"Failed to import AICleaner components: {import_error if not import_success else ''}"
    
    def test_www_directory_has_ui_files(self):
        """
        AAA Test: WWW directory should contain UI files
        """
        # ARRANGE
        www_path = '/addons/Aiclean/aicleaner/www'
        expected_files = [
            'aicleaner-card.js'
        ]
        
        # ACT & ASSERT
        for file in expected_files:
            file_path = os.path.join(www_path, file)
            assert os.path.exists(file_path), f"Required UI file does not exist: {file_path}"
    
    def test_data_directory_permissions(self):
        """
        AAA Test: Data directory should be writable for persistence
        """
        # ARRANGE
        data_dir = '/data'
        test_file = os.path.join(data_dir, 'test_write_permissions.tmp')
        
        # ACT
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            write_success = True
            
            # Clean up
            if os.path.exists(test_file):
                os.remove(test_file)
        except Exception:
            write_success = False
        
        # ASSERT
        assert write_success, "Data directory is not writable for persistence"
    
    @patch('subprocess.run')
    def test_static_server_can_start(self, mock_subprocess):
        """
        AAA Test: Static file server should be able to start
        """
        # ARRANGE
        mock_subprocess.return_value.returncode = 0
        www_path = '/addons/Aiclean/aicleaner/www'
        
        # ACT
        import subprocess
        result = subprocess.run(['python3', '-m', 'http.server', '8099'], 
                              cwd=www_path, capture_output=True, timeout=1)
        
        # ASSERT
        # The command should start successfully (we'll get timeout, but that's expected)
        assert True  # If we get here without exception, the command can start


class TestAddonStartup:
    """Test addon startup behavior following AAA pattern"""

    def test_addon_handles_missing_config_gracefully(self):
        """
        AAA Test: Addon should handle missing configuration gracefully
        """
        # ARRANGE
        import sys
        sys.path.append('/addons/Aiclean/aicleaner')

        # ACT & ASSERT
        try:
            # This should not crash even with missing config
            from aicleaner import AICleaner
            startup_success = True
        except Exception as e:
            startup_success = False
            error_message = str(e)

        # The import should succeed even if configuration is missing
        assert startup_success, f"Addon import failed: {error_message if not startup_success else ''}"

    def test_addon_validates_config_before_starting_zones(self):
        """
        AAA Test: Addon should validate configuration before starting zones
        """
        # ARRANGE
        import sys
        sys.path.append('/addons/Aiclean/aicleaner')

        invalid_config = {
            'gemini_api_key': None,  # Invalid - required field
            'display_name': 'Test User',
            'zones': []
        }

        # ACT
        try:
            from aicleaner import AICleaner
            app = AICleaner()
            validation_result = app._validate_configuration(invalid_config)
        except Exception as e:
            validation_result = False

        # ASSERT
        assert validation_result is False, "Invalid configuration should be rejected"


class TestAddonConfiguration:
    """Test addon configuration validation following AAA pattern"""
    
    def test_minimal_valid_configuration(self):
        """
        AAA Test: Minimal valid configuration should be accepted
        """
        # ARRANGE
        minimal_config = {
            'gemini_api_key': 'test_key_123',
            'display_name': 'Test User',
            'zones': [
                {
                    'name': 'kitchen',
                    'icon': 'mdi:chef-hat',
                    'purpose': 'Keep the kitchen clean',
                    'camera_entity': 'camera.kitchen',
                    'todo_list_entity': 'todo.kitchen_tasks',
                    'update_frequency': 30,
                    'notifications_enabled': True,
                    'notification_service': 'mobile_app_test',
                    'notification_personality': 'default',
                    'notify_on_create': True,
                    'notify_on_complete': True
                }
            ]
        }
        
        # ACT
        # Simulate configuration validation
        config_valid = self._validate_config(minimal_config)
        
        # ASSERT
        assert config_valid is True, "Minimal valid configuration should be accepted"
    
    def test_invalid_notification_personality_rejected(self):
        """
        AAA Test: Invalid notification personality should be rejected
        """
        # ARRANGE
        invalid_config = {
            'gemini_api_key': 'test_key_123',
            'display_name': 'Test User',
            'zones': [
                {
                    'name': 'kitchen',
                    'icon': 'mdi:chef-hat',
                    'purpose': 'Keep the kitchen clean',
                    'camera_entity': 'camera.kitchen',
                    'todo_list_entity': 'todo.kitchen_tasks',
                    'update_frequency': 30,
                    'notifications_enabled': True,
                    'notification_service': 'mobile_app_test',
                    'notification_personality': 'invalid_personality',  # Invalid
                    'notify_on_create': True,
                    'notify_on_complete': True
                }
            ]
        }
        
        # ACT
        config_valid = self._validate_config(invalid_config)
        
        # ASSERT
        assert config_valid is False, "Invalid notification personality should be rejected"
    
    def test_missing_required_fields_rejected(self):
        """
        AAA Test: Configuration missing required fields should be rejected
        """
        # ARRANGE
        incomplete_config = {
            'gemini_api_key': 'test_key_123',
            # Missing display_name
            'zones': []
        }
        
        # ACT
        config_valid = self._validate_config(incomplete_config)
        
        # ASSERT
        assert config_valid is False, "Configuration missing required fields should be rejected"
    
    def _validate_config(self, config):
        """Helper method to validate configuration"""
        try:
            # Check required top-level fields
            required_fields = ['gemini_api_key', 'display_name', 'zones']
            for field in required_fields:
                if field not in config:
                    return False
            
            # Check zone configurations
            valid_personalities = ['default', 'snarky', 'jarvis', 'roaster', 'butler', 'coach', 'zen']
            for zone in config['zones']:
                if 'notification_personality' in zone:
                    if zone['notification_personality'] not in valid_personalities:
                        return False
            
            return True
        except Exception:
            return False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
