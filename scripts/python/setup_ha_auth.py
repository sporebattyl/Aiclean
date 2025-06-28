#!/usr/bin/env python3
"""
Home Assistant CLI Authentication Setup Script

This script helps set up authentication for the Home Assistant CLI
following TDD and component-based design principles.
"""

import os
import sys
import subprocess
from pathlib import Path
from ha_auth_component import HAAuthenticationComponent


def test_token_validity(token: str) -> bool:
    """
    Test if a token is valid by making a test API call.
    
    Args:
        token: The token to test
        
    Returns:
        bool: True if token is valid
    """
    try:
        cmd = ["ha", "--api-token", token, "info"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return result.returncode == 0
    except Exception as e:
        print(f"Error testing token: {e}")
        return False


def setup_authentication_interactive():
    """Set up authentication interactively."""
    print("🏠 Home Assistant CLI Authentication Setup")
    print("=" * 50)
    
    # Check if token is already in environment
    existing_token = os.getenv('HA_TOKEN')
    if existing_token:
        print(f"Found existing HA_TOKEN in environment")
        if test_token_validity(existing_token):
            print("✅ Existing token is valid!")
            return existing_token
        else:
            print("❌ Existing token is invalid")
    
    print("\nTo get a Long-Lived Access Token:")
    print("1. Open Home Assistant in your browser")
    print("2. Click your profile (bottom left)")
    print("3. Scroll to 'Long-Lived Access Tokens'")
    print("4. Click 'Create Token'")
    print("5. Give it a name like 'HA CLI Access'")
    print("6. Copy the token")
    print()
    
    # Get token from user
    token = input("Paste your Long-Lived Access Token here: ").strip()
    
    if not token:
        print("❌ No token provided")
        return None
    
    # Test the token
    print("🔍 Testing token...")
    if test_token_validity(token):
        print("✅ Token is valid!")
        
        # Ask if user wants to save it
        save_choice = input("Save token to environment? (y/n): ").lower().strip()
        if save_choice == 'y':
            # Create a simple script to export the token
            script_path = Path.home() / "set_ha_token.sh"
            with open(script_path, 'w') as f:
                f.write(f"#!/bin/bash\nexport HA_TOKEN='{token}'\n")
            script_path.chmod(0o700)
            print(f"✅ Token saved to {script_path}")
            print(f"Run: source {script_path}")
        
        return token
    else:
        print("❌ Token is invalid")
        return None


def setup_authentication_from_env():
    """Set up authentication from environment variable."""
    token = os.getenv('HA_TOKEN')
    if not token:
        print("❌ HA_TOKEN environment variable not set")
        return None
    
    print("🔍 Testing token from environment...")
    if test_token_validity(token):
        print("✅ Token is valid!")
        return token
    else:
        print("❌ Token from environment is invalid")
        return None


def create_ha_config_file(token: str) -> bool:
    """Create HA CLI configuration file."""
    try:
        auth_component = HAAuthenticationComponent()
        return auth_component.create_config_file(token)
    except Exception as e:
        print(f"❌ Failed to create config file: {e}")
        return False


def main():
    """Main setup function."""
    print("🚀 Starting HA CLI Authentication Setup")
    
    # Try environment first
    token = setup_authentication_from_env()
    
    # If no valid token from environment, go interactive
    if not token:
        token = setup_authentication_interactive()
    
    if not token:
        print("❌ Authentication setup failed")
        sys.exit(1)
    
    # Create config file
    print("📝 Creating HA CLI config file...")
    if create_ha_config_file(token):
        print("✅ Config file created successfully")
    else:
        print("⚠️  Config file creation failed, but token is valid")
    
    # Test final setup
    print("🧪 Testing final setup...")
    try:
        result = subprocess.run(["ha", "info"], capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            print("✅ HA CLI authentication setup complete!")
            print("You can now use commands like:")
            print("  ha addons list")
            print("  ha addons restart aicleaner")
            print("  ha addons logs aicleaner")
        else:
            print("⚠️  Setup complete but CLI test failed")
            print("Try using: ha --api-token YOUR_TOKEN command")
    except Exception as e:
        print(f"⚠️  Final test failed: {e}")
        print("Try using: ha --api-token YOUR_TOKEN command")


if __name__ == "__main__":
    main()
