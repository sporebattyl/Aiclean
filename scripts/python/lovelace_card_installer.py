#!/usr/bin/env python3
"""
Lovelace Card Installer Component

This component handles the installation of AICleaner Lovelace cards
into Home Assistant's www directory following component-based design principles.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any


class LovelaceCardInstaller:
    """
    Component for installing Lovelace cards into Home Assistant.
    
    This component follows component-based design principles by:
    - Having a single responsibility (card installation)
    - Providing a clear interface
    - Being testable and mockable
    - Handling errors gracefully
    """
    
    def __init__(self, ha_www_path: str = "/homeassistant/www"):
        """
        Initialize the card installer.
        
        Args:
            ha_www_path: Path to Home Assistant www directory
        """
        self.ha_www_path = Path(ha_www_path)
        self.logger = logging.getLogger(__name__)
        
        # Card files to install
        self.card_files = [
            "aicleaner-card.js",
            "aicleaner-card-editor.js"
        ]
    
    def check_ha_www_directory(self) -> bool:
        """
        Check if Home Assistant www directory exists and is writable.
        
        Returns:
            bool: True if directory is accessible
        """
        try:
            if not self.ha_www_path.exists():
                self.logger.error(f"Home Assistant www directory not found: {self.ha_www_path}")
                return False
            
            if not self.ha_www_path.is_dir():
                self.logger.error(f"Path is not a directory: {self.ha_www_path}")
                return False
            
            # Test write access
            test_file = self.ha_www_path / ".aicleaner_test"
            try:
                test_file.touch()
                test_file.unlink()
                self.logger.info(f"Home Assistant www directory is accessible: {self.ha_www_path}")
                return True
            except PermissionError:
                self.logger.error(f"No write permission to: {self.ha_www_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error checking www directory: {e}")
            return False
    
    def find_card_source_files(self, addon_path: str = "/addons/Aiclean/aicleaner/www") -> Dict[str, Path]:
        """
        Find the source card files in the addon directory.
        
        Args:
            addon_path: Path to addon www directory
            
        Returns:
            dict: Mapping of filename to source path
        """
        source_path = Path(addon_path)
        found_files = {}
        
        for filename in self.card_files:
            file_path = source_path / filename
            if file_path.exists():
                found_files[filename] = file_path
                self.logger.info(f"Found source file: {file_path}")
            else:
                self.logger.warning(f"Source file not found: {file_path}")
        
        return found_files
    
    def install_card_files(self, source_files: Dict[str, Path]) -> bool:
        """
        Install card files to Home Assistant www directory.
        
        Args:
            source_files: Mapping of filename to source path
            
        Returns:
            bool: True if installation successful
        """
        try:
            installed_files = []
            
            for filename, source_path in source_files.items():
                dest_path = self.ha_www_path / filename
                
                # Copy file
                shutil.copy2(source_path, dest_path)
                installed_files.append(dest_path)
                self.logger.info(f"Installed: {filename} -> {dest_path}")
            
            if installed_files:
                self.logger.info(f"Successfully installed {len(installed_files)} card files")
                return True
            else:
                self.logger.warning("No files were installed")
                return False
                
        except Exception as e:
            self.logger.error(f"Error installing card files: {e}")
            return False
    
    def create_installation_info(self) -> str:
        """
        Create installation information for the user.
        
        Returns:
            str: Installation instructions
        """
        instructions = """
🎯 AICleaner Lovelace Card Installation Complete!

📁 Files installed to: {www_path}
   • aicleaner-card.js
   • aicleaner-card-editor.js

📋 Next Steps:

1. Add Resource in Home Assistant:
   • Go to Settings → Dashboards → Resources
   • Click "Add Resource"
   • URL: /local/aicleaner-card.js
   • Resource Type: JavaScript Module
   • Click "Create"

2. Add Card to Dashboard:
   • Edit any dashboard
   • Click "Add Card"
   • Search for "AICleaner Card"
   • Configure and save

3. Refresh your browser if the card doesn't appear immediately

✅ The card should now be available in your dashboard!
""".format(www_path=self.ha_www_path)
        
        return instructions
    
    def verify_installation(self) -> bool:
        """
        Verify that the card files are properly installed.
        
        Returns:
            bool: True if installation is verified
        """
        try:
            all_installed = True
            
            for filename in self.card_files:
                file_path = self.ha_www_path / filename
                if file_path.exists() and file_path.stat().st_size > 0:
                    self.logger.info(f"Verified: {filename} ({file_path.stat().st_size} bytes)")
                else:
                    self.logger.error(f"Missing or empty: {filename}")
                    all_installed = False
            
            return all_installed
            
        except Exception as e:
            self.logger.error(f"Error verifying installation: {e}")
            return False
    
    def uninstall_card_files(self) -> bool:
        """
        Remove card files from Home Assistant www directory.
        
        Returns:
            bool: True if uninstallation successful
        """
        try:
            removed_files = []
            
            for filename in self.card_files:
                file_path = self.ha_www_path / filename
                if file_path.exists():
                    file_path.unlink()
                    removed_files.append(filename)
                    self.logger.info(f"Removed: {filename}")
            
            if removed_files:
                self.logger.info(f"Successfully removed {len(removed_files)} card files")
            else:
                self.logger.info("No card files found to remove")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing card files: {e}")
            return False
    
    def install_cards(self, addon_path: str = "/addons/Aiclean/aicleaner/www") -> bool:
        """
        Complete card installation process.
        
        Args:
            addon_path: Path to addon www directory
            
        Returns:
            bool: True if installation successful
        """
        self.logger.info("Starting AICleaner Lovelace card installation...")
        
        # Check Home Assistant www directory
        if not self.check_ha_www_directory():
            return False
        
        # Find source files
        source_files = self.find_card_source_files(addon_path)
        if not source_files:
            self.logger.error("No source files found for installation")
            return False
        
        # Install files
        if not self.install_card_files(source_files):
            return False
        
        # Verify installation
        if not self.verify_installation():
            self.logger.error("Installation verification failed")
            return False
        
        self.logger.info("AICleaner Lovelace card installation completed successfully!")
        return True


def main():
    """Main installation function."""
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    print("🚀 AICleaner Lovelace Card Installer")
    print("=" * 50)
    
    installer = LovelaceCardInstaller()
    
    # Install cards
    success = installer.install_cards()
    
    if success:
        print("\n" + installer.create_installation_info())
        return True
    else:
        print("\n❌ Installation failed. Check the logs above for details.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
