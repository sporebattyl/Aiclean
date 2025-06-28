"""
Test suite for AICleaner Notification System
Following TDD principles with AAA (Arrange-Act-Assert) pattern
Component-based design testing
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import the components we'll create
from aicleaner.notification_engine import NotificationEngine
from aicleaner.personality_formatter import PersonalityFormatter
from aicleaner.message_template import MessageTemplate
from aicleaner.notification_sender import NotificationSender


class TestNotificationEngine:
    """Test the main NotificationEngine component following AAA pattern"""
    
    def test_notification_engine_initialization(self):
        """
        AAA Test: NotificationEngine should initialize with default personality
        """
        # ARRANGE
        config = {'notification_personality': 'default'}
        
        # ACT
        engine = NotificationEngine(config)
        
        # ASSERT
        assert engine.personality == 'default'
        assert engine.formatter is not None
        assert engine.sender is not None
    
    def test_notification_engine_with_custom_personality(self):
        """
        AAA Test: NotificationEngine should accept custom personality
        """
        # ARRANGE
        config = {'notification_personality': 'snarky'}
        
        # ACT
        engine = NotificationEngine(config)
        
        # ASSERT
        assert engine.personality == 'snarky'
    
    def test_send_task_notification_success(self):
        """
        AAA Test: NotificationEngine should send task notifications successfully
        """
        # ARRANGE
        config = {'notification_personality': 'default'}
        engine = NotificationEngine(config)
        task_data = {
            'zone': 'kitchen',
            'description': 'Clean countertops',
            'priority': 'high'
        }
        
        # Mock the sender
        engine.sender.send = Mock(return_value=True)
        
        # ACT
        result = engine.send_task_notification(task_data)
        
        # ASSERT
        assert result is True
        engine.sender.send.assert_called_once()
    
    def test_send_analysis_complete_notification(self):
        """
        AAA Test: NotificationEngine should send analysis complete notifications
        """
        # ARRANGE
        config = {'notification_personality': 'default'}
        engine = NotificationEngine(config)
        analysis_data = {
            'zone': 'living_room',
            'tasks_found': 3,
            'tasks_completed': 2
        }
        
        # Mock the sender
        engine.sender.send = Mock(return_value=True)
        
        # ACT
        result = engine.send_analysis_complete_notification(analysis_data)
        
        # ASSERT
        assert result is True
        engine.sender.send.assert_called_once()


class TestPersonalityFormatter:
    """Test the PersonalityFormatter component following AAA pattern"""
    
    def test_default_personality_formatting(self):
        """
        AAA Test: Default personality should format messages professionally
        """
        # ARRANGE
        formatter = PersonalityFormatter('default')
        task = {'description': 'Clean kitchen', 'zone': 'kitchen'}
        
        # ACT
        message = formatter.format_task_message(task)
        
        # ASSERT
        assert 'Clean kitchen' in message
        assert 'kitchen' in message
        assert len(message) > 0
    
    def test_snarky_personality_formatting(self):
        """
        AAA Test: Snarky personality should add sarcastic tone
        """
        # ARRANGE
        formatter = PersonalityFormatter('snarky')
        task = {'description': 'Clean kitchen', 'zone': 'kitchen'}
        
        # ACT
        message = formatter.format_task_message(task)
        
        # ASSERT
        assert 'Clean kitchen' in message
        # Should contain snarky elements
        snarky_indicators = ['again', 'really', 'seriously', 'obviously', 'surprise', 'oh look', 'well, well', 'here we go']
        assert any(indicator in message.lower() for indicator in snarky_indicators)
    
    def test_jarvis_personality_formatting(self):
        """
        AAA Test: Jarvis personality should be formal and helpful
        """
        # ARRANGE
        formatter = PersonalityFormatter('jarvis')
        task = {'description': 'Organize closet', 'zone': 'bedroom'}
        
        # ACT
        message = formatter.format_task_message(task)
        
        # ASSERT
        assert 'organize closet' in message.lower()
        # Should contain formal elements
        formal_indicators = ['sir', 'madam', 'recommend', 'suggest', 'advise', 'shall i assist', 'inform you']
        assert any(indicator in message.lower() for indicator in formal_indicators)
    
    def test_roaster_personality_formatting(self):
        """
        AAA Test: Roaster personality should be playfully critical
        """
        # ARRANGE
        formatter = PersonalityFormatter('roaster')
        task = {'description': 'Make bed', 'zone': 'bedroom'}
        
        # ACT
        message = formatter.format_task_message(task)
        
        # ASSERT
        assert 'Make bed' in message
        # Should contain roasting elements
        roast_indicators = ['lazy', 'messy', 'chaos', 'disaster', 'yikes', 'oh no', 'embarrassing', 'houston']
        assert any(indicator in message.lower() for indicator in roast_indicators)
    
    def test_butler_personality_formatting(self):
        """
        AAA Test: Butler personality should be polite and formal
        """
        # ARRANGE
        formatter = PersonalityFormatter('butler')
        task = {'description': 'Dust furniture', 'zone': 'living_room'}
        
        # ACT
        message = formatter.format_task_message(task)
        
        # ASSERT
        assert 'dust furniture' in message.lower()
        # Should contain butler elements
        butler_indicators = ['please', 'kindly', 'would you', 'if you will', 'at your convenience']
        assert any(indicator in message.lower() for indicator in butler_indicators)
    
    def test_coach_personality_formatting(self):
        """
        AAA Test: Coach personality should be motivational
        """
        # ARRANGE
        formatter = PersonalityFormatter('coach')
        task = {'description': 'Vacuum carpet', 'zone': 'living_room'}
        
        # ACT
        message = formatter.format_task_message(task)
        
        # ASSERT
        assert 'Vacuum carpet' in message
        # Should contain motivational elements
        coach_indicators = ['you got this', 'let\'s go', 'champion', 'crush it', 'power through', 'you\'re unstoppable', 'team']
        assert any(indicator in message.lower() for indicator in coach_indicators)
    
    def test_zen_personality_formatting(self):
        """
        AAA Test: Zen personality should be calm and mindful
        """
        # ARRANGE
        formatter = PersonalityFormatter('zen')
        task = {'description': 'Clean windows', 'zone': 'bedroom'}
        
        # ACT
        message = formatter.format_task_message(task)
        
        # ASSERT
        assert 'clean windows' in message.lower()
        # Should contain zen elements
        zen_indicators = ['mindfully', 'peaceful', 'harmony', 'balance', 'serenity']
        assert any(indicator in message.lower() for indicator in zen_indicators)
    
    def test_invalid_personality_defaults_to_default(self):
        """
        AAA Test: Invalid personality should default to 'default'
        """
        # ARRANGE
        formatter = PersonalityFormatter('invalid_personality')
        task = {'description': 'Test task', 'zone': 'test_zone'}
        
        # ACT
        message = formatter.format_task_message(task)
        
        # ASSERT
        assert len(message) > 0
        assert formatter.personality == 'default'


class TestMessageTemplate:
    """Test the MessageTemplate component following AAA pattern"""
    
    def test_task_notification_template(self):
        """
        AAA Test: Task notification template should format correctly
        """
        # ARRANGE
        template = MessageTemplate()
        data = {
            'zone': 'kitchen',
            'description': 'Clean countertops',
            'priority': 'high'
        }
        
        # ACT
        message = template.format_task_notification(data)
        
        # ASSERT
        assert 'kitchen' in message.lower()
        assert 'Clean countertops' in message
        assert 'high' in message.lower()
    
    def test_analysis_complete_template(self):
        """
        AAA Test: Analysis complete template should format correctly
        """
        # ARRANGE
        template = MessageTemplate()
        data = {
            'zone': 'living_room',
            'tasks_found': 3,
            'tasks_completed': 2,
            'completion_rate': 0.67
        }
        
        # ACT
        message = template.format_analysis_complete(data)
        
        # ASSERT
        assert 'living room' in message.lower()
        assert '3' in message
        assert '2' in message
    
    def test_system_status_template(self):
        """
        AAA Test: System status template should format correctly
        """
        # ARRANGE
        template = MessageTemplate()
        data = {
            'total_zones': 3,
            'active_tasks': 8,
            'completion_rate': 0.75
        }
        
        # ACT
        message = template.format_system_status(data)
        
        # ASSERT
        assert '3' in message
        assert '8' in message
        assert '75' in message


class TestNotificationSender:
    """Test the NotificationSender component following AAA pattern"""
    
    @patch('requests.post')
    def test_send_notification_success(self, mock_post):
        """
        AAA Test: NotificationSender should send notifications successfully
        """
        # ARRANGE
        mock_post.return_value.status_code = 200
        sender = NotificationSender({'webhook_url': 'http://test.com/webhook'})
        message = "Test notification message"
        
        # ACT
        result = sender.send(message)
        
        # ASSERT
        assert result is True
        mock_post.assert_called_once()
    
    @patch('requests.post')
    def test_send_notification_failure(self, mock_post):
        """
        AAA Test: NotificationSender should handle failures gracefully
        """
        # ARRANGE
        mock_post.return_value.status_code = 500
        sender = NotificationSender({'webhook_url': 'http://test.com/webhook'})
        message = "Test notification message"
        
        # ACT
        result = sender.send(message)
        
        # ASSERT
        assert result is False
        # Should retry 3 times (default retry_count)
        assert mock_post.call_count == 3
    
    def test_send_notification_no_config(self):
        """
        AAA Test: NotificationSender should handle missing config gracefully
        """
        # ARRANGE
        sender = NotificationSender({})
        message = "Test notification message"
        
        # ACT
        result = sender.send(message)
        
        # ASSERT
        assert result is False


# Integration Tests
class TestNotificationSystemIntegration:
    """Integration tests for the complete notification system"""
    
    @patch('requests.post')
    def test_end_to_end_task_notification(self, mock_post):
        """
        AAA Test: Complete end-to-end task notification flow
        """
        # ARRANGE
        mock_post.return_value.status_code = 200
        config = {
            'notification_personality': 'snarky',
            'webhook_url': 'http://test.com/webhook'
        }
        engine = NotificationEngine(config)
        task_data = {
            'zone': 'kitchen',
            'description': 'Clean countertops',
            'priority': 'high'
        }
        
        # ACT
        result = engine.send_task_notification(task_data)
        
        # ASSERT
        assert result is True
        mock_post.assert_called_once()
        
        # Verify the message was formatted with snarky personality
        call_args = mock_post.call_args
        message_data = call_args[1]['json']
        assert 'Clean countertops' in str(message_data)
    
    def test_personality_switching(self):
        """
        AAA Test: Notification engine should switch personalities correctly
        """
        # ARRANGE
        config = {'notification_personality': 'default'}
        engine = NotificationEngine(config)
        task_data = {'zone': 'kitchen', 'description': 'Clean', 'priority': 'high'}
        
        # ACT & ASSERT - Test default personality
        engine.formatter.personality = 'default'
        default_message = engine.formatter.format_task_message(task_data)
        
        # ACT & ASSERT - Test snarky personality
        engine.set_personality('snarky')
        snarky_message = engine.formatter.format_task_message(task_data)
        
        # ASSERT
        assert engine.personality == 'snarky'
        assert default_message != snarky_message


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
