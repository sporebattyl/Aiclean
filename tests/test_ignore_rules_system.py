"""
Test suite for AICleaner Ignore Rules System
Following TDD principles with AAA (Arrange-Act-Assert) pattern
Component-based design testing
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import the components we'll create
from aicleaner.ignore_rules_manager import IgnoreRulesManager
from aicleaner.rule_validator import RuleValidator
from aicleaner.rule_matcher import RuleMatcher
from aicleaner.rule_persistence import RulePersistence


class TestIgnoreRulesManager:
    """Test the main IgnoreRulesManager component following AAA pattern"""
    
    def test_ignore_rules_manager_initialization(self):
        """
        AAA Test: IgnoreRulesManager should initialize with empty rules
        """
        # ARRANGE
        zone_name = 'kitchen'
        
        # ACT
        manager = IgnoreRulesManager(zone_name)
        
        # ASSERT
        assert manager.zone_name == zone_name
        assert manager.rules == []
        assert manager.validator is not None
        assert manager.matcher is not None
        assert manager.persistence is not None
    
    def test_add_ignore_rule_success(self):
        """
        AAA Test: IgnoreRulesManager should add valid ignore rules
        """
        # ARRANGE
        manager = IgnoreRulesManager('kitchen')
        rule_text = "ignore dirty dishes"
        
        # Mock the validator to return success
        manager.validator.validate_rule = Mock(return_value={'valid': True, 'normalized': rule_text})
        manager.persistence.save_rules = Mock(return_value=True)
        
        # ACT
        result = manager.add_rule(rule_text)
        
        # ASSERT
        assert result is True
        assert len(manager.rules) == 1
        assert manager.rules[0]['text'] == rule_text
        assert 'created_at' in manager.rules[0]
        manager.validator.validate_rule.assert_called_once_with(rule_text, manager.rules)
        manager.persistence.save_rules.assert_called_once()
    
    def test_add_ignore_rule_invalid(self):
        """
        AAA Test: IgnoreRulesManager should reject invalid ignore rules
        """
        # ARRANGE
        manager = IgnoreRulesManager('kitchen')
        invalid_rule = ""
        
        # Mock the validator to return failure
        manager.validator.validate_rule = Mock(return_value={'valid': False, 'error': 'Empty rule'})
        
        # ACT
        result = manager.add_rule(invalid_rule)
        
        # ASSERT
        assert result is False
        assert len(manager.rules) == 0
        manager.validator.validate_rule.assert_called_once_with(invalid_rule, manager.rules)
    
    def test_remove_ignore_rule_success(self):
        """
        AAA Test: IgnoreRulesManager should remove existing rules
        """
        # ARRANGE
        manager = IgnoreRulesManager('kitchen')
        rule_id = "rule_123"
        manager.rules = [
            {'id': rule_id, 'text': 'ignore dirty dishes', 'created_at': datetime.now().isoformat()},
            {'id': 'rule_456', 'text': 'ignore crumbs', 'created_at': datetime.now().isoformat()}
        ]
        manager.persistence.save_rules = Mock(return_value=True)
        
        # ACT
        result = manager.remove_rule(rule_id)
        
        # ASSERT
        assert result is True
        assert len(manager.rules) == 1
        assert manager.rules[0]['id'] == 'rule_456'
        manager.persistence.save_rules.assert_called_once()
    
    def test_remove_ignore_rule_not_found(self):
        """
        AAA Test: IgnoreRulesManager should handle non-existent rule removal
        """
        # ARRANGE
        manager = IgnoreRulesManager('kitchen')
        manager.rules = [
            {'id': 'rule_456', 'text': 'ignore crumbs', 'created_at': datetime.now().isoformat()}
        ]
        
        # ACT
        result = manager.remove_rule('nonexistent_rule')
        
        # ASSERT
        assert result is False
        assert len(manager.rules) == 1
    
    def test_should_ignore_task_matches(self):
        """
        AAA Test: IgnoreRulesManager should identify tasks that match ignore rules
        """
        # ARRANGE
        manager = IgnoreRulesManager('kitchen')
        task_description = "Clean dirty dishes on counter"
        manager.rules = [
            {'id': 'rule_123', 'text': 'ignore dirty dishes', 'created_at': datetime.now().isoformat()}
        ]
        
        # Mock the matcher to return a match
        manager.matcher.matches_any_rule = Mock(return_value=True)
        
        # ACT
        result = manager.should_ignore_task(task_description)
        
        # ASSERT
        assert result is True
        manager.matcher.matches_any_rule.assert_called_once_with(task_description, manager.rules)
    
    def test_should_ignore_task_no_match(self):
        """
        AAA Test: IgnoreRulesManager should allow tasks that don't match ignore rules
        """
        # ARRANGE
        manager = IgnoreRulesManager('kitchen')
        task_description = "Wipe down countertops"
        manager.rules = [
            {'id': 'rule_123', 'text': 'ignore dirty dishes', 'created_at': datetime.now().isoformat()}
        ]
        
        # Mock the matcher to return no match
        manager.matcher.matches_any_rule = Mock(return_value=False)
        
        # ACT
        result = manager.should_ignore_task(task_description)
        
        # ASSERT
        assert result is False
        manager.matcher.matches_any_rule.assert_called_once_with(task_description, manager.rules)
    
    def test_load_rules_from_persistence(self):
        """
        AAA Test: IgnoreRulesManager should load rules from persistence
        """
        # ARRANGE
        manager = IgnoreRulesManager('kitchen')
        saved_rules = [
            {'id': 'rule_123', 'text': 'ignore dirty dishes', 'created_at': datetime.now().isoformat()}
        ]
        
        # Mock the persistence to return saved rules
        manager.persistence.load_rules = Mock(return_value=saved_rules)
        
        # ACT
        result = manager.load_rules()
        
        # ASSERT
        assert result is True
        assert manager.rules == saved_rules
        manager.persistence.load_rules.assert_called_once()


class TestRuleValidator:
    """Test the RuleValidator component following AAA pattern"""
    
    def test_validate_rule_valid_text(self):
        """
        AAA Test: RuleValidator should accept valid rule text
        """
        # ARRANGE
        validator = RuleValidator()
        rule_text = "ignore dirty dishes"
        
        # ACT
        result = validator.validate_rule(rule_text)
        
        # ASSERT
        assert result['valid'] is True
        assert result['normalized'] == rule_text.lower().strip()
        assert 'error' not in result
    
    def test_validate_rule_empty_text(self):
        """
        AAA Test: RuleValidator should reject empty rule text
        """
        # ARRANGE
        validator = RuleValidator()
        rule_text = ""
        
        # ACT
        result = validator.validate_rule(rule_text)
        
        # ASSERT
        assert result['valid'] is False
        assert 'error' in result
        assert 'empty' in result['error'].lower()
    
    def test_validate_rule_whitespace_only(self):
        """
        AAA Test: RuleValidator should reject whitespace-only rules
        """
        # ARRANGE
        validator = RuleValidator()
        rule_text = "   \t\n   "
        
        # ACT
        result = validator.validate_rule(rule_text)
        
        # ASSERT
        assert result['valid'] is False
        assert 'error' in result
    
    def test_validate_rule_too_long(self):
        """
        AAA Test: RuleValidator should reject overly long rules
        """
        # ARRANGE
        validator = RuleValidator()
        rule_text = "ignore " + "very " * 100 + "long rule"
        
        # ACT
        result = validator.validate_rule(rule_text)
        
        # ASSERT
        assert result['valid'] is False
        assert 'error' in result
        assert 'exceed' in result['error'].lower() or 'too long' in result['error'].lower()
    
    def test_validate_rule_normalizes_text(self):
        """
        AAA Test: RuleValidator should normalize rule text
        """
        # ARRANGE
        validator = RuleValidator()
        rule_text = "  IGNORE Dirty DISHES  "
        
        # ACT
        result = validator.validate_rule(rule_text)
        
        # ASSERT
        assert result['valid'] is True
        assert result['normalized'] == "ignore dirty dishes"
    
    def test_validate_rule_removes_duplicates(self):
        """
        AAA Test: RuleValidator should detect duplicate rules
        """
        # ARRANGE
        validator = RuleValidator()
        existing_rules = [
            {'text': 'ignore dirty dishes', 'id': 'rule_123'}
        ]
        rule_text = "IGNORE DIRTY DISHES"
        
        # ACT
        result = validator.validate_rule(rule_text, existing_rules)
        
        # ASSERT
        assert result['valid'] is False
        assert 'duplicate' in result['error'].lower()


class TestRuleMatcher:
    """Test the RuleMatcher component following AAA pattern"""
    
    def test_matches_any_rule_exact_match(self):
        """
        AAA Test: RuleMatcher should match exact rule text
        """
        # ARRANGE
        matcher = RuleMatcher()
        task_description = "Clean dirty dishes"
        rules = [
            {'text': 'dirty dishes', 'id': 'rule_123'}
        ]
        
        # ACT
        result = matcher.matches_any_rule(task_description, rules)
        
        # ASSERT
        assert result is True
    
    def test_matches_any_rule_partial_match(self):
        """
        AAA Test: RuleMatcher should match partial rule text
        """
        # ARRANGE
        matcher = RuleMatcher()
        task_description = "Organize dirty dishes on the counter"
        rules = [
            {'text': 'dirty dishes', 'id': 'rule_123'}
        ]
        
        # ACT
        result = matcher.matches_any_rule(task_description, rules)
        
        # ASSERT
        assert result is True
    
    def test_matches_any_rule_case_insensitive(self):
        """
        AAA Test: RuleMatcher should be case insensitive
        """
        # ARRANGE
        matcher = RuleMatcher()
        task_description = "Clean DIRTY DISHES"
        rules = [
            {'text': 'dirty dishes', 'id': 'rule_123'}
        ]
        
        # ACT
        result = matcher.matches_any_rule(task_description, rules)
        
        # ASSERT
        assert result is True
    
    def test_matches_any_rule_no_match(self):
        """
        AAA Test: RuleMatcher should return False when no rules match
        """
        # ARRANGE
        matcher = RuleMatcher()
        task_description = "Wipe down countertops"
        rules = [
            {'text': 'dirty dishes', 'id': 'rule_123'}
        ]
        
        # ACT
        result = matcher.matches_any_rule(task_description, rules)
        
        # ASSERT
        assert result is False
    
    def test_matches_any_rule_multiple_rules(self):
        """
        AAA Test: RuleMatcher should check against multiple rules
        """
        # ARRANGE
        matcher = RuleMatcher()
        task_description = "Clean up crumbs on floor"
        rules = [
            {'text': 'dirty dishes', 'id': 'rule_123'},
            {'text': 'crumbs', 'id': 'rule_456'},
            {'text': 'spills', 'id': 'rule_789'}
        ]
        
        # ACT
        result = matcher.matches_any_rule(task_description, rules)
        
        # ASSERT
        assert result is True
    
    def test_matches_any_rule_empty_rules(self):
        """
        AAA Test: RuleMatcher should handle empty rules list
        """
        # ARRANGE
        matcher = RuleMatcher()
        task_description = "Clean dirty dishes"
        rules = []
        
        # ACT
        result = matcher.matches_any_rule(task_description, rules)
        
        # ASSERT
        assert result is False


class TestRulePersistence:
    """Test the RulePersistence component following AAA pattern"""
    
    @patch('pathlib.Path.rename')
    @patch('pathlib.Path.exists')
    @patch('builtins.open')
    @patch('json.dump')
    def test_save_rules_success(self, mock_json_dump, mock_open, mock_exists, mock_rename):
        """
        AAA Test: RulePersistence should save rules to file
        """
        # ARRANGE
        persistence = RulePersistence('kitchen')
        rules = [
            {'id': 'rule_123', 'text': 'ignore dirty dishes', 'created_at': datetime.now().isoformat()}
        ]
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        mock_exists.return_value = False  # No existing file
        mock_rename.return_value = None  # Successful rename

        # ACT
        result = persistence.save_rules(rules)

        # ASSERT
        assert result is True
        mock_open.assert_called_once()
        mock_json_dump.assert_called_once_with(rules, mock_file, indent=2, ensure_ascii=False)
    
    @patch('builtins.open')
    def test_save_rules_failure(self, mock_open):
        """
        AAA Test: RulePersistence should handle save failures gracefully
        """
        # ARRANGE
        persistence = RulePersistence('kitchen')
        rules = [{'id': 'rule_123', 'text': 'ignore dirty dishes'}]
        mock_open.side_effect = IOError("Permission denied")
        
        # ACT
        result = persistence.save_rules(rules)
        
        # ASSERT
        assert result is False
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open')
    @patch('json.load')
    def test_load_rules_success(self, mock_json_load, mock_open, mock_exists):
        """
        AAA Test: RulePersistence should load rules from file
        """
        # ARRANGE
        persistence = RulePersistence('kitchen')
        saved_rules = [
            {'id': 'rule_123', 'text': 'ignore dirty dishes', 'created_at': datetime.now().isoformat()}
        ]
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        mock_json_load.return_value = saved_rules
        mock_exists.return_value = True  # File exists

        # ACT
        result = persistence.load_rules()

        # ASSERT
        assert result == saved_rules
        mock_open.assert_called_once()
        mock_json_load.assert_called_once_with(mock_file)
    
    @patch('builtins.open')
    def test_load_rules_file_not_found(self, mock_open):
        """
        AAA Test: RulePersistence should handle missing files gracefully
        """
        # ARRANGE
        persistence = RulePersistence('kitchen')
        mock_open.side_effect = FileNotFoundError("File not found")
        
        # ACT
        result = persistence.load_rules()
        
        # ASSERT
        assert result == []
    
    @patch('builtins.open')
    @patch('json.load')
    def test_load_rules_invalid_json(self, mock_json_load, mock_open):
        """
        AAA Test: RulePersistence should handle corrupted JSON gracefully
        """
        # ARRANGE
        persistence = RulePersistence('kitchen')
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        mock_json_load.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        
        # ACT
        result = persistence.load_rules()
        
        # ASSERT
        assert result == []


# Integration Tests
class TestIgnoreRulesSystemIntegration:
    """Integration tests for the complete ignore rules system"""
    
    def test_end_to_end_ignore_rules_workflow(self):
        """
        AAA Test: Complete end-to-end ignore rules workflow
        """
        # ARRANGE
        manager = IgnoreRulesManager('kitchen')
        
        # Mock all dependencies
        manager.validator.validate_rule = Mock(return_value={'valid': True, 'normalized': 'ignore dirty dishes'})
        manager.persistence.save_rules = Mock(return_value=True)
        manager.persistence.load_rules = Mock(return_value=[])
        manager.matcher.matches_any_rule = Mock(return_value=True)
        
        # ACT & ASSERT - Add rule
        add_result = manager.add_rule("ignore dirty dishes")
        assert add_result is True
        assert len(manager.rules) == 1
        
        # ACT & ASSERT - Check if task should be ignored
        ignore_result = manager.should_ignore_task("Clean dirty dishes on counter")
        assert ignore_result is True
        
        # ACT & ASSERT - Remove rule
        rule_id = manager.rules[0]['id']
        remove_result = manager.remove_rule(rule_id)
        assert remove_result is True
        assert len(manager.rules) == 0
    
    def test_integration_with_zone_analysis(self):
        """
        AAA Test: Integration with zone analysis workflow
        """
        # ARRANGE
        manager = IgnoreRulesManager('kitchen')
        manager.rules = [
            {'id': 'rule_123', 'text': 'ignore dirty dishes', 'created_at': datetime.now().isoformat()}
        ]
        
        # Mock the matcher
        manager.matcher.matches_any_rule = Mock(side_effect=lambda desc, rules: 'dirty dishes' in desc.lower())
        
        discovered_tasks = [
            "Clean dirty dishes on counter",
            "Wipe down countertops", 
            "Organize dirty dishes in sink",
            "Sweep floor"
        ]
        
        # ACT
        filtered_tasks = [task for task in discovered_tasks if not manager.should_ignore_task(task)]
        
        # ASSERT
        assert len(filtered_tasks) == 2
        assert "Wipe down countertops" in filtered_tasks
        assert "Sweep floor" in filtered_tasks
        assert "Clean dirty dishes on counter" not in filtered_tasks
        assert "Organize dirty dishes in sink" not in filtered_tasks


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
