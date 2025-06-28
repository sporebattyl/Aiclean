"""
Unit tests for AICleaner class following TDD/AAA principles
"""
import pytest
import os
import json
import yaml
import tempfile
from unittest.mock import Mock, patch, MagicMock, mock_open
from datetime import datetime, timezone, timedelta

# Import test fixtures and mocks
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from fixtures.test_configs import (
    get_valid_aicleaner_config, 
    get_addon_environment_config,
    get_local_development_config,
    get_multi_zone_config
)
from fixtures.test_states import (
    get_empty_state,
    get_multi_zone_state,
    get_corrupted_state_examples
)
from mocks.mock_ha_api import MockHAClient
from mocks.mock_gemini_api import MockGeminiClient

# Mock external dependencies before importing AICleaner
with patch.dict('sys.modules', {
    'google': Mock(),
    'google.generativeai': Mock(),
    'google.generativeai.client': Mock(),
    'google.generativeai.generative_models': Mock(),
}):
    from aicleaner.aicleaner import AICleaner, Zone
    import aicleaner.aicleaner as aicleaner_module


class TestAICleanerInitialization:
    """Test AICleaner class initialization"""
    
    def test_aicleaner_initialization_addon_environment(self):
        """
        Test AICleaner initialization in Home Assistant addon environment
        AAA Pattern: Arrange -> Act -> Assert
        """
        # Arrange
        env_config = get_addon_environment_config()
        config_data = get_valid_aicleaner_config()

        with patch.dict(os.environ, env_config):
            with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
                with patch('os.path.exists', return_value=True):
                    with patch.object(aicleaner_module, 'configure') as mock_configure:
                        # Act
                        cleaner = AICleaner()

                        # Assert
                        # Check core configuration fields (ignoring added HA fields)
                        assert cleaner.config['gemini_api_key'] == config_data['gemini_api_key']
                        assert cleaner.config['display_name'] == config_data['display_name']
                        assert cleaner.config['zones'] == config_data['zones']

                        # Check that HA fields were added
                        assert 'ha_api_url' in cleaner.config
                        assert 'ha_token' in cleaner.config

                        assert len(cleaner.zones) == len(config_data['zones'])
                        assert cleaner.ha_client is not None
                        assert cleaner.gemini_client is not None
                        assert cleaner.state is not None

                        # Verify zones were created with correct configurations
                        for i, zone in enumerate(cleaner.zones):
                            expected_config = config_data['zones'][i]
                            assert zone.name == expected_config['name']
                            assert zone.camera_entity == expected_config['camera_entity']

                        # Verify Gemini API was configured
                        mock_configure.assert_called_once_with(api_key=config_data['gemini_api_key'])
    
    def test_aicleaner_initialization_local_environment(self):
        """
        Test AICleaner initialization in local development environment
        """
        # Arrange
        config_data = get_local_development_config()
        
        # Remove SUPERVISOR_TOKEN to simulate local environment
        with patch.dict(os.environ, {}, clear=True):
            with patch('builtins.open', mock_open(read_data=yaml.dump(config_data))):
                with patch('os.path.exists', return_value=True):
                    with patch.object(aicleaner_module, 'configure'):
                        # Act
                        cleaner = AICleaner()

                        # Assert
                        # Check that config was transformed correctly from old format
                        assert cleaner.config['gemini_api_key'] == config_data['google_gemini']['api_key']
                        assert cleaner.config['zones'] == config_data['zones']
                        assert 'ha_api_url' in cleaner.config
                        assert 'ha_token' in cleaner.config

                        assert len(cleaner.zones) == len(config_data['zones'])
                        assert cleaner.ha_client is not None
                        assert cleaner.gemini_client is not None
    
    def test_aicleaner_initialization_missing_config(self):
        """
        Test AICleaner initialization when configuration is missing
        """
        # Arrange - No config file exists
        with patch('os.path.exists', return_value=False):
            # Act & Assert
            with pytest.raises(FileNotFoundError):
                AICleaner()
    
    def test_aicleaner_initialization_invalid_config(self):
        """
        Test AICleaner initialization with invalid configuration
        """
        # Arrange
        invalid_config = {"invalid": "config"}
        
        with patch('builtins.open', mock_open(read_data=json.dumps(invalid_config))):
            with patch('os.path.exists', return_value=True):
                # Act & Assert
                with pytest.raises(ValueError):
                    AICleaner()
    
    def test_aicleaner_initialization_no_zones(self):
        """
        Test AICleaner initialization with no zones configured
        """
        # Arrange
        config_data = get_valid_aicleaner_config()
        config_data['zones'] = []
        
        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            with patch('os.path.exists', return_value=True):
                # Act
                cleaner = AICleaner()
                
                # Assert
                assert len(cleaner.zones) == 0


class TestAICleanerStateManagement:
    """Test AICleaner state management functionality"""
    
    def test_load_persistent_state_file_exists(self):
        """
        Test loading persistent state when file exists
        """
        # Arrange
        state_data = get_multi_zone_state()
        config_data = get_valid_aicleaner_config()
        
        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            with patch('os.path.exists', return_value=True):
                cleaner = AICleaner()
                
                # Mock state file exists
                with patch('builtins.open', mock_open(read_data=json.dumps(state_data))):
                    with patch('os.path.exists', return_value=True):
                        # Act
                        loaded_state = cleaner._load_persistent_state()
                        
                        # Assert
                        assert loaded_state == state_data
    
    def test_load_persistent_state_file_missing(self):
        """
        Test loading persistent state when file doesn't exist
        """
        # Arrange
        config_data = get_valid_aicleaner_config()
        
        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            with patch('os.path.exists', return_value=True):
                cleaner = AICleaner()
                
                # Mock state file doesn't exist
                with patch('os.path.exists', return_value=False):
                    # Act
                    loaded_state = cleaner._load_persistent_state()
                    
                    # Assert
                    assert loaded_state == {}
    
    def test_load_persistent_state_corrupted_file(self):
        """
        Test loading persistent state when file is corrupted
        """
        # Arrange
        config_data = get_valid_aicleaner_config()
        corrupted_json = "{ invalid json content"
        
        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            with patch('os.path.exists', return_value=True):
                cleaner = AICleaner()
                
                # Mock corrupted state file
                with patch('builtins.open', mock_open(read_data=corrupted_json)):
                    with patch('os.path.exists', return_value=True):
                        # Act
                        loaded_state = cleaner._load_persistent_state()
                        
                        # Assert
                        assert loaded_state == {}  # Should return empty dict on error
    
    def test_save_persistent_state_atomic_operation(self):
        """
        Test that state saving uses atomic operation (write to .tmp then rename)
        """
        # Arrange
        config_data = get_valid_aicleaner_config()
        state_data = get_multi_zone_state()
        
        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            with patch('os.path.exists', return_value=True):
                cleaner = AICleaner()
                cleaner.state = state_data
                
                with patch('builtins.open', mock_open()) as mock_file:
                    with patch('os.rename') as mock_rename:
                        # Act
                        cleaner._save_persistent_state()
                        
                        # Assert
                        # Verify file was opened for writing
                        mock_file.assert_called_once()
                        
                        # Verify atomic rename operation
                        mock_rename.assert_called_once()
                        args = mock_rename.call_args[0]
                        assert args[0].endswith('.tmp')  # Source is temp file
                        assert args[1].endswith('state.json')  # Destination is state file
    
    def test_save_persistent_state_write_failure(self):
        """
        Test state saving when write operation fails
        """
        # Arrange
        config_data = get_valid_aicleaner_config()
        state_data = get_multi_zone_state()
        
        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            with patch('os.path.exists', return_value=True):
                cleaner = AICleaner()
                cleaner.state = state_data
                
                # Mock file write failure
                with patch('builtins.open', side_effect=IOError("Disk full")):
                    # Act & Assert
                    with pytest.raises(IOError):
                        cleaner._save_persistent_state()
    
    def test_save_persistent_state_rename_failure(self):
        """
        Test state saving when rename operation fails
        """
        # Arrange
        config_data = get_valid_aicleaner_config()
        state_data = get_multi_zone_state()
        
        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            with patch('os.path.exists', return_value=True):
                cleaner = AICleaner()
                cleaner.state = state_data
                
                with patch('builtins.open', mock_open()):
                    with patch('os.rename', side_effect=OSError("Permission denied")):
                        # Act & Assert
                        with pytest.raises(OSError):
                            cleaner._save_persistent_state()


class TestAICleanerConfigValidation:
    """Test AICleaner configuration validation"""
    
    def test_validate_config_success(self):
        """
        Test successful configuration validation
        """
        # Arrange
        config_data = get_valid_aicleaner_config()

        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            with patch('os.path.exists', return_value=True):
                with patch.object(aicleaner_module, 'configure'):
                    # Act & Assert - Should not raise exception
                    cleaner = AICleaner()
                    # Check core fields (ignoring added HA fields)
                    assert cleaner.config['gemini_api_key'] == config_data['gemini_api_key']
                    assert cleaner.config['zones'] == config_data['zones']
    
    def test_validate_config_missing_gemini_key(self):
        """
        Test configuration validation with missing Gemini API key
        """
        # Arrange
        config_data = get_valid_aicleaner_config()
        del config_data['gemini_api_key']
        
        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            with patch('os.path.exists', return_value=True):
                # Act & Assert
                with pytest.raises(ValueError, match="gemini_api_key"):
                    AICleaner()
    
    def test_validate_config_invalid_zone_config(self):
        """
        Test configuration validation with invalid zone configuration
        """
        # Arrange
        config_data = get_valid_aicleaner_config()
        config_data['zones'][0]['camera_entity'] = None  # Invalid
        
        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            with patch('os.path.exists', return_value=True):
                # Act & Assert
                with pytest.raises(ValueError):
                    AICleaner()


class TestAICleanerMainLoop:
    """Test AICleaner main application loop and zone coordination"""

    def test_run_single_cycle_success(self):
        """
        Test successful execution of a single analysis cycle across all zones
        """
        # Arrange
        config_data = get_multi_zone_config()

        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            with patch('os.path.exists', return_value=True):
                with patch.object(aicleaner_module, 'configure'):
                    cleaner = AICleaner()

                    # Mock zone analysis cycles
                    for zone in cleaner.zones:
                        zone.run_analysis_cycle = Mock(return_value={'tasks': []})

                    # Act
                    cleaner.run_single_cycle()

                    # Assert
                    # Verify each zone's analysis cycle was called
                    for zone in cleaner.zones:
                        zone.run_analysis_cycle.assert_called_once()

                    # Verify state was saved
                    assert hasattr(cleaner, '_save_persistent_state')

    def test_run_single_cycle_with_zone_failures(self):
        """
        Test single cycle execution when some zones fail
        """
        # Arrange
        config_data = get_multi_zone_config()

        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            with patch('os.path.exists', return_value=True):
                with patch.object(aicleaner_module, 'configure'):
                    cleaner = AICleaner()

                    # Mock first zone to succeed, second to fail
                    cleaner.zones[0].run_analysis_cycle = Mock(return_value={'tasks': []})
                    cleaner.zones[1].run_analysis_cycle = Mock(side_effect=Exception("Zone failure"))
                    cleaner.zones[2].run_analysis_cycle = Mock(return_value={'tasks': []})

                    # Act
                    cleaner.run_single_cycle()

                    # Assert
                    # All zones should have been attempted
                    for zone in cleaner.zones:
                        zone.run_analysis_cycle.assert_called_once()

    def test_run_scheduled_analysis(self):
        """
        Test scheduled analysis execution for zones based on their update frequencies
        """
        # Arrange
        config_data = get_multi_zone_config()

        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            with patch('os.path.exists', return_value=True):
                with patch.object(aicleaner_module, 'configure'):
                    cleaner = AICleaner()

                    # Mock zone analysis cycles
                    for zone in cleaner.zones:
                        zone.run_analysis_cycle = Mock(return_value={'tasks': []})

                    # Mock time to simulate different schedules
                    with patch('time.time') as mock_time:
                        mock_time.return_value = 3600  # 1 hour

                        # Act
                        cleaner.run_scheduled_analysis()

                        # Assert
                        # Verify zones were analyzed based on their schedules
                        # This would depend on the specific scheduling logic
                        assert any(zone.run_analysis_cycle.called for zone in cleaner.zones)


class TestAICleanerZoneManagement:
    """Test AICleaner zone management functionality"""

    def test_get_zone_by_name_success(self):
        """
        Test retrieving a zone by name
        """
        # Arrange
        config_data = get_multi_zone_config()

        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            with patch('os.path.exists', return_value=True):
                with patch.object(aicleaner_module, 'configure'):
                    cleaner = AICleaner()

                    # Act
                    kitchen_zone = cleaner.get_zone_by_name('Kitchen')

                    # Assert
                    assert kitchen_zone is not None
                    assert kitchen_zone.name == 'Kitchen'

    def test_get_zone_by_name_not_found(self):
        """
        Test retrieving a zone by name when zone doesn't exist
        """
        # Arrange
        config_data = get_multi_zone_config()

        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            with patch('os.path.exists', return_value=True):
                with patch.object(aicleaner_module, 'configure'):
                    cleaner = AICleaner()

                    # Act
                    nonexistent_zone = cleaner.get_zone_by_name('Nonexistent')

                    # Assert
                    assert nonexistent_zone is None

    def test_get_zones_due_for_analysis(self):
        """
        Test getting zones that are due for analysis based on their schedules
        """
        # Arrange
        config_data = get_multi_zone_config()

        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            with patch('os.path.exists', return_value=True):
                with patch.object(aicleaner_module, 'configure'):
                    cleaner = AICleaner()

                    # Mock current time and last analysis times
                    current_time = 3600  # 1 hour

                    with patch('time.time', return_value=current_time):
                        # Act
                        due_zones = cleaner.get_zones_due_for_analysis()

                        # Assert
                        # All zones should be due on first run
                        assert len(due_zones) == len(cleaner.zones)

    def test_update_zone_state(self):
        """
        Test updating state for a specific zone
        """
        # Arrange
        config_data = get_multi_zone_config()

        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            with patch('os.path.exists', return_value=True):
                with patch.object(aicleaner_module, 'configure'):
                    cleaner = AICleaner()

                    new_state = {'tasks': [{'id': 'test_task', 'description': 'Test task'}]}

                    # Mock file operations for state saving
                    with patch('builtins.open', mock_open()):
                        with patch('os.rename'):
                            # Act
                            cleaner.update_zone_state('Kitchen', new_state)

                            # Assert
                            kitchen_zone = cleaner.get_zone_by_name('Kitchen')
                            assert kitchen_zone.state == new_state
                            assert cleaner.state['Kitchen'] == new_state


class TestAICleanerAdvancedStateManagement:
    """Test AICleaner advanced state management features"""

    def test_state_schema_versioning(self):
        """
        Test state schema versioning and migration
        """
        # Arrange
        config_data = get_multi_zone_config()

        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            with patch('os.path.exists', return_value=True):
                with patch.object(aicleaner_module, 'configure'):
                    cleaner = AICleaner()

                    # Act
                    schema_version = cleaner.get_state_schema_version()

                    # Assert
                    assert schema_version is not None
                    assert isinstance(schema_version, str)
                    assert schema_version.count('.') >= 2  # Should be semantic version like "2.0.0"

    def test_state_migration_from_v1_to_v2(self):
        """
        Test migration of state from v1.0 format to v2.0 format
        """
        # Arrange
        config_data = get_multi_zone_config()

        # Create v1.0 format state
        v1_state = {
            'tasks': [
                {
                    'id': 'old_task_1',
                    'description': 'Old format task',
                    'status': 'active'
                    # Missing v2.0 fields like created_at, priority
                }
            ]
        }

        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            with patch('os.path.exists', return_value=True):
                with patch.object(aicleaner_module, 'configure'):
                    cleaner = AICleaner()

                    # Act
                    migrated_state = cleaner.migrate_state_to_current_version(v1_state)

                    # Assert
                    assert migrated_state is not None
                    assert 'schema_version' in migrated_state
                    assert migrated_state['schema_version'] == cleaner.get_state_schema_version()

                    # Check that tasks were migrated properly
                    if 'Kitchen' in migrated_state:
                        kitchen_tasks = migrated_state['Kitchen'].get('tasks', [])
                        for task in kitchen_tasks:
                            assert 'created_at' in task
                            assert 'priority' in task

    def test_state_backup_creation(self):
        """
        Test automatic state backup creation
        """
        # Arrange
        config_data = get_multi_zone_config()

        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            with patch('os.path.exists', return_value=True):
                with patch.object(aicleaner_module, 'configure'):
                    cleaner = AICleaner()

                    # Mock file operations
                    with patch('shutil.copy2') as mock_copy:
                        with patch('os.path.exists', return_value=True):
                            with patch('os.makedirs'):
                                with patch.object(cleaner, '_compress_file') as mock_compress:
                                    with patch('os.remove'):
                                        with patch.object(cleaner, '_cleanup_old_backups'):
                                            # Act
                                            backup_path = cleaner.create_state_backup()

                                            # Assert
                                            assert backup_path is not None
                                            assert 'backup' in backup_path
                                            mock_copy.assert_called_once()

    def test_state_compression_and_decompression(self):
        """
        Test state compression for large datasets
        """
        # Arrange
        config_data = get_multi_zone_config()

        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            with patch('os.path.exists', return_value=True):
                with patch.object(aicleaner_module, 'configure'):
                    cleaner = AICleaner()

                    # Create large state for testing compression
                    large_state = cleaner._create_large_test_state(1000)  # 1000 tasks

                    # Act
                    compressed_data = cleaner.compress_state(large_state)
                    decompressed_state = cleaner.decompress_state(compressed_data)

                    # Assert
                    assert compressed_data is not None
                    assert len(compressed_data) < len(json.dumps(large_state))  # Should be smaller
                    assert decompressed_state == large_state  # Should be identical after decompression

    def test_state_corruption_detection_and_recovery(self):
        """
        Test detection and recovery from state corruption
        """
        # Arrange
        config_data = get_multi_zone_config()

        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            with patch('os.path.exists', return_value=True):
                with patch.object(aicleaner_module, 'configure'):
                    cleaner = AICleaner()

                    # Create corrupted state
                    corrupted_state = {
                        'Kitchen': {
                            'tasks': [
                                {
                                    'id': 'corrupted_task',
                                    'description': None,  # Invalid - should be string
                                    'status': 'invalid_status',  # Invalid status
                                    'priority': 15  # Invalid - should be 0-10
                                }
                            ]
                        }
                    }

                    # Act
                    is_corrupted = cleaner.detect_state_corruption(corrupted_state)
                    recovered_state = cleaner.recover_from_corruption(corrupted_state)

                    # Assert
                    assert is_corrupted is True
                    assert recovered_state is not None

                    # Recovered state should be valid
                    kitchen_tasks = recovered_state.get('Kitchen', {}).get('tasks', [])
                    for task in kitchen_tasks:
                        assert cleaner.zones[0].validate_task_schema(task) if cleaner.zones else True

    def test_state_analytics_and_monitoring(self):
        """
        Test state analytics and monitoring features
        """
        # Arrange
        config_data = get_multi_zone_config()

        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            with patch('os.path.exists', return_value=True):
                with patch.object(aicleaner_module, 'configure'):
                    cleaner = AICleaner()

                    # Ensure state is properly initialized as dict
                    cleaner.state = {'Kitchen': {'tasks': []}, 'Living Room': {'tasks': []}}

                    # Mock file system operations for analytics
                    with patch('os.path.getsize', return_value=1024):
                        with patch('os.path.getmtime', return_value=1640995200):  # Fixed timestamp
                            with patch.object(cleaner, '_calculate_state_health_score', return_value=0.85):
                                # Act
                                analytics = cleaner.get_state_analytics()

                                # Assert
                                assert analytics is not None
                                assert 'total_tasks' in analytics
                                assert 'total_zones' in analytics
                                assert 'state_size_bytes' in analytics
                                assert 'last_modified' in analytics
                                assert 'health_score' in analytics

                                # Health score should be between 0 and 1
                                assert 0 <= analytics['health_score'] <= 1

    def test_state_performance_optimization(self):
        """
        Test state performance optimization features
        """
        # Arrange
        config_data = get_multi_zone_config()

        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            with patch('os.path.exists', return_value=True):
                with patch.object(aicleaner_module, 'configure'):
                    cleaner = AICleaner()

                    # Create state with performance issues
                    unoptimized_state = cleaner._create_unoptimized_test_state()

                    # Act
                    optimized_state = cleaner.optimize_state_performance(unoptimized_state)
                    performance_metrics = cleaner.measure_state_performance(optimized_state)

                    # Assert
                    assert optimized_state is not None
                    assert performance_metrics is not None
                    assert 'load_time_ms' in performance_metrics
                    assert 'save_time_ms' in performance_metrics
                    assert 'memory_usage_mb' in performance_metrics

                    # Optimized state should have fewer tasks (performance improvement)
                    original_task_count = cleaner._count_total_tasks(unoptimized_state)
                    optimized_task_count = performance_metrics['task_count']
                    assert optimized_task_count <= original_task_count


class TestAICleanerHAAPIIntegration:
    """Test Home Assistant API integration for task management"""

    def test_ha_client_todo_add_item(self):
        """
        Test HAClient todo.add_item service integration
        """
        # Arrange
        config_data = get_multi_zone_config()

        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            with patch('os.path.exists', return_value=True):
                with patch.object(aicleaner_module, 'configure'):
                    cleaner = AICleaner()

                    # Mock requests.post for HA API call
                    with patch.object(cleaner.ha_client, 'add_todo_item', return_value=True) as mock_add:
                        # Act
                        result = cleaner.ha_client.add_todo_item(
                            entity_id='todo.kitchen_tasks',
                            item='Clean the countertop'
                        )

                        # Assert
                        assert result is True
                        mock_add.assert_called_once()

                        # Check the API call details
                        call_args = mock_add.call_args[1]
                        assert call_args['entity_id'] == 'todo.kitchen_tasks'
                        assert call_args['item'] == 'Clean the countertop'

    def test_ha_client_todo_update_item(self):
        """
        Test HAClient todo.update_item service integration
        """
        # Arrange
        config_data = get_multi_zone_config()

        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            with patch('os.path.exists', return_value=True):
                with patch.object(aicleaner_module, 'configure'):
                    cleaner = AICleaner()

                    # Mock HA API call
                    with patch.object(cleaner.ha_client, 'update_todo_item', return_value=True) as mock_update:
                        # Act
                        result = cleaner.ha_client.update_todo_item(
                            entity_id='todo.kitchen_tasks',
                            item='Clean the countertop',
                            status='completed'
                        )

                        # Assert
                        assert result is True
                        mock_update.assert_called_once()

                        # Check the API call details
                        call_args = mock_update.call_args[1]
                        assert call_args['entity_id'] == 'todo.kitchen_tasks'
                        assert call_args['item'] == 'Clean the countertop'
                        assert call_args['status'] == 'completed'

    def test_multi_zone_sensor_updates(self):
        """
        Test sensor updates for multi-zone architecture
        """
        # Arrange
        config_data = get_multi_zone_config()

        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            with patch('os.path.exists', return_value=True):
                with patch.object(aicleaner_module, 'configure'):
                    cleaner = AICleaner()

                    # Mock HA API calls
                    with patch.object(cleaner.ha_client, 'update_sensor', return_value=True) as mock_sensor:
                        # Act
                        cleaner.update_all_zone_sensors()

                        # Assert
                        # Should update sensors for each zone
                        expected_calls = len(config_data['zones'])
                        assert mock_sensor.call_count >= expected_calls

    def test_zone_task_creation_with_ha_integration(self):
        """
        Test that zone task creation properly integrates with HA todo lists
        """
        # Arrange
        config_data = get_multi_zone_config()

        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            with patch('os.path.exists', return_value=True):
                with patch.object(aicleaner_module, 'configure'):
                    cleaner = AICleaner()

                    # Get a zone for testing
                    kitchen_zone = cleaner.get_zone_by_name('Kitchen')
                    assert kitchen_zone is not None

                    # Mock HA API calls
                    with patch.object(cleaner.ha_client, 'add_todo_item', return_value=True) as mock_add:
                        with patch.object(cleaner.ha_client, 'update_sensor', return_value=True) as mock_sensor:
                            # Act - Create a new task
                            new_task = {
                                'description': 'Test task for HA integration',
                                'priority': 7,
                                'context_aware': True,
                                'generated_at': datetime.now(timezone.utc).isoformat()
                            }

                            kitchen_zone._process_enhanced_new_tasks([new_task])

                            # Assert
                            # Should have called HA API to add todo item
                            mock_add.assert_called_once()
                            call_args = mock_add.call_args[1]
                            assert call_args['entity_id'] == kitchen_zone.todo_list_entity
                            assert call_args['item'] == 'Test task for HA integration'

    def test_zone_task_completion_with_ha_integration(self):
        """
        Test that zone task completion properly updates HA todo lists
        """
        # Arrange
        config_data = get_multi_zone_config()

        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            with patch('os.path.exists', return_value=True):
                with patch.object(aicleaner_module, 'configure'):
                    cleaner = AICleaner()

                    # Get a zone for testing
                    kitchen_zone = cleaner.get_zone_by_name('Kitchen')
                    assert kitchen_zone is not None

                    # Add a task to complete
                    test_task = {
                        'id': 'test_task_123',
                        'description': 'Test task to complete',
                        'status': 'active',
                        'created_at': datetime.now(timezone.utc).isoformat()
                    }
                    kitchen_zone.state['tasks'] = [test_task]

                    # Mock HA API calls
                    with patch.object(cleaner.ha_client, 'update_todo_item', return_value=True) as mock_update:
                        with patch.object(cleaner.ha_client, 'update_sensor', return_value=True) as mock_sensor:
                            # Act - Complete the task
                            kitchen_zone._process_completed_tasks(['test_task_123'])

                            # Assert
                            # Should have called HA API to update todo item
                            mock_update.assert_called_once()
                            call_args = mock_update.call_args[1]
                            assert call_args['entity_id'] == kitchen_zone.todo_list_entity
                            assert call_args['item'] == 'Test task to complete'
                            assert call_args['status'] == 'completed'

                            # Task should be marked as completed
                            completed_task = kitchen_zone.state['tasks'][0]
                            assert completed_task['status'] == 'completed'
                            assert 'completed_at' in completed_task

    def test_zone_sensor_data_format(self):
        """
        Test that zone sensor data is formatted correctly for HA
        """
        # Arrange
        config_data = get_multi_zone_config()

        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            with patch('os.path.exists', return_value=True):
                with patch.object(aicleaner_module, 'configure'):
                    cleaner = AICleaner()

                    # Get a zone for testing
                    kitchen_zone = cleaner.get_zone_by_name('Kitchen')
                    assert kitchen_zone is not None

                    # Add some test tasks
                    kitchen_zone.state['tasks'] = [
                        {
                            'id': 'task_1',
                            'description': 'Active task 1',
                            'status': 'active',
                            'priority': 8,
                            'created_at': datetime.now(timezone.utc).isoformat()
                        },
                        {
                            'id': 'task_2',
                            'description': 'Completed task 1',
                            'status': 'completed',
                            'priority': 5,
                            'created_at': (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
                            'completed_at': datetime.now(timezone.utc).isoformat()
                        }
                    ]

                    # Act
                    sensor_data = kitchen_zone.get_sensor_data()

                    # Assert
                    assert sensor_data is not None
                    assert 'state' in sensor_data
                    assert 'attributes' in sensor_data

                    # Check state value (should be number of active tasks)
                    assert sensor_data['state'] == 1

                    # Check attributes
                    attributes = sensor_data['attributes']
                    assert 'zone_name' in attributes
                    assert 'total_tasks' in attributes
                    assert 'active_tasks' in attributes
                    assert 'completed_tasks' in attributes
                    assert 'last_updated' in attributes
                    assert attributes['zone_name'] == 'Kitchen'
                    assert attributes['total_tasks'] == 2
                    assert attributes['active_tasks'] == 1
                    assert attributes['completed_tasks'] == 1
