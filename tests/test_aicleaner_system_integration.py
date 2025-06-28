"""
Comprehensive AICleaner System Integration Tests
Following TDD principles with AAA (Arrange-Act-Assert) pattern
End-to-end testing of the complete system
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

# Import the main AICleaner class
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from aicleaner.aicleaner import Zone


class TestAICleanerSystemIntegration:
    """Comprehensive integration tests for the complete AICleaner system"""
    
    def setup_method(self):
        """Set up test fixtures for each test method"""
        # Complete zone configuration
        self.zone_config = {
            'name': 'kitchen',
            'camera_entity': 'camera.kitchen',
            'todo_list_entity': 'todo.kitchen_tasks',
            'update_frequency': 30,
            'purpose': 'Keep the kitchen clean and organized',
            'notifications_enabled': True,
            'notification_service': 'mobile_app_test',
            'notification_personality': 'snarky',
            'notify_on_create': True,
            'notify_on_complete': True,
            'webhook_url': 'http://test.webhook.com/notify'
        }
        
        # Zone state with existing tasks
        self.zone_state = {
            'tasks': [
                {
                    'id': 'existing_task_1',
                    'description': 'Wipe down countertops',
                    'status': 'active',
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'priority': 5
                }
            ]
        }
        
        # Mock clients
        self.mock_ha_client = Mock()
        self.mock_gemini_client = Mock()
        
        # Mock successful HA operations
        self.mock_ha_client.add_todo_item.return_value = True
        self.mock_ha_client.update_todo_item.return_value = True
        self.mock_ha_client.send_notification.return_value = True
    
    @patch('aicleaner.rule_persistence.RulePersistence.save_rules', return_value=True)
    @patch('aicleaner.rule_persistence.RulePersistence.load_rules', return_value=[])
    @patch('aicleaner.aicleaner.Image.open')
    def test_complete_ai_analysis_workflow(self, mock_image_open, mock_load_rules, mock_save_rules):
        """
        AAA Test: Complete AI analysis workflow from image to task creation
        """
        # ARRANGE
        zone = Zone(self.zone_config, self.zone_state, self.mock_ha_client, self.mock_gemini_client)
        
        # Add some ignore rules
        zone.add_ignore_rule("ignore dirty dishes")
        zone.add_ignore_rule("ignore crumbs")
        
        # Mock image processing
        mock_image = Mock()
        mock_image_open.return_value = mock_image
        
        # Mock Gemini response with new tasks
        mock_response = Mock()
        mock_response.text = json.dumps([
            "Clean dirty dishes on counter",  # Should be ignored
            "Organize pantry shelves",        # Should be added
            "Sweep up crumbs from floor",     # Should be ignored
            "Clean coffee maker"              # Should be added
        ])
        zone.gemini_client.generate_content.return_value = mock_response
        
        # Mock file existence
        with patch('os.path.exists', return_value=True):
            # ACT
            new_tasks = zone.analyze_image_for_new_tasks('/fake/image/path.jpg')

        # Process the new tasks
        zone._process_new_tasks(new_tasks)

        # ASSERT
        assert new_tasks is not None
        assert len(new_tasks) == 4  # All tasks returned from Gemini
        
        # Verify only non-ignored tasks were added
        tasks = zone.state['tasks']
        task_descriptions = [task['description'] for task in tasks]
        
        # Should have original task + 2 new tasks (2 were ignored)
        assert len(tasks) == 3
        assert 'Wipe down countertops' in task_descriptions  # Original task
        assert 'Organize pantry shelves' in task_descriptions  # New task
        assert 'Clean coffee maker' in task_descriptions  # New task
        assert 'Clean dirty dishes on counter' not in task_descriptions  # Ignored
        assert 'Sweep up crumbs from floor' not in task_descriptions  # Ignored
        
        # Verify HA todo items were added for new tasks only
        assert self.mock_ha_client.add_todo_item.call_count == 2
        
        # Verify Gemini was called with ignore rules in prompt
        gemini_call_args = zone.gemini_client.generate_content.call_args[0]
        prompt_data = gemini_call_args[0]  # This is a list: [prompt_string, image]

        # The prompt is the first element in the list
        if isinstance(prompt_data, list):
            prompt = prompt_data[0]
        else:
            prompt = prompt_data

        assert 'ignore dirty dishes' in prompt
        assert 'ignore crumbs' in prompt
    
    @patch('aicleaner.rule_persistence.RulePersistence.save_rules', return_value=True)
    @patch('aicleaner.rule_persistence.RulePersistence.load_rules', return_value=[])
    def test_task_completion_workflow(self, mock_load_rules, mock_save_rules):
        """
        AAA Test: Complete task completion workflow with notifications
        """
        # ARRANGE
        zone = Zone(self.zone_config, self.zone_state, self.mock_ha_client, self.mock_gemini_client)
        
        # Add a task to complete
        task_id = 'existing_task_1'
        
        # ACT - Manually complete the task (simulating the completion process)
        completed_task_ids = [task_id]
        zone._process_completed_tasks(completed_task_ids)

        # ASSERT
        # Verify task status was updated
        completed_task = next((task for task in zone.state['tasks'] if task['id'] == task_id), None)
        assert completed_task is not None
        assert completed_task['status'] == 'completed'
        assert 'completed_at' in completed_task
        
        # Verify HA todo item was updated
        self.mock_ha_client.update_todo_item.assert_called_once()
        
        # Verify notification was sent (mocked in the zone's notification engine)
        # The actual notification sending is tested in the notification system tests
    
    @patch('aicleaner.rule_persistence.RulePersistence.save_rules', return_value=True)
    @patch('aicleaner.rule_persistence.RulePersistence.load_rules', return_value=[])
    def test_sensor_data_generation(self, mock_load_rules, mock_save_rules):
        """
        AAA Test: Sensor data generation includes all system information
        """
        # ARRANGE
        zone = Zone(self.zone_config, self.zone_state, self.mock_ha_client, self.mock_gemini_client)
        zone.add_ignore_rule("ignore test items")
        
        # ACT
        sensor_data = zone.get_sensor_data()
        
        # ASSERT
        assert sensor_data['state'] == 1  # One active task (integer, not string)
        
        attributes = sensor_data['attributes']
        assert attributes['zone_name'] == 'kitchen'
        assert attributes['purpose'] == 'Keep the kitchen clean and organized'
        assert attributes['active_tasks'] == 1
        assert attributes['completed_tasks'] == 0
        assert 'last_analysis' in attributes
        assert 'ignore_rules' in attributes
        assert len(attributes['ignore_rules']) == 1
        assert attributes['ignore_rules'][0]['text'] == 'ignore test items'
        assert 'tasks' in attributes
        assert len(attributes['tasks']) == 1
    
    @patch('aicleaner.rule_persistence.RulePersistence.save_rules', return_value=True)
    @patch('aicleaner.rule_persistence.RulePersistence.load_rules', return_value=[])
    def test_ignore_rules_management_workflow(self, mock_load_rules, mock_save_rules):
        """
        AAA Test: Complete ignore rules management workflow
        """
        # ARRANGE
        zone = Zone(self.zone_config, self.zone_state, self.mock_ha_client, self.mock_gemini_client)
        
        # ACT & ASSERT - Add rules
        assert zone.add_ignore_rule("ignore dirty dishes") is True
        assert zone.add_ignore_rule("ignore crumbs") is True
        assert zone.add_ignore_rule("ignore spills") is True
        
        # Verify rules were added
        rules = zone.get_ignore_rules()
        assert len(rules) == 3
        rule_texts = [rule['text'] for rule in rules]
        assert 'ignore dirty dishes' in rule_texts
        assert 'ignore crumbs' in rule_texts
        assert 'ignore spills' in rule_texts
        
        # ACT & ASSERT - Test rule matching
        assert zone.should_ignore_task("Clean dirty dishes") is True
        assert zone.should_ignore_task("Sweep up crumbs") is True
        assert zone.should_ignore_task("Wipe up spills") is True
        assert zone.should_ignore_task("Organize pantry") is False
        
        # ACT & ASSERT - Remove a rule
        rule_to_remove = rules[0]['id']
        assert zone.remove_ignore_rule(rule_to_remove) is True
        
        # Verify rule was removed
        updated_rules = zone.get_ignore_rules()
        assert len(updated_rules) == 2
        
        # ACT & ASSERT - Try to add duplicate rule
        assert zone.add_ignore_rule("ignore crumbs") is False  # Should fail - duplicate
    
    @patch('aicleaner.rule_persistence.RulePersistence.save_rules', return_value=True)
    @patch('aicleaner.rule_persistence.RulePersistence.load_rules', return_value=[])
    def test_notification_system_integration(self, mock_load_rules, mock_save_rules):
        """
        AAA Test: Notification system integration with zone operations
        """
        # ARRANGE
        zone = Zone(self.zone_config, self.zone_state, self.mock_ha_client, self.mock_gemini_client)
        
        # Mock the notification engine methods
        zone.notification_engine.send_task_notification = Mock(return_value=True)
        zone.notification_engine.send_analysis_complete_notification = Mock(return_value=True)
        
        # ACT - Add a new task (should trigger notification)
        new_task = {
            'id': 'new_task_1',
            'description': 'Clean microwave',
            'status': 'active',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'priority': 3
        }
        
        zone.state['tasks'].append(new_task)
        zone.send_notification('task_created', {
            'task_description': new_task['description'],
            'priority': 'normal'
        })
        
        # ACT - Complete a task (should trigger notification)
        zone.send_notification('task_completed', {
            'task_description': new_task['description'],
            'completion_method': 'manual'
        })
        
        # ASSERT
        # Verify notifications were sent
        assert zone.notification_engine.send_task_notification.call_count == 2
        
        # Verify notification data
        task_calls = zone.notification_engine.send_task_notification.call_args_list
        assert task_calls[0][0][0]['description'] == 'Clean microwave'
        assert task_calls[1][0][0]['description'] == 'Clean microwave'
    
    @patch('aicleaner.rule_persistence.RulePersistence.save_rules', return_value=True)
    @patch('aicleaner.rule_persistence.RulePersistence.load_rules', return_value=[])
    def test_error_handling_and_resilience(self, mock_load_rules, mock_save_rules):
        """
        AAA Test: System handles errors gracefully and maintains functionality
        """
        # ARRANGE
        zone = Zone(self.zone_config, self.zone_state, self.mock_ha_client, self.mock_gemini_client)
        
        # ACT & ASSERT - Test with HA client failures
        self.mock_ha_client.add_todo_item.return_value = False
        
        # Should still work even if HA operations fail
        new_tasks = ["Clean oven", "Organize spice rack"]
        zone._process_new_tasks(new_tasks)
        
        # Tasks should still be added to state even if HA fails
        task_descriptions = [task['description'] for task in zone.state['tasks']]
        assert 'Clean oven' in task_descriptions
        assert 'Organize spice rack' in task_descriptions
        
        # ACT & ASSERT - Test with notification failures
        zone.notification_engine.send_task_notification = Mock(return_value=False)
        
        # Should not crash when notifications fail
        zone.send_notification('task_created', {'task_description': 'Test task'})
        
        # ACT & ASSERT - Test with invalid ignore rules
        assert zone.add_ignore_rule("") is False  # Empty rule
        assert zone.add_ignore_rule("   ") is False  # Whitespace only
        
        # System should remain functional
        assert zone.add_ignore_rule("ignore valid rule") is True
    
    @patch('aicleaner.rule_persistence.RulePersistence.save_rules', return_value=True)
    @patch('aicleaner.rule_persistence.RulePersistence.load_rules', return_value=[])
    def test_system_state_consistency(self, mock_load_rules, mock_save_rules):
        """
        AAA Test: System maintains consistent state across operations
        """
        # ARRANGE
        zone = Zone(self.zone_config, self.zone_state, self.mock_ha_client, self.mock_gemini_client)
        initial_task_count = len(zone.state['tasks'])
        
        # ACT - Perform multiple operations
        zone.add_ignore_rule("ignore test items")
        
        new_tasks = [
            "Clean test items",  # Should be ignored
            "Organize cabinet",  # Should be added
            "Put away test items", # Should be ignored (contains "test items")
            "Wipe surfaces"      # Should be added
        ]
        
        zone._process_new_tasks(new_tasks)
        
        # Complete one of the original tasks
        original_task_id = zone.state['tasks'][0]['id']
        zone._process_completed_tasks([original_task_id])
        
        # ASSERT - Verify state consistency
        final_tasks = zone.state['tasks']
        
        # Should have: 1 original task (completed) + 2 new tasks (2 were ignored)
        assert len(final_tasks) == initial_task_count + 2
        
        # Verify task statuses
        active_tasks = [task for task in final_tasks if task['status'] == 'active']
        completed_tasks = [task for task in final_tasks if task['status'] == 'completed']
        
        assert len(active_tasks) == 2  # 2 new tasks
        assert len(completed_tasks) == 1  # 1 completed original task
        
        # Verify ignore rules are still active
        assert len(zone.get_ignore_rules()) == 1
        assert zone.should_ignore_task("Clean test items") is True
        
        # Verify sensor data reflects current state
        sensor_data = zone.get_sensor_data()
        assert sensor_data['state'] == 2  # 2 active tasks (integer, not string)
        assert sensor_data['attributes']['active_tasks'] == 2
        assert sensor_data['attributes']['completed_tasks'] == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
