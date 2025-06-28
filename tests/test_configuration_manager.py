"""
Test suite for Configuration Manager Component
Following TDD principles with AAA (Arrange-Act-Assert) pattern
Testing configuration validation and error handling
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock


class TestConfigurationManager:
    """Test configuration management following AAA pattern"""
    
    def test_configuration_manager_initialization(self):
        """
        AAA Test: Configuration manager should initialize correctly
        """
        # ARRANGE
        import sys
        sys.path.append('/addons/Aiclean/aicleaner')
        
        # ACT
        from configuration_manager import ConfigurationManager
        config_manager = ConfigurationManager()
        
        # ASSERT
        assert config_manager is not None
        assert hasattr(config_manager, 'validate_configuration')
        assert hasattr(config_manager, 'load_configuration')
        assert hasattr(config_manager, 'get_validation_errors')
    
    def test_valid_configuration_passes_validation(self):
        """
        AAA Test: Valid configuration should pass validation
        """
        # ARRANGE
        import sys
        sys.path.append('/addons/Aiclean/aicleaner')
        from configuration_manager import ConfigurationManager
        
        config_manager = ConfigurationManager()
        valid_config = {
            'gemini_api_key': 'valid_api_key_123',
            'display_name': 'Test User',
            'zones': [
                {
                    'name': 'kitchen',
                    'icon': 'mdi:chef-hat',
                    'purpose': 'Keep kitchen clean',
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
        is_valid = config_manager.validate_configuration(valid_config)
        errors = config_manager.get_validation_errors()
        
        # ASSERT
        assert is_valid is True
        assert len(errors) == 0
    
    def test_missing_required_fields_fails_validation(self):
        """
        AAA Test: Configuration missing required fields should fail validation
        """
        # ARRANGE
        import sys
        sys.path.append('/addons/Aiclean/aicleaner')
        from configuration_manager import ConfigurationManager
        
        config_manager = ConfigurationManager()
        invalid_config = {
            # Missing gemini_api_key
            'display_name': 'Test User',
            'zones': []
        }
        
        # ACT
        is_valid = config_manager.validate_configuration(invalid_config)
        errors = config_manager.get_validation_errors()
        
        # ASSERT
        assert is_valid is False
        assert len(errors) > 0
        assert any('gemini_api_key' in error for error in errors)
    
    def test_invalid_notification_personality_fails_validation(self):
        """
        AAA Test: Invalid notification personality should fail validation
        """
        # ARRANGE
        import sys
        sys.path.append('/addons/Aiclean/aicleaner')
        from configuration_manager import ConfigurationManager
        
        config_manager = ConfigurationManager()
        invalid_config = {
            'gemini_api_key': 'valid_api_key_123',
            'display_name': 'Test User',
            'zones': [
                {
                    'name': 'kitchen',
                    'icon': 'mdi:chef-hat',
                    'purpose': 'Keep kitchen clean',
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
        is_valid = config_manager.validate_configuration(invalid_config)
        errors = config_manager.get_validation_errors()
        
        # ASSERT
        assert is_valid is False
        assert len(errors) > 0
        assert any('notification_personality' in error for error in errors)
    
    def test_configuration_provides_helpful_error_messages(self):
        """
        AAA Test: Configuration validation should provide helpful error messages
        """
        # ARRANGE
        import sys
        sys.path.append('/addons/Aiclean/aicleaner')
        from configuration_manager import ConfigurationManager
        
        config_manager = ConfigurationManager()
        invalid_config = {
            'gemini_api_key': '',  # Empty string
            'display_name': '',    # Empty string
            'zones': [
                {
                    'name': '',  # Empty string
                    'update_frequency': 0,  # Invalid range
                    'notification_personality': 'invalid'  # Invalid choice
                }
            ]
        }
        
        # ACT
        is_valid = config_manager.validate_configuration(invalid_config)
        errors = config_manager.get_validation_errors()
        
        # ASSERT
        assert is_valid is False
        assert len(errors) >= 3  # Should have multiple specific errors
        
        # Check that errors are descriptive
        error_text = ' '.join(errors)
        assert 'gemini_api_key' in error_text
        assert 'display_name' in error_text
        assert 'update_frequency' in error_text or 'frequency' in error_text
    
    @patch.dict(os.environ, {
        'GEMINI_API_KEY': 'test_key_from_env',
        'DISPLAY_NAME': 'Test User From Env'
    })
    def test_load_configuration_from_environment(self):
        """
        AAA Test: Configuration should load from environment variables
        """
        # ARRANGE
        import sys
        sys.path.append('/addons/Aiclean/aicleaner')
        from configuration_manager import ConfigurationManager
        
        config_manager = ConfigurationManager()
        
        # ACT
        config = config_manager.load_configuration()
        
        # ASSERT
        assert config is not None
        assert config.get('gemini_api_key') == 'test_key_from_env'
        assert config.get('display_name') == 'Test User From Env'
    
    def test_configuration_manager_handles_missing_environment_gracefully(self):
        """
        AAA Test: Configuration manager should handle missing environment gracefully
        """
        # ARRANGE
        import sys
        sys.path.append('/addons/Aiclean/aicleaner')
        from configuration_manager import ConfigurationManager
        
        config_manager = ConfigurationManager()
        
        # ACT
        config = config_manager.load_configuration()
        
        # ASSERT
        assert config is not None
        assert isinstance(config, dict)
        # Should have default values for missing environment variables
        assert 'gemini_api_key' in config
        assert 'display_name' in config
        assert 'zones' in config
    
    def test_configuration_manager_provides_startup_guidance(self):
        """
        AAA Test: Configuration manager should provide startup guidance for missing config
        """
        # ARRANGE
        import sys
        sys.path.append('/addons/Aiclean/aicleaner')
        from configuration_manager import ConfigurationManager

        config_manager = ConfigurationManager()
        empty_config = {}

        # ACT
        is_valid = config_manager.validate_configuration(empty_config)
        guidance = config_manager.get_startup_guidance()

        # ASSERT
        assert is_valid is False
        assert guidance is not None
        assert len(guidance) > 0
        assert 'gemini_api_key' in guidance.lower()
        assert 'configuration' in guidance.lower()

    def test_configuration_with_example_values_validates(self):
        """
        AAA Test: Configuration with example values from config.yaml should validate correctly
        """
        # ARRANGE
        import sys
        sys.path.append('/addons/Aiclean/aicleaner')
        from configuration_manager import ConfigurationManager

        config_manager = ConfigurationManager()

        # Use the example configuration from our updated config.yaml
        example_config = {
            'gemini_api_key': 'test_api_key_123',
            'display_name': 'User',
            'zones': [
                {
                    'name': 'kitchen',
                    'icon': 'mdi:chef-hat',
                    'purpose': 'Keep the kitchen clean and organized',
                    'camera_entity': 'camera.kitchen',
                    'todo_list_entity': 'todo.kitchen_tasks',
                    'update_frequency': 30,
                    'notifications_enabled': True,
                    'notification_service': 'mobile_app_your_phone',
                    'notification_personality': 'default',
                    'notify_on_create': True,
                    'notify_on_complete': True
                }
            ]
        }

        # ACT
        is_valid = config_manager.validate_configuration(example_config)
        errors = config_manager.get_validation_errors()

        # ASSERT
        assert is_valid is True, f"Example configuration should be valid. Errors: {errors}"
        assert len(errors) == 0

    def test_config_schema_includes_all_required_fields_with_examples(self):
        """
        AAA Test: Configuration schema should include all required fields with example values
        """
        # ARRANGE
        import yaml
        import os

        config_path = '/addons/Aiclean/aicleaner/config.yaml'

        # ACT
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)

        # ASSERT
        # Check that schema is at root level, not nested in zones
        assert 'schema' in config_data, "Schema should be at root level"
        schema = config_data['schema']

        # Check required top-level fields
        assert 'gemini_api_key' in schema, "Schema should include gemini_api_key"
        assert 'display_name' in schema, "Schema should include display_name"
        assert 'zones' in schema, "Schema should include zones"

        # Check zone schema includes all required fields
        zone_schema = schema['zones'][0] if isinstance(schema['zones'], list) else schema['zones']
        required_zone_fields = [
            'name', 'icon', 'purpose', 'camera_entity', 'todo_list_entity',
            'update_frequency', 'notifications_enabled', 'notification_service',
            'notification_personality', 'notify_on_create', 'notify_on_complete'
        ]

        for field in required_zone_fields:
            assert field in zone_schema, f"Zone schema should include {field}"

        # Check that options section has example values
        options = config_data.get('options', {})
        assert options.get('gemini_api_key') is not None, "Options should have example gemini_api_key"
        assert options.get('display_name'), "Options should have example display_name"

        # Check that zones have example values for all fields
        if 'zones' in options and options['zones']:
            example_zone = options['zones'][0]
            for field in required_zone_fields:
                assert field in example_zone, f"Example zone should include {field}"
                assert example_zone[field] is not None, f"Example zone {field} should not be null"

    def test_notification_service_field_is_required_in_validation(self):
        """
        AAA Test: notification_service field should be validated as required for zones
        """
        # ARRANGE
        import sys
        sys.path.append('/addons/Aiclean/aicleaner')
        from configuration_manager import ConfigurationManager

        config_manager = ConfigurationManager()
        config_missing_notification_service = {
            'gemini_api_key': 'test_api_key_123',
            'display_name': 'Test User',
            'zones': [
                {
                    'name': 'kitchen',
                    'icon': 'mdi:chef-hat',
                    'purpose': 'Keep kitchen clean',
                    'camera_entity': 'camera.kitchen',
                    'todo_list_entity': 'todo.kitchen_tasks',
                    'update_frequency': 30,
                    'notifications_enabled': True,
                    # Missing notification_service
                    'notification_personality': 'default',
                    'notify_on_create': True,
                    'notify_on_complete': True
                }
            ]
        }

        # ACT
        is_valid = config_manager.validate_configuration(config_missing_notification_service)
        errors = config_manager.get_validation_errors()

        # ASSERT
        assert is_valid is False, "Configuration missing notification_service should fail validation"
        assert any('notification_service' in error for error in errors), f"Should have notification_service error. Errors: {errors}"

    def test_camera_entity_field_is_required_in_validation(self):
        """
        AAA Test: camera_entity field should be validated as required for zones
        """
        # ARRANGE
        import sys
        sys.path.append('/addons/Aiclean/aicleaner')
        from configuration_manager import ConfigurationManager

        config_manager = ConfigurationManager()
        config_missing_camera_entity = {
            'gemini_api_key': 'test_api_key_123',
            'display_name': 'Test User',
            'zones': [
                {
                    'name': 'kitchen',
                    'icon': 'mdi:chef-hat',
                    'purpose': 'Keep kitchen clean',
                    # Missing camera_entity
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
        is_valid = config_manager.validate_configuration(config_missing_camera_entity)
        errors = config_manager.get_validation_errors()

        # ASSERT
        assert is_valid is False, "Configuration missing camera_entity should fail validation"
        assert any('camera_entity' in error for error in errors), f"Should have camera_entity error. Errors: {errors}"

    def test_todo_list_entity_field_is_required_in_validation(self):
        """
        AAA Test: todo_list_entity field should be validated as required for zones
        """
        # ARRANGE
        import sys
        sys.path.append('/addons/Aiclean/aicleaner')
        from configuration_manager import ConfigurationManager

        config_manager = ConfigurationManager()
        config_missing_todo_entity = {
            'gemini_api_key': 'test_api_key_123',
            'display_name': 'Test User',
            'zones': [
                {
                    'name': 'kitchen',
                    'icon': 'mdi:chef-hat',
                    'purpose': 'Keep kitchen clean',
                    'camera_entity': 'camera.kitchen',
                    # Missing todo_list_entity
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
        is_valid = config_manager.validate_configuration(config_missing_todo_entity)
        errors = config_manager.get_validation_errors()

        # ASSERT
        assert is_valid is False, "Configuration missing todo_list_entity should fail validation"
        assert any('todo_list_entity' in error for error in errors), f"Should have todo_list_entity error. Errors: {errors}"


    def test_home_assistant_ui_configuration_format(self):
        """
        AAA Test: Configuration should be in correct format for Home Assistant UI
        """
        # ARRANGE
        import yaml

        config_path = '/addons/Aiclean/aicleaner/config.yaml'

        # ACT
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)

        # ASSERT
        # Verify Home Assistant addon structure
        assert 'name' in config_data, "Config should have addon name"
        assert 'version' in config_data, "Config should have version"
        assert 'slug' in config_data, "Config should have slug"
        assert 'options' in config_data, "Config should have options section"
        assert 'schema' in config_data, "Config should have schema section"

        # Verify all fields have example values for UI
        options = config_data['options']
        assert options['gemini_api_key'] != None, "gemini_api_key should have example value"
        assert options['display_name'] != None, "display_name should have example value"

        # Verify zone example has all required fields with values
        example_zone = options['zones'][0]
        required_fields = [
            'name', 'icon', 'purpose', 'camera_entity', 'todo_list_entity',
            'update_frequency', 'notifications_enabled', 'notification_service',
            'notification_personality', 'notify_on_create', 'notify_on_complete'
        ]

        for field in required_fields:
            assert field in example_zone, f"Example zone missing field: {field}"
            assert example_zone[field] is not None, f"Example zone field {field} should not be null"

        # Verify schema matches options structure
        schema = config_data['schema']
        assert 'gemini_api_key' in schema, "Schema should include gemini_api_key"
        assert 'display_name' in schema, "Schema should include display_name"
        assert 'zones' in schema, "Schema should include zones"

        # Verify zone schema has all required fields
        zone_schema = schema['zones'][0]
        for field in required_fields:
            assert field in zone_schema, f"Zone schema missing field: {field}"


class TestConfigurationIntegration:
    """Test configuration integration with main application"""

    def test_aicleaner_uses_configuration_manager(self):
        """
        AAA Test: AICleaner should use configuration manager for validation
        """
        # ARRANGE
        import sys
        sys.path.append('/addons/Aiclean/aicleaner')

        # ACT & ASSERT
        try:
            from aicleaner import AICleaner
            # This should fail with missing configuration, but in a controlled way
            app = AICleaner()
            integration_success = False  # Should not reach here
        except ValueError as e:
            # Expected - configuration validation should fail gracefully
            error_message = str(e)
            integration_success = 'gemini_api_key' in error_message
        except Exception as e:
            integration_success = False
            error_message = str(e)

        assert integration_success, f"AICleaner should fail gracefully with helpful error: {error_message if 'error_message' in locals() else 'No error message'}"
    
    def test_aicleaner_provides_helpful_startup_messages(self):
        """
        AAA Test: AICleaner should provide helpful startup messages for configuration issues
        """
        # ARRANGE
        import sys
        sys.path.append('/addons/Aiclean/aicleaner')

        # ACT
        # This should provide helpful error messages
        try:
            from aicleaner import AICleaner
            app = AICleaner()
            startup_success = False  # Should not reach here
        except ValueError as e:
            # Expected - should provide helpful error message
            error_message = str(e)
            startup_success = 'Configuration validation failed' in error_message
        except SystemExit:
            # Also acceptable for missing configuration
            startup_success = True
        except Exception as e:
            startup_success = False
            error_message = str(e)

        # ASSERT
        assert startup_success, f"AICleaner should provide helpful error messages: {error_message if 'error_message' in locals() else 'No error message'}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
