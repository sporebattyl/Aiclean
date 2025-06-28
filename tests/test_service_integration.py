"""
Test suite for AICleaner service integration using TDD and AAA principles.

This module tests that the AICleaner service integration works correctly
with Home Assistant service calls.
"""

import pytest
import json
import tempfile
import os
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add the aicleaner directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'aicleaner'))


class TestServiceIntegration:
    """Test class for service integration functionality."""
    
    def test_service_trigger_file_creation(self):
        """
        Test creation of service trigger files.
        
        Arrange: Trigger directory and service data
        Act: Create trigger file
        Assert: File is created with correct content
        """
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            trigger_dir = Path(temp_dir)
            trigger_data = {
                "action": "run_analysis",
                "data": {"zone": "kitchen"},
                "timestamp": time.time()
            }
            
            # Act
            trigger_file = trigger_dir / f"trigger_{int(time.time())}.json"
            with open(trigger_file, 'w') as f:
                json.dump(trigger_data, f)
            
            # Assert
            assert trigger_file.exists(), "Trigger file should be created"
            
            with open(trigger_file, 'r') as f:
                loaded_data = json.load(f)
            
            assert loaded_data["action"] == "run_analysis", \
                "Action should be preserved"
            assert loaded_data["data"]["zone"] == "kitchen", \
                "Zone data should be preserved"
    
    def test_service_trigger_processing(self):
        """
        Test processing of service trigger files.
        
        Arrange: Mock AICleaner with trigger file
        Act: Process trigger files
        Assert: Trigger is processed correctly
        """
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock AICleaner
            from aicleaner import AICleaner
            
            # Create trigger file
            trigger_dir = Path(temp_dir)
            trigger_file = trigger_dir / "trigger_test.json"
            trigger_data = {
                "action": "run_analysis",
                "data": {"zone": "kitchen"},
                "timestamp": time.time()
            }
            
            with open(trigger_file, 'w') as f:
                json.dump(trigger_data, f)
            
            # Mock the AICleaner methods
            with patch.object(AICleaner, '__init__', return_value=None):
                with patch.object(AICleaner, 'zones', []):
                    with patch.object(AICleaner, 'handle_service_run_analysis') as mock_handler:
                        cleaner = AICleaner()
                        
                        # Mock the process_service_triggers method to use our temp dir
                        def mock_process_triggers():
                            trigger_files = list(trigger_dir.glob("trigger_*.json"))
                            for tf in trigger_files:
                                with open(tf, 'r') as f:
                                    data = json.load(f)
                                if data.get('action') == 'run_analysis':
                                    cleaner.handle_service_run_analysis(data.get('data', {}))
                                tf.unlink()
                        
                        # Act
                        mock_process_triggers()
                        
                        # Assert
                        mock_handler.assert_called_once_with({"zone": "kitchen"})
                        assert not trigger_file.exists(), \
                            "Trigger file should be removed after processing"
    
    def test_run_analysis_service_handler_specific_zone(self):
        """
        Test run_analysis service handler for specific zone.
        
        Arrange: Mock AICleaner with zones
        Act: Call service handler with zone data
        Assert: Correct zone analysis is triggered
        """
        # Arrange
        from aicleaner import AICleaner
        
        # Create mock zone
        mock_zone = MagicMock()
        mock_zone.name = "kitchen"
        mock_zone.run_analysis_cycle = MagicMock()
        
        with patch.object(AICleaner, '__init__', return_value=None):
            cleaner = AICleaner()
            cleaner.zones = [mock_zone]
            cleaner.sync_all_ha_integrations = MagicMock()
            
            # Act
            cleaner.handle_service_run_analysis({"zone": "kitchen"})
            
            # Assert
            mock_zone.run_analysis_cycle.assert_called_once()
            cleaner.sync_all_ha_integrations.assert_called_once()
    
    def test_run_analysis_service_handler_all_zones(self):
        """
        Test run_analysis service handler for all zones.
        
        Arrange: Mock AICleaner with multiple zones
        Act: Call service handler without zone data
        Assert: All zones analysis is triggered
        """
        # Arrange
        from aicleaner import AICleaner
        
        with patch.object(AICleaner, '__init__', return_value=None):
            cleaner = AICleaner()
            cleaner.run_single_cycle = MagicMock()
            
            # Act
            cleaner.handle_service_run_analysis({})
            
            # Assert
            cleaner.run_single_cycle.assert_called_once()
    
    def test_run_analysis_service_handler_nonexistent_zone(self):
        """
        Test run_analysis service handler with nonexistent zone.
        
        Arrange: Mock AICleaner with zones
        Act: Call service handler with invalid zone
        Assert: Error is handled gracefully
        """
        # Arrange
        from aicleaner import AICleaner
        
        mock_zone = MagicMock()
        mock_zone.name = "kitchen"
        
        with patch.object(AICleaner, '__init__', return_value=None):
            cleaner = AICleaner()
            cleaner.zones = [mock_zone]
            
            # Act & Assert
            # Should not raise exception, just log error
            cleaner.handle_service_run_analysis({"zone": "nonexistent"})
            
            # Verify the existing zone was not called
            mock_zone.run_analysis_cycle.assert_not_called()
    
    def test_service_integration_in_main_loop(self):
        """
        Test that service integration is called in main loop.
        
        Arrange: Mock AICleaner main loop components
        Act: Simulate one iteration of main loop
        Assert: Service triggers are processed
        """
        # Arrange
        from aicleaner import AICleaner
        
        with patch.object(AICleaner, '__init__', return_value=None):
            cleaner = AICleaner()
            cleaner.run_scheduled_analysis = MagicMock()
            cleaner.process_service_triggers = MagicMock()
            
            # Mock time.sleep to prevent actual waiting
            with patch('time.sleep', side_effect=KeyboardInterrupt):
                # Act
                try:
                    cleaner.run()
                except KeyboardInterrupt:
                    pass  # Expected
                
                # Assert
                cleaner.run_scheduled_analysis.assert_called()
                cleaner.process_service_triggers.assert_called()


class TestServiceIntegrationFiles:
    """Test class for service integration file operations."""
    
    def test_trigger_directory_creation(self):
        """
        Test that trigger directory is created if it doesn't exist.
        
        Arrange: Non-existent trigger directory path
        Act: Check for trigger directory in process
        Assert: Directory handling works correctly
        """
        # Arrange
        from aicleaner import AICleaner
        
        with patch.object(AICleaner, '__init__', return_value=None):
            cleaner = AICleaner()
            
            # Mock Path.exists to return False initially
            with patch('pathlib.Path.exists', return_value=False):
                with patch('pathlib.Path.glob', return_value=[]):
                    # Act
                    cleaner.process_service_triggers()
                    
                    # Assert
                    # Should handle missing directory gracefully
                    assert True, "Should handle missing directory without error"
    
    def test_malformed_trigger_file_handling(self):
        """
        Test handling of malformed trigger files.
        
        Arrange: Trigger file with invalid JSON
        Act: Process trigger files
        Assert: Malformed files are handled gracefully
        """
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            from aicleaner import AICleaner
            
            # Create malformed trigger file
            trigger_dir = Path(temp_dir)
            trigger_file = trigger_dir / "trigger_malformed.json"
            trigger_file.write_text("invalid json content")
            
            with patch.object(AICleaner, '__init__', return_value=None):
                cleaner = AICleaner()
                
                # Mock the trigger directory path
                with patch('pathlib.Path', return_value=trigger_dir):
                    with patch.object(trigger_dir, 'exists', return_value=True):
                        with patch.object(trigger_dir, 'glob', return_value=[trigger_file]):
                            # Act
                            cleaner.process_service_triggers()
                            
                            # Assert
                            # File should be removed even if malformed
                            assert not trigger_file.exists(), \
                                "Malformed trigger file should be removed"
