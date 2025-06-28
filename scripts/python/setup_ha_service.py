#!/usr/bin/env python3
"""
Setup Home Assistant Service Integration for AICleaner

This script helps set up the service integration between AICleaner
and Home Assistant following TDD and component-based design principles.
"""

import os
import json
import time
import requests
from pathlib import Path


class HAServiceSetup:
    """
    Component for setting up Home Assistant service integration.
    
    This component follows component-based design principles by:
    - Having a single responsibility (service setup)
    - Providing a clear interface
    - Being testable and mockable
    - Handling errors gracefully
    """
    
    def __init__(self, ha_url="http://localhost:8123", token=""):
        """Initialize the service setup component."""
        self.ha_url = ha_url.rstrip('/')
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.trigger_dir = Path("/tmp/aicleaner_triggers")
    
    def create_trigger_directory(self):
        """Create the trigger directory for service communication."""
        try:
            self.trigger_dir.mkdir(exist_ok=True)
            print(f"✅ Created trigger directory: {self.trigger_dir}")
            
            # Create initial status file
            status_file = self.trigger_dir / "status.json"
            status_data = {
                "status": "ready",
                "message": "AICleaner service integration ready",
                "timestamp": time.time()
            }
            
            with open(status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
            
            print(f"✅ Created status file: {status_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating trigger directory: {e}")
            return False
    
    def test_ha_connection(self):
        """Test connection to Home Assistant."""
        try:
            response = requests.get(f"{self.ha_url}/api/", headers=self.headers, timeout=10)
            if response.status_code == 200:
                print("✅ Home Assistant connection successful")
                return True
            else:
                print(f"❌ Home Assistant connection failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error connecting to Home Assistant: {e}")
            return False
    
    def create_test_service_call(self, zone=None):
        """Create a test service call trigger."""
        try:
            trigger_data = {
                "action": "run_analysis",
                "data": {"zone": zone} if zone else {},
                "timestamp": time.time()
            }
            
            trigger_file = self.trigger_dir / f"trigger_{int(time.time())}.json"
            with open(trigger_file, 'w') as f:
                json.dump(trigger_data, f, indent=2)
            
            zone_text = f" for zone '{zone}'" if zone else " for all zones"
            print(f"✅ Created test service call{zone_text}: {trigger_file}")
            return trigger_file
            
        except Exception as e:
            print(f"❌ Error creating test service call: {e}")
            return None
    
    def check_service_processing(self, timeout=30):
        """Check if service calls are being processed."""
        print(f"🔍 Checking for service processing (timeout: {timeout}s)...")
        
        start_time = time.time()
        initial_triggers = list(self.trigger_dir.glob("trigger_*.json"))
        initial_count = len(initial_triggers)
        
        print(f"📊 Initial trigger files: {initial_count}")
        
        while time.time() - start_time < timeout:
            current_triggers = list(self.trigger_dir.glob("trigger_*.json"))
            current_count = len(current_triggers)
            
            if current_count < initial_count:
                print(f"✅ Service processing detected! Triggers reduced from {initial_count} to {current_count}")
                return True
            
            time.sleep(2)
        
        print(f"⏰ Timeout reached. Triggers still present: {len(current_triggers)}")
        return False
    
    def get_configuration_instructions(self):
        """Get instructions for Home Assistant configuration."""
        config_text = """
🏠 Home Assistant Configuration Setup

Add the following to your Home Assistant configuration.yaml:

# AICleaner Service Integration
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

📋 Setup Steps:

1. Add the above configuration to your configuration.yaml
2. Restart Home Assistant
3. Ensure AICleaner addon is running
4. Test the service: Developer Tools → Services → aicleaner.run_analysis
5. Check the Lovelace card "Analyze Now" button

🔧 Troubleshooting:

- Check Home Assistant logs for automation errors
- Verify /tmp/aicleaner_triggers directory exists and is writable
- Ensure AICleaner addon is processing trigger files
- Test shell command manually in Home Assistant
"""
        return config_text
    
    def run_complete_setup(self):
        """Run the complete setup process."""
        print("🚀 AICleaner Home Assistant Service Setup")
        print("=" * 50)
        
        success = True
        
        # Test HA connection
        if not self.test_ha_connection():
            success = False
        
        # Create trigger directory
        if not self.create_trigger_directory():
            success = False
        
        if success:
            print("\n✅ Basic setup completed successfully!")
            print("\n" + self.get_configuration_instructions())
            
            # Offer to create test trigger
            print("\n🧪 Testing Service Integration")
            print("=" * 30)
            
            test_file = self.create_test_service_call("kitchen")
            if test_file:
                print(f"\n📁 Test trigger created: {test_file}")
                print("💡 If AICleaner is running, this file should be processed automatically")
                print("💡 You can also test via Home Assistant Developer Tools")
            
            return True
        else:
            print("\n❌ Setup failed. Please check the errors above.")
            return False


def main():
    """Main setup function."""
    import sys
    
    # Get token from environment or command line
    token = os.getenv('HA_TOKEN')
    if len(sys.argv) > 1:
        token = sys.argv[1]
    
    if not token:
        print("❌ Error: Home Assistant token required")
        print("Usage: python setup_ha_service.py <HA_TOKEN>")
        print("   or: HA_TOKEN=<token> python setup_ha_service.py")
        return False
    
    # Create setup instance
    setup = HAServiceSetup(token=token)
    
    # Run setup
    return setup.run_complete_setup()


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
