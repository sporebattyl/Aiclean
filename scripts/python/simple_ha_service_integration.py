#!/usr/bin/env python3
"""
Simple Home Assistant Service Integration

This script creates a simple integration that allows the Lovelace card
to trigger AICleaner analysis through Home Assistant automations.
"""

import json
import logging
import os
import sys
import time
from pathlib import Path

# Add the aicleaner directory to the path
sys.path.insert(0, '/addons/Aiclean/aicleaner')

from aicleaner import AICleaner


class SimpleHAServiceIntegration:
    """
    Simple integration that creates trigger files for Home Assistant automations.
    
    This approach uses file-based triggers instead of complex webhook servers,
    making it more reliable and easier to implement.
    """
    
    def __init__(self, aicleaner_instance, trigger_dir="/tmp/aicleaner_triggers"):
        """
        Initialize the service integration.
        
        Args:
            aicleaner_instance: Instance of AICleaner
            trigger_dir: Directory for trigger files
        """
        self.aicleaner = aicleaner_instance
        self.trigger_dir = Path(trigger_dir)
        self.trigger_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # Create status file
        self.status_file = self.trigger_dir / "status.json"
        self.update_status("ready")
    
    def update_status(self, status: str, message: str = ""):
        """Update the status file for Home Assistant to monitor."""
        status_data = {
            "status": status,
            "message": message,
            "timestamp": time.time(),
            "zones": [zone.name for zone in self.aicleaner.zones] if self.aicleaner.zones else []
        }
        
        with open(self.status_file, 'w') as f:
            json.dump(status_data, f, indent=2)
    
    def create_trigger_file(self, action: str, data: dict = None):
        """Create a trigger file for Home Assistant to detect."""
        trigger_data = {
            "action": action,
            "data": data or {},
            "timestamp": time.time()
        }
        
        trigger_file = self.trigger_dir / f"{action}_{int(time.time())}.json"
        with open(trigger_file, 'w') as f:
            json.dump(trigger_data, f, indent=2)
        
        self.logger.info(f"Created trigger file: {trigger_file}")
        return trigger_file
    
    def process_trigger_files(self):
        """Process any trigger files that Home Assistant has created."""
        trigger_files = list(self.trigger_dir.glob("trigger_*.json"))
        
        for trigger_file in trigger_files:
            try:
                with open(trigger_file, 'r') as f:
                    trigger_data = json.load(f)
                
                action = trigger_data.get('action')
                data = trigger_data.get('data', {})
                
                self.logger.info(f"Processing trigger: {action} with data: {data}")
                
                if action == 'run_analysis':
                    self.handle_run_analysis(data)
                else:
                    self.logger.warning(f"Unknown action: {action}")
                
                # Remove processed trigger file
                trigger_file.unlink()
                
            except Exception as e:
                self.logger.error(f"Error processing trigger file {trigger_file}: {e}")
                # Remove problematic file
                trigger_file.unlink()
    
    def handle_run_analysis(self, data: dict):
        """Handle run_analysis trigger."""
        try:
            zone_name = data.get('zone')
            
            if zone_name:
                # Run analysis for specific zone
                zone = next((z for z in self.aicleaner.zones if z.name == zone_name), None)
                if zone:
                    self.update_status("running", f"Analyzing zone: {zone_name}")
                    self.logger.info(f"Running analysis for zone: {zone_name}")
                    zone.run_analysis_cycle()
                    self.aicleaner.sync_all_ha_integrations()
                    self.update_status("completed", f"Analysis completed for zone: {zone_name}")
                    
                    # Create completion trigger
                    self.create_trigger_file("analysis_completed", {
                        "zone": zone_name,
                        "success": True
                    })
                else:
                    self.update_status("error", f"Zone not found: {zone_name}")
                    self.logger.error(f"Zone not found: {zone_name}")
            else:
                # Run analysis for all zones
                self.update_status("running", "Analyzing all zones")
                self.logger.info("Running analysis for all zones")
                self.aicleaner.run_single_cycle()
                self.update_status("completed", "Analysis completed for all zones")
                
                # Create completion trigger
                self.create_trigger_file("analysis_completed", {
                    "zone": "all",
                    "success": True
                })
                
        except Exception as e:
            self.logger.error(f"Error in run_analysis: {e}")
            self.update_status("error", f"Analysis failed: {str(e)}")
            
            # Create error trigger
            self.create_trigger_file("analysis_error", {
                "error": str(e),
                "zone": data.get('zone', 'all')
            })
    
    def run_service_loop(self, check_interval: int = 5):
        """Run the service loop to check for triggers."""
        self.logger.info("Starting AICleaner service integration loop")
        
        try:
            while True:
                self.process_trigger_files()
                time.sleep(check_interval)
        except KeyboardInterrupt:
            self.logger.info("Service integration stopped by user")
        except Exception as e:
            self.logger.error(f"Error in service loop: {e}")
            self.update_status("error", f"Service loop error: {str(e)}")
            raise


def create_ha_automation_config():
    """Create Home Assistant automation configuration."""
    
    automation_config = """
# AICleaner Service Integration Automations
# Add these to your Home Assistant configuration.yaml

automation:
  - alias: "AICleaner Run Analysis Service"
    description: "Handle aicleaner.run_analysis service calls"
    trigger:
      - platform: event
        event_type: call_service
        event_data:
          domain: aicleaner
          service: run_analysis
    action:
      - service: shell_command.aicleaner_run_analysis
        data:
          zone: "{{ trigger.event.data.service_data.zone | default('') }}"

shell_command:
  aicleaner_run_analysis: >
    echo '{"action": "run_analysis", "data": {"zone": "{{ zone }}"}, "timestamp": {{ now().timestamp() }}}' > 
    /tmp/aicleaner_triggers/trigger_{{ now().timestamp() | int }}.json

# Optional: Monitor AICleaner status
sensor:
  - platform: file
    name: "AICleaner Status"
    file_path: "/tmp/aicleaner_triggers/status.json"
    value_template: "{{ value_json.status }}"
    json_attributes:
      - message
      - timestamp
      - zones
"""
    
    return automation_config


def test_integration():
    """Test the service integration."""
    print("🧪 Testing AICleaner Service Integration")
    print("=" * 50)
    
    # Create test configuration
    test_config = {
        'gemini_api_key': 'test_key',
        'display_name': 'Test User',
        'zones': [{
            'name': 'kitchen',
            'camera_entity': 'camera.test',
            'todo_list_entity': 'todo.test',
            'update_frequency': 30
        }],
        'ha_api_url': 'http://localhost:8123',
        'ha_token': 'test_token'
    }
    
    try:
        # Mock the AICleaner for testing
        class MockAICleaner:
            def __init__(self):
                self.zones = [MockZone('kitchen')]
            
            def run_single_cycle(self):
                print("Mock: Running single cycle")
            
            def sync_all_ha_integrations(self):
                print("Mock: Syncing HA integrations")
        
        class MockZone:
            def __init__(self, name):
                self.name = name
            
            def run_analysis_cycle(self):
                print(f"Mock: Running analysis for zone {self.name}")
        
        # Test the integration
        mock_aicleaner = MockAICleaner()
        integration = SimpleHAServiceIntegration(mock_aicleaner)
        
        print("✅ Integration initialized successfully")
        
        # Test trigger creation
        trigger_file = integration.create_trigger_file("run_analysis", {"zone": "kitchen"})
        print(f"✅ Trigger file created: {trigger_file}")
        
        # Test trigger processing
        integration.process_trigger_files()
        print("✅ Trigger processing completed")
        
        # Check status
        if integration.status_file.exists():
            with open(integration.status_file, 'r') as f:
                status = json.load(f)
            print(f"✅ Status: {status['status']} - {status['message']}")
        
        print("\n🎉 Service integration test completed successfully!")
        print("\nNext steps:")
        print("1. Add the automation configuration to Home Assistant")
        print("2. Restart Home Assistant")
        print("3. Test the aicleaner.run_analysis service")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def main():
    """Main function to run the service integration."""
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    print("🚀 AICleaner Simple Service Integration")
    print("=" * 50)
    
    # Check if we should just test
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        return test_integration()
    
    # Print automation config
    if len(sys.argv) > 1 and sys.argv[1] == 'config':
        print("Home Assistant Configuration:")
        print("=" * 30)
        print(create_ha_automation_config())
        return True
    
    try:
        # Initialize AICleaner
        aicleaner = AICleaner()
        
        # Create service integration
        integration = SimpleHAServiceIntegration(aicleaner)
        
        print("✅ AICleaner service integration started")
        print("📁 Trigger directory:", integration.trigger_dir)
        print("📄 Status file:", integration.status_file)
        print("\nWaiting for service calls...")
        
        # Run the service loop
        integration.run_service_loop()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
