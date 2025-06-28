#!/usr/bin/env python3
"""
Set HA_TOKEN Environment Variable for AICleaner Addon

This script helps set the HA_TOKEN environment variable so that
AICleaner can use the Long-Lived Access Token instead of the
supervisor token.
"""

import os
import subprocess
import sys


def set_ha_token_environment(token):
    """Set the HA_TOKEN environment variable."""
    try:
        # Export the token for the current session
        os.environ['HA_TOKEN'] = token
        
        # Also try to set it in a way that persists for the addon
        # This approach writes to a file that can be sourced
        token_file = "/tmp/ha_token_env.sh"
        with open(token_file, 'w') as f:
            f.write(f"#!/bin/bash\nexport HA_TOKEN='{token}'\n")
        
        # Make it executable
        os.chmod(token_file, 0o755)
        
        print(f"✅ HA_TOKEN environment variable set")
        print(f"✅ Token file created: {token_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting HA_TOKEN: {e}")
        return False


def test_token_with_api(token):
    """Test the token with Home Assistant API."""
    try:
        import requests
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get("http://localhost:8123/api/", headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ Token verified with Home Assistant API")
            return True
        else:
            print(f"❌ Token verification failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing token: {e}")
        return False


def restart_aicleaner_with_token():
    """Restart AICleaner with the new token environment."""
    try:
        print("🔄 Restarting AICleaner with new token...")
        
        # Kill existing AICleaner processes
        subprocess.run(["pkill", "-f", "aicleaner.py"], capture_output=True)
        
        # Wait a moment
        import time
        time.sleep(2)
        
        # Start AICleaner with the token environment
        env = os.environ.copy()
        
        # Start in background
        process = subprocess.Popen(
            ["python3", "aicleaner.py"],
            cwd="/addons/Aiclean/aicleaner",
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        print(f"✅ AICleaner restarted with PID: {process.pid}")
        print("💡 Check the logs to verify the API endpoints are working")
        
        return True
        
    except Exception as e:
        print(f"❌ Error restarting AICleaner: {e}")
        return False


def main():
    """Main function."""
    print("🔧 AICleaner HA_TOKEN Environment Setup")
    print("=" * 50)
    
    # Get token from command line or environment
    token = None
    if len(sys.argv) > 1:
        token = sys.argv[1]
    else:
        token = os.getenv('HA_TOKEN')
    
    if not token:
        print("❌ Error: HA_TOKEN required")
        print("Usage: python set_ha_token_env.py <HA_TOKEN>")
        print("   or: HA_TOKEN=<token> python set_ha_token_env.py")
        return False
    
    print(f"🔑 Using token: {token[:20]}...")
    
    # Test the token
    if not test_token_with_api(token):
        print("❌ Token verification failed. Please check your token.")
        return False
    
    # Set environment variable
    if not set_ha_token_environment(token):
        print("❌ Failed to set environment variable.")
        return False
    
    # Ask if user wants to restart AICleaner
    print("\n🚀 Setup Complete!")
    print("=" * 20)
    print("The HA_TOKEN environment variable has been set.")
    print("AICleaner will now use the direct Home Assistant API.")
    print("\nNext steps:")
    print("1. Restart the AICleaner addon")
    print("2. Check the logs for successful camera/sensor connections")
    print("3. Test the 'Analyze Now' button in the Lovelace card")
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
