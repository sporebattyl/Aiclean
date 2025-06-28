"""
Integration tests for Zone class with Ignore Rules System
Following TDD principles with AAA (Arrange-Act-Assert) pattern
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

# Import the Zone class
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from aicleaner.aicleaner import Zone


class TestZoneIgnoreRulesIntegration:
    """Integration tests for Zone class with ignore rules functionality"""
    
    def setup_method(self):
        """Set up test fixtures for each test method"""
        # Mock configuration for zone
        self.zone_config = {
            'name': 'kitchen',
            'camera_entity': 'camera.kitchen',
            'todo_list_entity': 'todo.kitchen_tasks',
            'update_frequency': 30,
            'purpose': 'Keep the kitchen clean and organized',
            'notifications_enabled': True,
            'notification_service': 'mobile_app_test',
            'notification_personality': 'default',
            'notify_on_create': True,
            'notify_on_complete': True
        }

        # Mock state
        self.zone_state = {
            'tasks': []
        }

        # Mock clients
        self.mock_ha_client = Mock()
        self.mock_gemini_client = Mock()

        # Clear any existing rules files for clean test isolation
        import tempfile
        import shutil
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up after each test method"""
        # Clean up temporary directory
        import shutil
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('aicleaner.rule_persistence.RulePersistence.save_rules', return_value=True)
    @patch('aicleaner.rule_persistence.RulePersistence.load_rules', return_value=[])
    def test_zone_initialization_with_ignore_rules(self, mock_load_rules, mock_save_rules):
        """
        AAA Test: Zone should initialize with ignore rules manager
        """
        # ARRANGE & ACT
        zone = Zone(self.zone_config, self.zone_state, self.mock_ha_client, self.mock_gemini_client)

        # ASSERT
        assert hasattr(zone, 'ignore_rules_manager')
        assert zone.ignore_rules_manager is not None
        assert zone.ignore_rules_manager.zone_name == 'kitchen'
    
    @patch('aicleaner.rule_persistence.RulePersistence.save_rules', return_value=True)
    @patch('aicleaner.rule_persistence.RulePersistence.load_rules', return_value=[])
    def test_add_ignore_rule_to_zone(self, mock_load_rules, mock_save_rules):
        """
        AAA Test: Zone should be able to add ignore rules
        """
        # ARRANGE
        zone = Zone(self.zone_config, self.zone_state, self.mock_ha_client, self.mock_gemini_client)
        rule_text = "ignore dirty dishes"
        
        # ACT
        result = zone.add_ignore_rule(rule_text)
        
        # ASSERT
        assert result is True
        rules = zone.get_ignore_rules()
        assert len(rules) == 1
        assert rules[0]['text'] == 'ignore dirty dishes'
    
    @patch('aicleaner.rule_persistence.RulePersistence.save_rules', return_value=True)
    @patch('aicleaner.rule_persistence.RulePersistence.load_rules', return_value=[])
    def test_remove_ignore_rule_from_zone(self, mock_load_rules, mock_save_rules):
        """
        AAA Test: Zone should be able to remove ignore rules
        """
        # ARRANGE
        zone = Zone(self.zone_config, self.zone_state, self.mock_ha_client, self.mock_gemini_client)
        zone.add_ignore_rule("ignore dirty dishes")
        rules = zone.get_ignore_rules()
        rule_id = rules[0]['id']
        
        # ACT
        result = zone.remove_ignore_rule(rule_id)
        
        # ASSERT
        assert result is True
        assert len(zone.get_ignore_rules()) == 0
    
    def test_should_ignore_task_in_zone(self):
        """
        AAA Test: Zone should check if tasks should be ignored
        """
        # ARRANGE
        zone = Zone(self.zone_config, self.zone_state, self.mock_ha_client, self.mock_gemini_client)
        zone.add_ignore_rule("ignore dirty dishes")
        
        # ACT & ASSERT
        assert zone.should_ignore_task("Clean dirty dishes on counter") is True
        assert zone.should_ignore_task("Wipe down countertops") is False
    
    @patch('aicleaner.aicleaner.Zone.validate_task_schema')
    def test_process_enhanced_new_tasks_with_ignore_rules(self, mock_validate):
        """
        AAA Test: Zone should filter out ignored tasks when processing new tasks
        """
        # ARRANGE
        zone = Zone(self.zone_config, self.zone_state, self.mock_ha_client, self.mock_gemini_client)
        zone.add_ignore_rule("ignore dirty dishes")
        
        # Mock validation to always pass
        mock_validate.return_value = True
        
        # Mock HA client methods
        zone.ha_client.add_todo_item = Mock(return_value=True)
        zone.send_notification = Mock()
        
        enhanced_tasks = [
            {
                'description': 'Clean dirty dishes on counter',
                'priority': 5,
                'context_aware': True,
                'generated_at': datetime.now(timezone.utc).isoformat()
            },
            {
                'description': 'Wipe down countertops',
                'priority': 3,
                'context_aware': True,
                'generated_at': datetime.now(timezone.utc).isoformat()
            },
            {
                'description': 'Organize dirty dishes in sink',
                'priority': 4,
                'context_aware': True,
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
        ]
        
        # ACT
        zone._process_enhanced_new_tasks(enhanced_tasks)
        
        # ASSERT
        # Only one task should be added (the one that doesn't match ignore rules)
        assert len(zone.state['tasks']) == 1
        assert zone.state['tasks'][0]['description'] == 'Wipe down countertops'
        
        # Verify HA todo item was added only once
        zone.ha_client.add_todo_item.assert_called_once()
    
    @patch('aicleaner.aicleaner.Zone.validate_task_schema')
    def test_process_new_tasks_with_ignore_rules(self, mock_validate):
        """
        AAA Test: Zone should filter out ignored tasks in regular task processing
        """
        # ARRANGE
        zone = Zone(self.zone_config, self.zone_state, self.mock_ha_client, self.mock_gemini_client)
        zone.add_ignore_rule("ignore dirty dishes")
        
        # Mock validation to always pass
        mock_validate.return_value = True
        
        # Mock HA client methods
        zone.ha_client.add_todo_item = Mock()
        zone.send_notification = Mock()
        
        new_task_descriptions = [
            'Clean dirty dishes on counter',
            'Wipe down countertops',
            'Organize dirty dishes in sink'
        ]
        
        # ACT
        zone._process_new_tasks(new_task_descriptions)
        
        # ASSERT
        # Only one task should be added (the one that doesn't match ignore rules)
        assert len(zone.state['tasks']) == 1
        assert zone.state['tasks'][0]['description'] == 'Wipe down countertops'
    
    @patch('aicleaner.rule_persistence.RulePersistence.save_rules', return_value=True)
    @patch('aicleaner.rule_persistence.RulePersistence.load_rules', return_value=[])
    def test_sensor_data_includes_ignore_rules(self, mock_load_rules, mock_save_rules):
        """
        AAA Test: Zone sensor data should include ignore rules information
        """
        # ARRANGE
        zone = Zone(self.zone_config, self.zone_state, self.mock_ha_client, self.mock_gemini_client)
        zone.add_ignore_rule("ignore dirty dishes")
        zone.add_ignore_rule("ignore crumbs on floor")
        
        # ACT
        sensor_data = zone.get_sensor_data()
        
        # ASSERT
        assert 'ignore_rules' in sensor_data['attributes']
        ignore_rules = sensor_data['attributes']['ignore_rules']
        assert len(ignore_rules) == 2
        assert any(rule['text'] == 'ignore dirty dishes' for rule in ignore_rules)
        assert any(rule['text'] == 'ignore crumbs on floor' for rule in ignore_rules)
    
    @patch('aicleaner.rule_persistence.RulePersistence.save_rules', return_value=True)
    @patch('aicleaner.rule_persistence.RulePersistence.load_rules', return_value=[])
    @patch('aicleaner.aicleaner.Image.open')
    def test_ai_prompt_includes_ignore_rules(self, mock_image_open, mock_load_rules, mock_save_rules):
        """
        AAA Test: AI analysis prompt should include ignore rules
        """
        # ARRANGE
        zone = Zone(self.zone_config, self.zone_state, self.mock_ha_client, self.mock_gemini_client)
        zone.add_ignore_rule("ignore dirty dishes")
        zone.add_ignore_rule("ignore crumbs")
        
        # Mock image and Gemini response
        mock_image = Mock()
        mock_image_open.return_value = mock_image
        
        mock_response = Mock()
        mock_response.text = '["Clean countertops", "Organize pantry"]'
        zone.gemini_client.generate_content.return_value = mock_response
        
        # Mock file existence
        with patch('os.path.exists', return_value=True):
            # ACT
            zone.analyze_image_for_new_tasks('/fake/image/path.jpg')
        
        # ASSERT
        # Verify that generate_content was called
        zone.gemini_client.generate_content.assert_called_once()
        
        # Get the prompt that was sent to Gemini
        call_args = zone.gemini_client.generate_content.call_args[0]
        prompt_data = call_args[0]  # This is a list: [prompt_string, image]

        # The prompt is the first element in the list
        if isinstance(prompt_data, list):
            prompt = prompt_data[0]
        else:
            prompt = prompt_data

        # Verify ignore rules are included in the prompt
        assert 'ignore dirty dishes' in prompt
        assert 'ignore crumbs' in prompt
    
    @patch('aicleaner.rule_persistence.RulePersistence.save_rules', return_value=True)
    @patch('aicleaner.rule_persistence.RulePersistence.load_rules', return_value=[])
    def test_multiple_ignore_rules_interaction(self, mock_load_rules, mock_save_rules):
        """
        AAA Test: Multiple ignore rules should work together correctly
        """
        # ARRANGE
        zone = Zone(self.zone_config, self.zone_state, self.mock_ha_client, self.mock_gemini_client)
        zone.add_ignore_rule("ignore dirty dishes")
        zone.add_ignore_rule("ignore crumbs")
        zone.add_ignore_rule("ignore spills")
        
        test_tasks = [
            "Clean dirty dishes on counter",
            "Sweep up crumbs from floor", 
            "Wipe up spills on table",
            "Organize pantry shelves",
            "Clean dirty dishes in sink",
            "Vacuum carpet"
        ]
        
        # ACT & ASSERT
        ignored_count = 0
        allowed_count = 0
        ignored_tasks = []
        allowed_tasks = []

        for task in test_tasks:
            if zone.should_ignore_task(task):
                ignored_count += 1
                ignored_tasks.append(task)
            else:
                allowed_count += 1
                allowed_tasks.append(task)

        # Should ignore 4 tasks (2 with dirty dishes, 1 with crumbs, 1 with spills) and allow 2 tasks
        assert ignored_count == 4
        assert allowed_count == 2

        # Verify specific tasks are ignored correctly
        assert "Clean dirty dishes on counter" in ignored_tasks
        assert "Clean dirty dishes in sink" in ignored_tasks
        assert "Sweep up crumbs from floor" in ignored_tasks
        assert "Wipe up spills on table" in ignored_tasks

        # Verify specific tasks are allowed correctly
        assert "Organize pantry shelves" in allowed_tasks
        assert "Vacuum carpet" in allowed_tasks
    
    @patch('aicleaner.rule_persistence.RulePersistence.save_rules', return_value=True)
    @patch('aicleaner.rule_persistence.RulePersistence.load_rules', return_value=[])
    def test_ignore_rules_persistence_integration(self, mock_load_rules, mock_save_rules):
        """
        AAA Test: Ignore rules should persist and load correctly with zone
        """
        # ARRANGE - Create first zone with clean state
        zone1 = Zone(self.zone_config, self.zone_state, self.mock_ha_client, self.mock_gemini_client)
        zone1.add_ignore_rule("ignore dirty dishes")
        zone1.add_ignore_rule("ignore crumbs")

        # Get the rules that were added (should be exactly 2)
        saved_rules = zone1.get_ignore_rules()
        assert len(saved_rules) == 2  # Verify we have exactly 2 rules

        # ACT - Create a new zone instance (simulating restart)
        # Mock the load_rules to return the saved rules
        with patch('aicleaner.rule_persistence.RulePersistence.load_rules', return_value=saved_rules):
            zone2 = Zone(self.zone_config, self.zone_state, self.mock_ha_client, self.mock_gemini_client)

        # ASSERT - Rules should be loaded automatically
        rules = zone2.get_ignore_rules()
        assert len(rules) == 2
        rule_texts = [rule['text'] for rule in rules]
        assert 'ignore dirty dishes' in rule_texts
        assert 'ignore crumbs' in rule_texts
    
    def test_error_handling_in_ignore_rules_integration(self):
        """
        AAA Test: Zone should handle ignore rules errors gracefully
        """
        # ARRANGE
        zone = Zone(self.zone_config, self.zone_state, self.mock_ha_client, self.mock_gemini_client)
        
        # Mock the ignore rules manager to raise an exception
        zone.ignore_rules_manager.should_ignore_task = Mock(side_effect=Exception("Test error"))
        
        # ACT & ASSERT - Should not crash, should return False
        result = zone.should_ignore_task("Test task")
        assert result is False
        
        # ACT & ASSERT - Should not crash when adding rules
        result = zone.add_ignore_rule("test rule")
        # The add_ignore_rule method should handle the exception and return False
        # (depending on where the exception occurs in the chain)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
