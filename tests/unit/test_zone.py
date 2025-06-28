"""
Unit tests for Zone class following TDD/AAA principles
"""
import pytest
import os
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

# Import test fixtures and mocks
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from fixtures.test_configs import (
    get_valid_zone_config,
    get_invalid_zone_configs,
    get_empty_zone_state,
    get_zone_with_duplicate_tasks,
    get_zone_with_old_tasks,
    get_zone_with_task_history,
    get_zone_with_performance_history,
    get_zone_with_related_tasks,
    get_zone_with_mixed_priority_tasks,
    get_zone_with_analytics_data,
    get_zone_with_learning_data
)
from fixtures.test_states import (
    get_single_zone_with_active_tasks, 
    get_active_tasks_for_zone,
    create_test_task
)
from mocks.mock_ha_api import MockHAClient
from mocks.mock_gemini_api import MockGeminiClient

# Mock external dependencies before importing Zone
with patch.dict('sys.modules', {
    'google': Mock(),
    'google.generativeai': Mock(),
    'google.generativeai.client': Mock(),
    'google.generativeai.generative_models': Mock(),
}):
    from aicleaner.aicleaner import Zone
    import aicleaner.aicleaner as aicleaner_module


class TestZoneInitialization:
    """Test Zone class initialization"""
    
    def test_zone_initialization_success(self):
        """
        Test successful Zone initialization with valid configuration
        AAA Pattern: Arrange -> Act -> Assert
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = {'tasks': []}
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()
        
        # Act
        zone = Zone(zone_config, zone_state, ha_client, gemini_client)
        
        # Assert
        assert zone.name == zone_config['name']
        assert zone.camera_entity == zone_config['camera_entity']
        assert zone.todo_list_entity == zone_config['todo_list_entity']
        assert zone.update_frequency == zone_config['update_frequency']
        assert zone.notifications_enabled == zone_config['notifications_enabled']
        assert zone.notification_personality == zone_config['notification_personality']
        assert zone.state == zone_state
        assert zone.ha_client == ha_client
        assert zone.gemini_client == gemini_client
    
    def test_zone_initialization_invalid_config(self):
        """
        Test Zone initialization with invalid configurations
        """
        # Arrange
        invalid_configs = get_invalid_zone_configs()
        zone_state = {'tasks': []}
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()
        
        for invalid_config in invalid_configs:
            # Act & Assert
            with pytest.raises(ValueError):
                Zone(invalid_config, zone_state, ha_client, gemini_client)
    
    def test_zone_initialization_missing_clients(self):
        """
        Test Zone initialization with missing client dependencies
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = {'tasks': []}
        
        # Act & Assert - Missing HA client
        with pytest.raises(ValueError):
            Zone(zone_config, zone_state, None, MockGeminiClient())
        
        # Act & Assert - Missing Gemini client
        with pytest.raises(ValueError):
            Zone(zone_config, zone_state, MockHAClient(), None)


class TestZoneCameraSnapshot:
    """Test Zone camera snapshot functionality"""
    
    def test_get_camera_snapshot_success(self):
        """
        Test successful camera snapshot capture
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = {'tasks': []}
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()
        zone = Zone(zone_config, zone_state, ha_client, gemini_client)
        
        # Act
        snapshot_path = zone.get_camera_snapshot()
        
        # Assert
        assert snapshot_path is not None
        assert os.path.exists(snapshot_path)
        assert ha_client.call_count('get_camera_snapshot') == 1
        
        # Verify correct API call was made
        last_call = ha_client.get_last_call('get_camera_snapshot')
        assert last_call['entity_id'] == zone_config['camera_entity']
        
        # Cleanup
        if os.path.exists(snapshot_path):
            os.remove(snapshot_path)
    
    def test_get_camera_snapshot_api_failure(self):
        """
        Test camera snapshot capture when HA API fails
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = {'tasks': []}
        ha_client = MockHAClient()
        ha_client.set_failure(True, "Camera not available")
        gemini_client = MockGeminiClient()
        zone = Zone(zone_config, zone_state, ha_client, gemini_client)
        
        # Act
        snapshot_path = zone.get_camera_snapshot()
        
        # Assert
        assert snapshot_path is None
        assert ha_client.call_count('get_camera_snapshot') == 1
    
    def test_get_camera_snapshot_file_path_format(self):
        """
        Test that camera snapshot uses correct file path format
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = {'tasks': []}
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()
        zone = Zone(zone_config, zone_state, ha_client, gemini_client)
        
        # Act
        snapshot_path = zone.get_camera_snapshot()
        
        # Assert
        expected_filename = f"/tmp/{zone_config['name']}_latest.jpg"
        assert snapshot_path == expected_filename
        
        # Cleanup
        if os.path.exists(snapshot_path):
            os.remove(snapshot_path)


class TestZoneTaskAnalysis:
    """Test Zone AI task analysis functionality"""
    
    def test_analyze_image_for_completed_tasks_success(self):
        """
        Test successful completed tasks analysis
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = get_single_zone_with_active_tasks()['Kitchen']
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()

        # Configure mock Gemini response
        completed_task_ids = ['task_1687392000_kitchen_0', 'task_1687392120_kitchen_2']
        gemini_client.add_completed_tasks_response(completed_task_ids)

        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        # Create test image file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(b'test_image_data')
            image_path = temp_file.name

        # Mock PIL Image.open in the aicleaner module
        mock_image = Mock()
        with patch.object(aicleaner_module, 'Image') as mock_image_module:
            mock_image_module.open.return_value = mock_image
            # Act
            result = zone.analyze_image_for_completed_tasks(image_path)

        # Assert
        assert result == completed_task_ids
        assert gemini_client.call_count() == 1

        # Verify correct prompt was used
        active_tasks = [task for task in zone_state['tasks'] if task['status'] == 'active']
        assert gemini_client.verify_completed_tasks_prompt(active_tasks)

        # Cleanup
        os.unlink(image_path)
    
    def test_analyze_image_for_completed_tasks_no_completions(self):
        """
        Test completed tasks analysis when no tasks are completed
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = get_single_zone_with_active_tasks()['Kitchen']
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()

        # Configure mock Gemini response with no completed tasks
        gemini_client.add_completed_tasks_response([])

        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        # Create test image file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(b'test_image_data')
            image_path = temp_file.name

        # Mock PIL Image.open in the aicleaner module
        mock_image = Mock()
        with patch.object(aicleaner_module, 'Image') as mock_image_module:
            mock_image_module.open.return_value = mock_image
            # Act
            result = zone.analyze_image_for_completed_tasks(image_path)

        # Assert
        assert result == []
        assert gemini_client.call_count() == 1

        # Cleanup
        os.unlink(image_path)
    
    def test_analyze_image_for_new_tasks_success(self):
        """
        Test successful new tasks analysis
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = get_single_zone_with_active_tasks()['Kitchen']
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()

        # Configure mock Gemini response
        new_tasks = [
            'Clean the microwave inside and out',
            'Organize the spice rack',
            'Empty the trash can'
        ]
        gemini_client.add_new_tasks_response(new_tasks)

        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        # Create test image file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(b'test_image_data')
            image_path = temp_file.name

        # Mock PIL Image.open in the aicleaner module
        mock_image = Mock()
        with patch.object(aicleaner_module, 'Image') as mock_image_module:
            mock_image_module.open.return_value = mock_image
            # Act
            result = zone.analyze_image_for_new_tasks(image_path)

        # Assert
        assert result == new_tasks
        assert gemini_client.call_count() == 1

        # Verify correct prompt was used
        context = f"This is the {zone_config['name']}. The goal is to '{zone_config['purpose']}'."
        active_task_descriptions = [task['description'] for task in zone_state['tasks'] if task['status'] == 'active']
        ignore_rules = zone_state.get('ignore_rules', [])
        assert gemini_client.verify_new_tasks_prompt(context, active_task_descriptions, ignore_rules)

        # Cleanup
        os.unlink(image_path)

    def test_analyze_image_for_new_tasks_with_ignore_rules(self):
        """
        Test new tasks analysis with ignore rules applied
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = get_single_zone_with_active_tasks()['Kitchen']
        zone_state['ignore_rules'] = [
            'Ignore the fruit bowl on the counter',
            'The decorative vase on the shelf is supposed to be there'
        ]
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()

        # Configure mock Gemini response
        new_tasks = ['Clean the microwave inside and out']
        gemini_client.add_new_tasks_response(new_tasks)

        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        # Create test image file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(b'test_image_data')
            image_path = temp_file.name

        # Mock PIL Image.open in the aicleaner module
        mock_image = Mock()
        with patch.object(aicleaner_module, 'Image') as mock_image_module:
            mock_image_module.open.return_value = mock_image
            # Act
            result = zone.analyze_image_for_new_tasks(image_path)

        # Assert
        assert result == new_tasks

        # Verify ignore rules were included in prompt
        context = f"This is the {zone_config['name']}. The goal is to '{zone_config['purpose']}'."
        active_task_descriptions = [task['description'] for task in zone_state['tasks'] if task['status'] == 'active']
        ignore_rules = zone_state['ignore_rules']
        assert gemini_client.verify_new_tasks_prompt(context, active_task_descriptions, ignore_rules)

        # Cleanup
        os.unlink(image_path)

    def test_analyze_image_gemini_api_failure(self):
        """
        Test image analysis when Gemini API fails
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = get_single_zone_with_active_tasks()['Kitchen']
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()
        gemini_client.set_failure(True, "Gemini API rate limit exceeded")

        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        # Create test image file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(b'test_image_data')
            image_path = temp_file.name

        # Act & Assert
        with pytest.raises(Exception):
            zone.analyze_image_for_completed_tasks(image_path)

        with pytest.raises(Exception):
            zone.analyze_image_for_new_tasks(image_path)

        # Cleanup
        os.unlink(image_path)

    def test_analyze_image_invalid_file_path(self):
        """
        Test image analysis with invalid file path
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = get_single_zone_with_active_tasks()['Kitchen']
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()
        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        # Act
        result_completed = zone.analyze_image_for_completed_tasks('/nonexistent/path.jpg')
        result_new = zone.analyze_image_for_new_tasks('/nonexistent/path.jpg')

        # Assert
        assert result_completed is None
        assert result_new is None
        assert gemini_client.call_count() == 0


class TestZoneNotifications:
    """Test Zone notification functionality"""

    def test_send_notification_task_created(self):
        """
        Test sending notification for task creation
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = {'tasks': []}
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()
        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        context = {
            'task_description': 'Clean the microwave inside and out',
            'zone_name': zone_config['name']
        }

        # Act
        zone.send_notification('task_created', context)

        # Assert
        assert ha_client.call_count('send_notification') == 1
        last_call = ha_client.get_last_call('send_notification')
        assert last_call['service'] == zone_config['notification_service']
        assert context['task_description'] in last_call['message']
        assert context['zone_name'] in last_call['message']

    def test_send_notification_task_completed(self):
        """
        Test sending notification for task completion
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = {'tasks': []}
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()
        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        context = {
            'task_description': 'Load the dirty dishes from the counter into the dishwasher',
            'zone_name': zone_config['name']
        }

        # Act
        zone.send_notification('task_completed', context)

        # Assert
        assert ha_client.call_count('send_notification') == 1
        last_call = ha_client.get_last_call('send_notification')
        assert last_call['service'] == zone_config['notification_service']
        assert context['task_description'] in last_call['message']

    def test_send_notification_disabled(self):
        """
        Test that notifications are not sent when disabled
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_config['notifications_enabled'] = False
        zone_state = {'tasks': []}
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()
        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        context = {'task_description': 'Test task', 'zone_name': zone_config['name']}

        # Act
        zone.send_notification('task_created', context)

        # Assert
        assert ha_client.call_count('send_notification') == 0

    def test_send_notification_personality_formatting(self):
        """
        Test that notification messages are formatted according to personality
        """
        personalities = ['default', 'snarky', 'jarvis', 'roaster', 'comedian', 'sargent']

        for personality in personalities:
            # Arrange
            zone_config = get_valid_zone_config()
            zone_config['notification_personality'] = personality
            zone_state = {'tasks': []}
            ha_client = MockHAClient()
            gemini_client = MockGeminiClient()
            zone = Zone(zone_config, zone_state, ha_client, gemini_client)

            context = {'task_description': 'Test task', 'zone_name': zone_config['name']}

            # Act
            zone.send_notification('task_created', context)

            # Assert
            assert ha_client.call_count('send_notification') == 1
            last_call = ha_client.get_last_call('send_notification')

            # Verify personality-specific formatting is applied
            message = last_call['message']
            if personality == 'snarky':
                assert any(word in message.lower() for word in ['really', 'seriously', 'again'])
            elif personality == 'jarvis':
                assert any(word in message.lower() for word in ['sir', 'madam', 'shall'])
            elif personality == 'roaster':
                assert any(word in message.lower() for word in ['mess', 'disaster', 'chaos'])

            # Reset for next iteration
            ha_client.reset()


class TestZoneAnalysisCycle:
    """Test Zone complete analysis cycle"""

    def test_run_analysis_cycle_full_workflow(self):
        """
        Test complete analysis cycle workflow
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = get_single_zone_with_active_tasks()['Kitchen']
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()

        # Configure mock responses
        completed_task_ids = ['task_1687392000_kitchen_0']
        new_tasks = ['Clean the microwave inside and out']
        gemini_client.add_completed_tasks_response(completed_task_ids)
        gemini_client.add_new_tasks_response(new_tasks)

        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        # Mock PIL Image.open for the analysis cycle
        mock_image = Mock()
        with patch.object(aicleaner_module, 'Image') as mock_image_module:
            mock_image_module.open.return_value = mock_image
            # Act
            updated_state = zone.run_analysis_cycle()

        # Assert
        # Verify camera snapshot was taken
        assert ha_client.call_count('get_camera_snapshot') == 1

        # Verify Gemini was called twice (completed tasks + new tasks)
        assert gemini_client.call_count() == 2

        # Note: HA API integration will be implemented in the next task
        # For now, verify that the enhanced analysis cycle processes tasks correctly
        # The HA API calls will be added when we implement the HA integration task

        # Verify notifications were sent
        expected_notifications = len(completed_task_ids) + len(new_tasks)
        assert ha_client.call_count('send_notification') == expected_notifications

        # Verify state was updated
        assert updated_state is not None

        # Verify completed tasks are marked as completed
        completed_tasks = [task for task in updated_state['tasks'] if task['status'] == 'completed']
        assert len(completed_tasks) == len(completed_task_ids)

        # Verify new tasks were added
        all_task_descriptions = [task['description'] for task in updated_state['tasks']]
        for new_task in new_tasks:
            assert new_task in all_task_descriptions

    def test_run_analysis_cycle_camera_failure(self):
        """
        Test analysis cycle when camera snapshot fails
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = get_single_zone_with_active_tasks()['Kitchen']
        ha_client = MockHAClient()
        ha_client.set_failure(True, "Camera not available")
        gemini_client = MockGeminiClient()
        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        # Act
        updated_state = zone.run_analysis_cycle()

        # Assert
        # Camera snapshot should have been attempted
        assert ha_client.call_count('get_camera_snapshot') == 1

        # No further processing should occur
        assert gemini_client.call_count() == 0
        assert ha_client.call_count('update_todo_item') == 0
        assert ha_client.call_count('add_todo_item') == 0

        # State should remain unchanged
        assert updated_state == zone_state

    def test_run_analysis_cycle_partial_failure(self):
        """
        Test analysis cycle with partial failures (some operations succeed, others fail)
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = get_single_zone_with_active_tasks()['Kitchen']
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()

        # Configure Gemini to succeed for completed tasks but fail for new tasks
        completed_task_ids = ['task_1687392000_kitchen_0']
        gemini_client.add_completed_tasks_response(completed_task_ids)

        # Override the generate_content method to fail on second call
        original_generate_content = gemini_client.generate_content
        call_count = [0]  # Use list to allow modification in nested function

        def failing_generate_content(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call succeeds (completed tasks)
                return original_generate_content(*args, **kwargs)
            else:
                # Second call fails (new tasks)
                raise Exception("Gemini API failure on new tasks")

        gemini_client.generate_content = failing_generate_content

        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        # Mock PIL Image.open for the analysis cycle
        mock_image = Mock()
        with patch.object(aicleaner_module, 'Image') as mock_image_module:
            mock_image_module.open.return_value = mock_image
            # Act
            updated_state = zone.run_analysis_cycle()

        # Assert
        # Completed tasks processing should have succeeded
        assert ha_client.call_count('update_todo_item') == len(completed_task_ids)

        # New tasks processing should have failed, so no new tasks added
        assert ha_client.call_count('add_todo_item') == 0

        # State should reflect completed tasks but no new tasks
        completed_tasks = [task for task in updated_state['tasks'] if task['status'] == 'completed']
        assert len(completed_tasks) == len(completed_task_ids)


class TestZoneEnhancedStateManagement:
    """Test Zone enhanced state management features for Phase 2"""

    def test_validate_task_schema_success(self):
        """
        Test successful task schema validation
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = get_empty_zone_state()
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()

        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        valid_task = {
            'id': 'task_1687392000_kitchen_0',
            'description': 'Clean the countertops',
            'status': 'active',
            'created_at': '2023-06-21T20:00:00Z',
            'priority': 5,
            'confidence_score': 0.85
        }

        # Act
        is_valid = zone.validate_task_schema(valid_task)

        # Assert
        assert is_valid is True

    def test_validate_task_schema_missing_required_fields(self):
        """
        Test task schema validation with missing required fields
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = get_empty_zone_state()
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()

        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        invalid_task = {
            'description': 'Clean the countertops',
            # Missing required fields: id, status, created_at
        }

        # Act
        is_valid = zone.validate_task_schema(invalid_task)

        # Assert
        assert is_valid is False

    def test_validate_task_schema_invalid_status(self):
        """
        Test task schema validation with invalid status
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = get_empty_zone_state()
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()

        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        invalid_task = {
            'id': 'task_1687392000_kitchen_0',
            'description': 'Clean the countertops',
            'status': 'invalid_status',  # Invalid status
            'created_at': '2023-06-21T20:00:00Z'
        }

        # Act
        is_valid = zone.validate_task_schema(invalid_task)

        # Assert
        assert is_valid is False

    def test_calculate_task_priority_high_priority(self):
        """
        Test task priority calculation for high priority tasks
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = get_empty_zone_state()
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()

        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        task_description = "Clean up spilled food on the floor"

        # Act
        priority = zone.calculate_task_priority(task_description)

        # Assert
        assert priority >= 8  # High priority for safety/hygiene issues

    def test_calculate_task_priority_low_priority(self):
        """
        Test task priority calculation for low priority tasks
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = get_empty_zone_state()
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()

        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        task_description = "Organize books on shelf"

        # Act
        priority = zone.calculate_task_priority(task_description)

        # Assert
        assert priority <= 3  # Low priority for organizational tasks

    def test_merge_duplicate_tasks(self):
        """
        Test merging of duplicate or similar tasks
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = get_zone_with_duplicate_tasks()
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()

        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        # Act
        merged_state = zone.merge_duplicate_tasks()

        # Assert
        # Should have fewer tasks after merging duplicates
        original_task_count = len(zone_state['tasks'])
        merged_task_count = len(merged_state['tasks'])
        assert merged_task_count < original_task_count

        # Merged tasks should have higher priority
        merged_tasks = [task for task in merged_state['tasks'] if task.get('merged_from')]
        assert len(merged_tasks) > 0
        assert all(task.get('priority', 0) > 5 for task in merged_tasks)

    def test_expire_old_tasks(self):
        """
        Test automatic expiration of old tasks
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = get_zone_with_old_tasks()
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()

        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        # Act
        updated_state = zone.expire_old_tasks(max_age_days=7)

        # Assert
        # Old tasks should be marked as expired
        expired_tasks = [task for task in updated_state['tasks'] if task.get('status') == 'expired']
        assert len(expired_tasks) > 0

        # Active tasks should only be recent ones
        active_tasks = [task for task in updated_state['tasks'] if task.get('status') == 'active']
        for task in active_tasks:
            created_at = datetime.fromisoformat(task['created_at'].replace('Z', '+00:00'))
            age_days = (datetime.now(timezone.utc) - created_at).days
            assert age_days <= 7


class TestZoneAdvancedAIAnalysis:
    """Test Zone advanced AI analysis features for Phase 2"""

    def test_analyze_with_confidence_scoring(self):
        """
        Test AI analysis with confidence scoring for task completion
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = get_single_zone_with_active_tasks()['Kitchen']
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()

        # Configure mock response with confidence scores
        completion_response = [
            {'task_id': 'task_1687392000_kitchen_0', 'confidence': 0.95},
            {'task_id': 'task_1687392120_kitchen_2', 'confidence': 0.75}
        ]
        gemini_client.add_completed_tasks_response(completion_response)

        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        # Create test image file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(b'test_image_data')
            image_path = temp_file.name

        # Mock PIL Image.open
        mock_image = Mock()
        with patch.object(aicleaner_module, 'Image') as mock_image_module:
            mock_image_module.open.return_value = mock_image

            # Act
            result = zone.analyze_with_confidence_scoring(image_path)

            # Assert
            assert result is not None
            assert 'completed_tasks' in result
            assert 'confidence_scores' in result

            # High confidence tasks should be marked for completion
            high_confidence_tasks = [
                task for task in result['completed_tasks']
                if result['confidence_scores'].get(task, 0) >= 0.9
            ]
            assert len(high_confidence_tasks) > 0

        # Cleanup
        os.unlink(image_path)

    def test_analyze_with_retry_logic(self):
        """
        Test AI analysis with retry logic for failed API calls
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = get_single_zone_with_active_tasks()['Kitchen']
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()

        # Configure mock to fail first two calls, succeed on third
        call_count = [0]
        def failing_generate_content(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 2:
                raise Exception("API rate limit exceeded")
            return Mock(text='["task_1687392000_kitchen_0"]')

        gemini_client.generate_content = failing_generate_content

        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        # Create test image file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(b'test_image_data')
            image_path = temp_file.name

        # Mock PIL Image.open
        mock_image = Mock()
        with patch.object(aicleaner_module, 'Image') as mock_image_module:
            mock_image_module.open.return_value = mock_image

            # Act
            result = zone.analyze_with_retry_logic(image_path, max_retries=3)

            # Assert
            assert result is not None
            assert call_count[0] == 3  # Should have retried 3 times

        # Cleanup
        os.unlink(image_path)

    def test_context_aware_task_generation(self):
        """
        Test context-aware task generation based on zone purpose and history
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_config['purpose'] = 'Keep kitchen clean and organized for cooking'
        zone_state = get_zone_with_task_history()
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()

        # Configure mock response with context-aware tasks
        context_tasks = [
            'Wipe down cutting board after meal prep',
            'Put away cooking utensils in designated spots',
            'Clean stovetop after cooking'
        ]
        gemini_client.add_new_tasks_response(context_tasks)

        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        # Create test image file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(b'test_image_data')
            image_path = temp_file.name

        # Mock PIL Image.open
        mock_image = Mock()
        with patch.object(aicleaner_module, 'Image') as mock_image_module:
            mock_image_module.open.return_value = mock_image

            # Act
            result = zone.generate_context_aware_tasks(image_path)

            # Assert
            assert result is not None
            assert len(result) > 0

            # Tasks should be relevant to kitchen context
            kitchen_keywords = ['cooking', 'kitchen', 'stovetop', 'cutting board']
            context_relevant_tasks = [
                task for task in result
                if any(keyword in task['description'].lower() for keyword in kitchen_keywords)
            ]
            assert len(context_relevant_tasks) > 0

        # Cleanup
        os.unlink(image_path)

    def test_enhanced_prompt_formatting(self):
        """
        Test enhanced prompt formatting with detailed context and instructions
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = get_single_zone_with_active_tasks()['Kitchen']
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()

        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        # Act
        prompt = zone.format_enhanced_completion_prompt()

        # Assert
        assert prompt is not None
        assert len(prompt) > 0

        # Prompt should include enhanced context
        assert zone.name in prompt
        assert zone.purpose in prompt
        assert 'confidence' in prompt.lower()
        assert 'priority' in prompt.lower()

        # Should include active tasks context
        active_tasks = [task for task in zone_state['tasks'] if task.get('status') == 'active']
        for task in active_tasks:
            assert task['description'] in prompt


class TestZoneSmartTaskFeatures:
    """Test Zone smart task features for Phase 2"""

    def test_calculate_zone_performance_metrics(self):
        """
        Test calculation of zone performance metrics
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = get_zone_with_performance_history()
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()

        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        # Act
        metrics = zone.calculate_performance_metrics()

        # Assert
        assert metrics is not None
        assert 'completion_rate' in metrics
        assert 'average_completion_time' in metrics
        assert 'task_creation_rate' in metrics
        assert 'efficiency_score' in metrics

        # Metrics should be within expected ranges
        assert 0 <= metrics['completion_rate'] <= 1
        assert metrics['average_completion_time'] > 0
        assert metrics['efficiency_score'] >= 0

    def test_identify_task_dependencies(self):
        """
        Test identification of task dependencies and relationships
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = get_zone_with_related_tasks()
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()

        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        # Act
        dependencies = zone.identify_task_dependencies()

        # Assert
        assert dependencies is not None
        assert isinstance(dependencies, dict)

        # Should identify logical dependencies
        # e.g., "Clear countertop" should come before "Wipe countertop"
        clear_task_id = None
        wipe_task_id = None

        for task in zone_state['tasks']:
            if 'clear' in task['description'].lower() and 'countertop' in task['description'].lower():
                clear_task_id = task['id']
            elif 'wipe' in task['description'].lower() and 'countertop' in task['description'].lower():
                wipe_task_id = task['id']

        if clear_task_id and wipe_task_id:
            assert wipe_task_id in dependencies
            assert clear_task_id in dependencies[wipe_task_id]

    def test_optimize_task_scheduling(self):
        """
        Test optimization of task scheduling based on priority and dependencies
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = get_zone_with_mixed_priority_tasks()
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()

        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        # Act
        optimized_schedule = zone.optimize_task_scheduling()

        # Assert
        assert optimized_schedule is not None
        assert isinstance(optimized_schedule, list)
        assert len(optimized_schedule) > 0

        # High priority tasks should come first
        priorities = [task.get('priority', 0) for task in optimized_schedule]
        assert priorities == sorted(priorities, reverse=True)

        # Dependencies should be respected
        task_ids = [task['id'] for task in optimized_schedule]
        dependencies = zone.identify_task_dependencies()

        for task_id, deps in dependencies.items():
            if task_id in task_ids:
                task_index = task_ids.index(task_id)
                for dep_id in deps:
                    if dep_id in task_ids:
                        dep_index = task_ids.index(dep_id)
                        assert dep_index < task_index  # Dependency should come first

    def test_generate_task_insights(self):
        """
        Test generation of task insights and recommendations
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = get_zone_with_analytics_data()
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()

        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        # Act
        insights = zone.generate_task_insights()

        # Assert
        assert insights is not None
        assert 'recommendations' in insights
        assert 'patterns' in insights
        assert 'efficiency_tips' in insights

        # Should provide actionable recommendations
        recommendations = insights['recommendations']
        assert len(recommendations) > 0
        assert all(isinstance(rec, str) for rec in recommendations)

        # Should identify patterns
        patterns = insights['patterns']
        assert isinstance(patterns, dict)
        assert 'most_common_tasks' in patterns
        assert 'peak_activity_times' in patterns

    def test_adaptive_task_learning(self):
        """
        Test adaptive learning from task completion patterns
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = get_zone_with_learning_data()
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()

        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        # Act
        learning_updates = zone.apply_adaptive_learning()

        # Assert
        assert learning_updates is not None
        assert 'updated_priorities' in learning_updates
        assert 'new_ignore_rules' in learning_updates
        assert 'optimized_prompts' in learning_updates

        # Should update task priorities based on completion patterns
        updated_priorities = learning_updates['updated_priorities']
        assert isinstance(updated_priorities, dict)

        # Should suggest new ignore rules for frequently dismissed tasks
        new_ignore_rules = learning_updates['new_ignore_rules']
        assert isinstance(new_ignore_rules, list)


class TestZoneEnhancedTwoStageAIAnalysis:
    """Test enhanced two-stage AI analysis with detailed prompts"""

    def test_enhanced_analysis_cycle_with_confidence_scoring(self):
        """
        Test enhanced analysis cycle using confidence scoring for completed tasks
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = get_single_zone_with_active_tasks()['Kitchen']
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()

        # Configure mock to fail basic analysis but succeed with confidence scoring
        gemini_client.add_completion_response([])  # Basic analysis fails
        gemini_client.add_confidence_response([
            {
                'task_id': 'task_1687392000_kitchen_0',
                'confidence': 0.85,
                'reasoning': 'Dishes are loaded in dishwasher'
            }
        ])

        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        # Create test image file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(b'test_image_data')
            image_path = temp_file.name

        # Mock PIL Image.open and file operations
        mock_image = Mock()
        with patch.object(aicleaner_module, 'Image') as mock_image_module:
            mock_image_module.open.return_value = mock_image
            with patch('os.path.exists', return_value=True):
                with patch('os.remove'):
                    with patch.object(zone, 'get_camera_snapshot', return_value=image_path):
                        # Act
                        result_state = zone.run_analysis_cycle()

                        # Assert
                        assert result_state is not None

                        # Check that confidence-based completion was used
                        completed_tasks = [task for task in result_state.get('tasks', [])
                                         if task.get('status') == 'completed']
                        assert len(completed_tasks) > 0

    def test_enhanced_analysis_cycle_with_context_aware_generation(self):
        """
        Test enhanced analysis cycle using context-aware task generation
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_config['purpose'] = 'Keep kitchen clean and organized for cooking'
        zone_state = get_zone_with_task_history()
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()

        # Configure mock for context-aware task generation
        context_tasks = [
            'Wipe down cutting board after meal prep',
            'Put away cooking utensils in designated spots'
        ]
        gemini_client.add_new_tasks_response(context_tasks)

        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        # Create test image file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(b'test_image_data')
            image_path = temp_file.name

        # Mock PIL Image.open and file operations
        mock_image = Mock()
        with patch.object(aicleaner_module, 'Image') as mock_image_module:
            mock_image_module.open.return_value = mock_image
            with patch('os.path.exists', return_value=True):
                with patch('os.remove'):
                    with patch.object(zone, 'get_camera_snapshot', return_value=image_path):
                        # Act
                        result_state = zone.run_analysis_cycle()

                        # Assert
                        assert result_state is not None

                        # Check that context-aware tasks were created
                        active_tasks = [task for task in result_state.get('tasks', [])
                                      if task.get('status') == 'active']

                        # Should have new context-aware tasks
                        context_aware_tasks = [task for task in active_tasks
                                             if task.get('context_aware', False)]
                        assert len(context_aware_tasks) > 0

                        # Tasks should have priority assigned
                        for task in context_aware_tasks:
                            assert 'priority' in task
                            assert 1 <= task['priority'] <= 10

    def test_detailed_prompts_match_design_specification(self):
        """
        Test that the detailed prompts match exactly what's specified in DesignDocument.md
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = get_single_zone_with_active_tasks()['Kitchen']
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()

        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        # Create test image file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(b'test_image_data')
            image_path = temp_file.name

        # Mock PIL Image.open
        mock_image = Mock()
        with patch.object(aicleaner_module, 'Image') as mock_image_module:
            mock_image_module.open.return_value = mock_image

            # Capture the prompts sent to Gemini
            captured_prompts = []

            def capture_generate_content(prompt_and_image):
                captured_prompts.append(prompt_and_image[0])  # First element is the prompt
                return Mock(text='[]')  # Return empty JSON array

            gemini_client.generate_content = capture_generate_content

            # Act - Test completed task analysis
            zone.analyze_image_for_completed_tasks(image_path)

            # Assert - Check Stage 1 prompt matches specification
            stage1_prompt = captured_prompts[0]
            assert "You are a state verification assistant" in stage1_prompt
            assert "Respond ONLY with a JSON array of the string IDs" in stage1_prompt
            assert "active_tasks" in stage1_prompt
            assert "which tasks from the active_tasks list are now complete" in stage1_prompt

            # Act - Test new task analysis
            zone.analyze_image_for_new_tasks(image_path)

            # Assert - Check Stage 2 prompt matches specification
            stage2_prompt = captured_prompts[1]
            assert "You are a home organization assistant" in stage2_prompt
            assert "Do not suggest tasks that are already listed as active" in stage2_prompt
            assert "Adhere to all ignore rules" in stage2_prompt
            assert "Respond ONLY with a JSON array of new task descriptions" in stage2_prompt
            assert "context" in stage2_prompt
            assert "active_tasks" in stage2_prompt
            assert "ignore_rules" in stage2_prompt
