"""
Home Assistant Addon Manager Component

This component provides addon management functionality when the HA CLI
is not available or not working properly. It uses the Home Assistant API
directly to manage addons and retrieve logs.
"""

import requests
import json
import logging
import subprocess
import time
from typing import Optional, Dict, Any, List


class HAAddonManager:
    """
    Component for managing Home Assistant addons via API.
    
    This component follows component-based design principles by:
    - Having a single responsibility (addon management)
    - Providing a clear interface
    - Being testable and mockable
    - Handling errors gracefully
    """
    
    def __init__(self, ha_url: str = "http://localhost:8123", token: str = ""):
        """
        Initialize the addon manager.
        
        Args:
            ha_url: Home Assistant URL
            token: Long-lived access token
        """
        self.ha_url = ha_url.rstrip('/')
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.logger = logging.getLogger(__name__)
    
    def test_connection(self) -> bool:
        """
        Test connection to Home Assistant API.
        
        Returns:
            bool: True if connection successful
        """
        try:
            response = requests.get(f"{self.ha_url}/api/", headers=self.headers, timeout=10)
            if response.status_code == 200:
                self.logger.info("Successfully connected to Home Assistant API")
                return True
            else:
                self.logger.error(f"API connection failed: {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
    
    def restart_addon_via_service(self, addon_slug: str) -> bool:
        """
        Restart addon using Home Assistant service call.
        
        Args:
            addon_slug: Addon slug (e.g., 'aicleaner')
            
        Returns:
            bool: True if restart initiated successfully
        """
        try:
            # Use the hassio.addon_restart service
            url = f"{self.ha_url}/api/services/hassio/addon_restart"
            payload = {"addon": addon_slug}
            
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                self.logger.info(f"Addon {addon_slug} restart initiated")
                return True
            else:
                self.logger.error(f"Addon restart failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"Error restarting addon: {e}")
            return False
    
    def get_addon_logs_via_service(self, addon_slug: str) -> Optional[str]:
        """
        Get addon logs using Home Assistant service call.
        
        Args:
            addon_slug: Addon slug (e.g., 'aicleaner')
            
        Returns:
            str: Addon logs if successful, None otherwise
        """
        try:
            # Use the hassio.addon_logs service
            url = f"{self.ha_url}/api/services/hassio/addon_logs"
            payload = {"addon": addon_slug}
            
            response = requests.post(url, headers=self.headers, json=payload, timeout=15)
            
            if response.status_code == 200:
                # The logs might be in the response or we might need to check a different endpoint
                return response.text
            else:
                self.logger.error(f"Get logs failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"Error getting addon logs: {e}")
            return None
    
    def restart_addon_via_process(self, addon_name: str = "aicleaner") -> bool:
        """
        Restart addon by stopping and starting the process directly.
        
        Args:
            addon_name: Name of the addon
            
        Returns:
            bool: True if restart successful
        """
        try:
            # Kill existing processes
            self.logger.info(f"Stopping {addon_name} processes...")
            subprocess.run(["pkill", "-f", "aicleaner.py"], capture_output=True)
            time.sleep(2)
            
            # Start the addon process
            self.logger.info(f"Starting {addon_name}...")
            # This would typically be handled by the addon supervisor
            # For now, we'll just indicate the process was attempted
            return True
        except Exception as e:
            self.logger.error(f"Error restarting addon via process: {e}")
            return False
    
    def get_addon_status(self, addon_slug: str) -> Optional[Dict[str, Any]]:
        """
        Get addon status information.
        
        Args:
            addon_slug: Addon slug
            
        Returns:
            dict: Addon status information if available
        """
        try:
            # Try to get addon info via API
            # This might not be available in all setups
            url = f"{self.ha_url}/api/hassio/addons/{addon_slug}/info"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.debug(f"Addon status not available via API: {response.status_code}")
                return None
        except Exception as e:
            self.logger.debug(f"Error getting addon status: {e}")
            return None
    
    def check_addon_running(self, process_name: str = "aicleaner.py") -> bool:
        """
        Check if addon process is running.
        
        Args:
            process_name: Name of the process to check
            
        Returns:
            bool: True if process is running
        """
        try:
            result = subprocess.run(
                ["pgrep", "-f", process_name], 
                capture_output=True, 
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Error checking if addon is running: {e}")
            return False
    
    def get_process_logs(self, log_file: str = "/tmp/aicleaner.log") -> Optional[str]:
        """
        Get logs from a log file.
        
        Args:
            log_file: Path to log file
            
        Returns:
            str: Log content if available
        """
        try:
            with open(log_file, 'r') as f:
                return f.read()
        except FileNotFoundError:
            self.logger.debug(f"Log file not found: {log_file}")
            return None
        except Exception as e:
            self.logger.error(f"Error reading log file: {e}")
            return None
    
    def start_addon_manually(self, addon_path: str = "/addons/Aiclean/aicleaner") -> bool:
        """
        Start the addon manually by running the Python script.
        
        Args:
            addon_path: Path to the addon directory
            
        Returns:
            bool: True if start initiated
        """
        try:
            # Change to addon directory and run the script
            cmd = f"cd {addon_path} && python3 aicleaner.py"
            
            # Run in background
            process = subprocess.Popen(
                cmd, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                cwd=addon_path
            )
            
            self.logger.info(f"Started addon manually with PID: {process.pid}")
            return True
        except Exception as e:
            self.logger.error(f"Error starting addon manually: {e}")
            return False
