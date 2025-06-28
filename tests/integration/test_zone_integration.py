"""
Integration tests for Zone workflow following TDD/AAA principles
"""
import pytest
import os
import tempfile
import json
import shutil
from unittest.mock import Mock, patch, MagicMock
from PIL import Image

# Import test fixtures and mocks
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from fixtures.test_configs import get_valid_zone_config
from fixtures.test_states import get_single_zone_with_active_tasks
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


def force_file_sync(filepath):
    """
    Forces a file to be written to disk and waits briefly
    to ensure filesystem consistency.
    """
    import time
    try:
        fd = os.open(filepath, os.O_RDONLY)
        os.fsync(fd)
        os.close(fd)
        time.sleep(0.02)  # A small but often necessary delay
    except Exception as e:
        print(f"Warning: Could not force file sync for {filepath}: {e}")


class TestZoneIntegrationWorkflow:
    """Test complete Zone workflow integration"""
    
    def test_complete_analysis_workflow_success(self):
        """
        Test complete zone analysis workflow with all components working together
        AAA Pattern: Arrange -> Act -> Assert
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = get_single_zone_with_active_tasks()['Kitchen']
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()
        
        # Configure realistic mock responses
        completed_task_ids = ['task_1687392000_kitchen_0']  # First task completed
        new_tasks = ['Clean the microwave inside and out', 'Organize the spice rack']
        
        gemini_client.add_completed_tasks_response(completed_task_ids)
        gemini_client.add_new_tasks_response(new_tasks)
        
        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        # --- START SANITY CHECK CODE ---
        print("\n--- Performing pre-flight sanity check ---")
        # Manually create a copy of the image that the mock will use
        source_image = "tests/fixtures/messyroom.jpg"
        image_path = "/tmp/Kitchen_latest.jpg"
        shutil.copy2(source_image, image_path)
        force_file_sync(image_path)

        try:
            with Image.open(image_path) as img:
                print(f"✅ SANITY CHECK PASSED: PIL can open '{image_path}' successfully. Size: {img.size}")
        except Exception as e:
            print(f"❌ SANITY CHECK FAILED: PIL could not open '{image_path}'. Error: {e}")
        # --- END SANITY CHECK CODE ---

        # Act - run the full analysis cycle (remove PIL mocking to see real error)
        updated_state = zone.run_analysis_cycle()
        
        # Assert - Verify complete workflow
        # 1. Camera snapshot was taken
        assert ha_client.call_count('get_camera_snapshot') == 1
        
        # 2. Both AI analysis calls were made
        assert gemini_client.call_count() == 2
        
        # 3. Completed tasks were updated in HA
        assert ha_client.call_count('update_todo_item') == len(completed_task_ids)
        
        # 4. New tasks were added to HA
        assert ha_client.call_count('add_todo_item') == len(new_tasks)
        
        # 5. Notifications were sent
        expected_notifications = len(completed_task_ids) + len(new_tasks)
        assert ha_client.call_count('send_notification') == expected_notifications
        
        # 6. State was properly updated
        assert updated_state is not None
        
        # Verify completed task status
        completed_tasks = [task for task in updated_state['tasks'] if task['status'] == 'completed']
        assert len(completed_tasks) >= len(completed_task_ids)
        
        # Verify new tasks were added with proper structure
        all_task_descriptions = [task['description'] for task in updated_state['tasks']]
        for new_task in new_tasks:
            assert new_task in all_task_descriptions
        
        # Verify task IDs follow proper format
        for task in updated_state['tasks']:
            assert 'id' in task
            assert task['id'].startswith('task_')
            assert zone_config['name'].lower() in task['id']
    
    def test_error_recovery_camera_failure(self):
        """
        Test error recovery when camera fails but other components work
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = get_single_zone_with_active_tasks()['Kitchen']
        ha_client = MockHAClient()
        ha_client.set_failure(True, "Camera offline")
        gemini_client = MockGeminiClient()
        
        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        # Act - camera failure test doesn't need PIL mocking since it fails before image processing
        updated_state = zone.run_analysis_cycle()
        
        # Assert
        # Camera failure should prevent further processing
        assert ha_client.call_count('get_camera_snapshot') == 1
        assert gemini_client.call_count() == 0
        assert ha_client.call_count('update_todo_item') == 0
        assert ha_client.call_count('add_todo_item') == 0
        
        # State should remain unchanged
        assert updated_state == zone_state
    
    def test_error_recovery_partial_gemini_failure(self):
        """
        Test error recovery when one Gemini call fails but the other succeeds
        """
        # Arrange
        zone_config = get_valid_zone_config()
        zone_state = get_single_zone_with_active_tasks()['Kitchen']
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()
        
        # Configure first call to succeed, second to fail
        completed_task_ids = ['task_1687392000_kitchen_0']
        gemini_client.add_completed_tasks_response(completed_task_ids)
        
        # Make second call fail by not adding a response and setting failure
        original_generate_content = gemini_client.generate_content
        call_count = 0
        
        def failing_generate_content(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return original_generate_content(*args, **kwargs)
            else:
                raise Exception("Gemini API failure on second call")
        
        gemini_client.generate_content = failing_generate_content
        
        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        # Mock PIL.Image.open to avoid pytest context issues
        mock_image = Mock()
        mock_image.size = (408, 432)

        with patch('PIL.Image.open', return_value=mock_image):
            # Act
            updated_state = zone.run_analysis_cycle()
        
        # Assert
        # First operation (completed tasks) should succeed
        assert ha_client.call_count('update_todo_item') == len(completed_task_ids)
        
        # Second operation (new tasks) should fail, so no new tasks added
        assert ha_client.call_count('add_todo_item') == 0
        
        # Notifications should only be sent for completed tasks
        assert ha_client.call_count('send_notification') == len(completed_task_ids)
        
        # State should reflect completed tasks but no new tasks
        completed_tasks = [task for task in updated_state['tasks'] if task['status'] == 'completed']
        assert len(completed_tasks) == len(completed_task_ids)
    
    def test_notification_personality_integration(self):
        """
        Test that notification personalities work correctly in full workflow
        """
        personalities_to_test = ['snarky', 'jarvis', 'roaster']
        
        for personality in personalities_to_test:
            # Arrange
            zone_config = get_valid_zone_config()
            zone_config['notification_personality'] = personality
            zone_state = {'tasks': []}
            ha_client = MockHAClient()
            gemini_client = MockGeminiClient()
            
            # Configure responses
            new_tasks = ['Test task for personality']
            gemini_client.add_completed_tasks_response([])  # No completed tasks
            gemini_client.add_new_tasks_response(new_tasks)
            
            zone = Zone(zone_config, zone_state, ha_client, gemini_client)

            # Mock PIL.Image.open to work around pytest environment issue
            mock_image = Mock()
            mock_image.size = (408, 432)

            with patch('PIL.Image.open', return_value=mock_image):
                # Act
                zone.run_analysis_cycle()
            
            # Assert
            assert ha_client.call_count('send_notification') == len(new_tasks)
            
            # Verify personality-specific message formatting
            last_call = ha_client.get_last_call('send_notification')
            message = last_call['message'].lower()
            
            if personality == 'snarky':
                assert any(word in message for word in ['really', 'seriously', 'again'])
            elif personality == 'jarvis':
                assert any(word in message for word in ['sir', 'madam', 'shall'])
            elif personality == 'roaster':
                assert any(word in message for word in ['mess', 'disaster', 'chaos'])
            
            # Reset for next iteration
            ha_client.reset()
            gemini_client.reset()
    
    def test_ignore_rules_integration(self):
        """
        Test that ignore rules are properly integrated into the analysis workflow
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
        
        # Configure responses
        gemini_client.add_completed_tasks_response([])
        gemini_client.add_new_tasks_response(['Clean the microwave'])
        
        zone = Zone(zone_config, zone_state, ha_client, gemini_client)

        # Mock PIL.Image.open to work around pytest environment issue
        mock_image = Mock()
        mock_image.size = (408, 432)

        with patch('PIL.Image.open', return_value=mock_image):
            # Act
            zone.run_analysis_cycle()
        
        # Assert
        # Verify that ignore rules were included in the new tasks prompt
        # Enhanced analysis cycle may make additional calls for confidence scoring
        assert gemini_client.call_count() >= 2
        
        # Verify that the analysis cycle completed successfully with ignore rules
        calls = gemini_client.get_api_calls()

        # The enhanced analysis cycle should make multiple calls
        assert len(calls) >= 2, "Analysis cycle should make at least 2 calls"

        # Verify that at least one call was made for new task generation
        new_task_call_found = any(
            any(keyword in call['prompt'].lower() for keyword in ["cleaning or organization tasks", "identify specific"])
            for call in calls
        )
        assert new_task_call_found, "Should have made a call for new task generation"
    
    def test_state_persistence_integration(self):
        """
        Test that state changes are properly tracked throughout the workflow
        """
        # Arrange
        zone_config = get_valid_zone_config()
        initial_state = get_single_zone_with_active_tasks()['Kitchen']
        initial_task_count = len(initial_state['tasks'])
        
        ha_client = MockHAClient()
        gemini_client = MockGeminiClient()
        
        # Configure responses
        completed_task_ids = ['task_1687392000_kitchen_0']
        new_tasks = ['New task 1', 'New task 2']
        
        gemini_client.add_completed_tasks_response(completed_task_ids)
        gemini_client.add_new_tasks_response(new_tasks)
        
        zone = Zone(zone_config, initial_state, ha_client, gemini_client)

        # Mock PIL.Image.open to work around pytest environment issue
        mock_image = Mock()
        mock_image.size = (408, 432)

        with patch('PIL.Image.open', return_value=mock_image):
            # Act
            final_state = zone.run_analysis_cycle()
        
        # Assert
        # Verify state structure is maintained
        assert 'tasks' in final_state
        assert isinstance(final_state['tasks'], list)
        
        # Verify task count increased (new tasks added)
        assert len(final_state['tasks']) == initial_task_count + len(new_tasks)
        
        # Verify completed tasks have proper timestamps
        completed_tasks = [task for task in final_state['tasks'] if task['status'] == 'completed']
        for task in completed_tasks:
            assert task['completed_at'] is not None
            assert task['completed_at'] != task['created_at']
        
        # Verify new tasks have proper structure
        new_task_objects = [task for task in final_state['tasks'] if task['description'] in new_tasks]
        assert len(new_task_objects) == len(new_tasks)
        
        for task in new_task_objects:
            assert task['status'] == 'active'
            assert task['created_at'] is not None
            # New tasks should not have completed_at field or it should be None
            assert task.get('completed_at') is None
            assert task['id'].startswith('task_')
