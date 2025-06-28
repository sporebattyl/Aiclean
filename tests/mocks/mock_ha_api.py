"""
Mock Home Assistant API client for testing
"""
import json
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, Optional


class MockHAClient:
    """Mock Home Assistant API client for testing"""
    
    def __init__(self):
        self.api_calls = []
        self.responses = {}
        self.should_fail = False
        self.failure_message = "Mock API failure"
        
    def reset(self):
        """Reset mock state"""
        self.api_calls.clear()
        self.responses.clear()
        self.should_fail = False
        
    def set_response(self, endpoint: str, response: Any):
        """Set mock response for specific endpoint"""
        self.responses[endpoint] = response
        
    def set_failure(self, should_fail: bool, message: str = "Mock API failure"):
        """Configure mock to simulate failures"""
        self.should_fail = should_fail
        self.failure_message = message
        
    def get_camera_snapshot(self, entity_id: str, filename: str) -> bool:
        """Mock camera snapshot API call"""
        call_info = {
            'method': 'get_camera_snapshot',
            'entity_id': entity_id,
            'filename': filename
        }
        self.api_calls.append(call_info)

        if self.should_fail:
            raise Exception(self.failure_message)

        # Copy the real room photo for realistic testing
        import os
        import shutil
        import time

        def force_file_sync(filepath):
            """
            Forces a file to be written to disk and waits briefly
            to ensure filesystem consistency.
            """
            try:
                fd = os.open(filepath, os.O_RDONLY)
                os.fsync(fd)
                os.close(fd)
                time.sleep(0.02)  # A small but often necessary delay
            except Exception as e:
                print(f"Warning: Could not force file sync for {filepath}: {e}")

        # Get the path to the real room photo
        current_dir = os.path.dirname(os.path.abspath(__file__))
        real_photo_path = os.path.join(current_dir, '..', 'fixtures', 'messyroom.jpg')

        if os.path.exists(real_photo_path):
            # Copy the real photo - this is guaranteed to be a valid JPEG
            shutil.copy2(real_photo_path, filename)
            # Force filesystem sync to ensure file is ready for reading
            force_file_sync(filename)
        else:
            # Fallback: create a simple valid image if the real photo is missing
            from PIL import Image
            img = Image.new('RGB', (100, 100), color='red')
            img.save(filename, 'JPEG', quality=95)
            # Force filesystem sync for the created image too
            force_file_sync(filename)

        return True
        
    def add_todo_item(self, entity_id: str, item: str, description=None) -> bool:
        """Mock todo list add item API call"""
        call_info = {
            'method': 'add_todo_item',
            'entity_id': entity_id,
            'item': item,
            'description': description
        }
        self.api_calls.append(call_info)
        
        if self.should_fail:
            raise Exception(self.failure_message)
            
        return True
        
    def update_todo_item(self, entity_id: str, item: str, status: str) -> bool:
        """Mock todo list update item API call"""
        call_info = {
            'method': 'update_todo_item',
            'entity_id': entity_id,
            'item': item,
            'status': status
        }
        self.api_calls.append(call_info)
        
        if self.should_fail:
            raise Exception(self.failure_message)
            
        return True
        
    def update_sensor(self, entity_id: str, state: Any, attributes: Dict[str, Any] = None) -> bool:
        """Mock sensor update API call"""
        call_info = {
            'method': 'update_sensor',
            'entity_id': entity_id,
            'state': state,
            'attributes': attributes or {}
        }
        self.api_calls.append(call_info)
        
        if self.should_fail:
            raise Exception(self.failure_message)
            
        return True
        
    def send_notification(self, service: str, message: str, title: str = None) -> bool:
        """Mock notification service API call"""
        call_info = {
            'method': 'send_notification',
            'service': service,
            'message': message,
            'title': title
        }
        self.api_calls.append(call_info)
        
        if self.should_fail:
            raise Exception(self.failure_message)
            
        return True
        
    def get_api_calls(self, method: str = None) -> list:
        """Get recorded API calls, optionally filtered by method"""
        if method:
            return [call for call in self.api_calls if call['method'] == method]
        return self.api_calls.copy()
        
    def get_last_call(self, method: str = None) -> Optional[Dict[str, Any]]:
        """Get the last API call, optionally filtered by method"""
        calls = self.get_api_calls(method)
        return calls[-1] if calls else None
        
    def call_count(self, method: str = None) -> int:
        """Get count of API calls, optionally filtered by method"""
        return len(self.get_api_calls(method))
