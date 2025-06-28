"""
Mock Gemini API client for testing
"""
import json
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, List, Optional


class MockGeminiResponse:
    """Mock Gemini API response"""
    
    def __init__(self, text: str):
        self.text = text


class MockGeminiClient:
    """Mock Gemini API client for testing"""
    
    def __init__(self):
        self.api_calls = []
        self.responses = []
        self.current_response_index = 0
        self.should_fail = False
        self.failure_message = "Mock Gemini API failure"
        
    def reset(self):
        """Reset mock state"""
        self.api_calls.clear()
        self.responses.clear()
        self.current_response_index = 0
        self.should_fail = False
        
    def add_response(self, response_data: Dict[str, Any]):
        """Add a mock response to the queue"""
        response_text = json.dumps(response_data)
        self.responses.append(MockGeminiResponse(response_text))
        
    def add_completed_tasks_response(self, completed_task_ids: List[str]):
        """Add a mock response for completed tasks analysis"""
        self.add_response(completed_task_ids)
        
    def add_new_tasks_response(self, new_tasks: List[str]):
        """Add a mock response for new tasks analysis"""
        self.add_response(new_tasks)
        
    def add_malformed_response(self, malformed_text: str):
        """Add a malformed response for error testing"""
        self.responses.append(MockGeminiResponse(malformed_text))
        
    def set_failure(self, should_fail: bool, message: str = "Mock Gemini API failure"):
        """Configure mock to simulate failures"""
        self.should_fail = should_fail
        self.failure_message = message
        
    def generate_content(self, content_parts: List[Any]) -> MockGeminiResponse:
        """Mock generate_content method"""
        # Record the API call
        call_info = {
            'method': 'generate_content',
            'content_parts': content_parts,
            'prompt': content_parts[0] if content_parts else None,
            'has_image': len(content_parts) > 1
        }
        self.api_calls.append(call_info)
        
        if self.should_fail:
            raise Exception(self.failure_message)
            
        if not self.responses:
            # Default response if none configured
            default_response = {"tasks": [], "score": 50}
            return MockGeminiResponse(json.dumps(default_response))
            
        # Return next response in queue
        if self.current_response_index < len(self.responses):
            response = self.responses[self.current_response_index]
            self.current_response_index += 1
            return response
        else:
            # Return last response if we've exhausted the queue
            return self.responses[-1]
            
    def get_api_calls(self) -> List[Dict[str, Any]]:
        """Get recorded API calls"""
        return self.api_calls.copy()
        
    def get_last_call(self) -> Optional[Dict[str, Any]]:
        """Get the last API call"""
        return self.api_calls[-1] if self.api_calls else None
        
    def get_last_prompt(self) -> Optional[str]:
        """Get the prompt from the last API call"""
        last_call = self.get_last_call()
        return last_call['prompt'] if last_call else None
        
    def call_count(self) -> int:
        """Get count of API calls"""
        return len(self.api_calls)
        
    def verify_prompt_contains(self, text: str) -> bool:
        """Verify that the last prompt contains specific text"""
        prompt = self.get_last_prompt()
        return text in prompt if prompt else False
        
    def verify_completed_tasks_prompt(self, active_tasks: List[Dict[str, Any]]) -> bool:
        """Verify that the prompt is correctly formatted for completed tasks analysis"""
        prompt = self.get_last_prompt()
        if not prompt:
            return False
            
        # Check for system prompt indicators
        if "state verification assistant" not in prompt.lower():
            return False
            
        # Check that active tasks are included
        for task in active_tasks:
            if task['description'] not in prompt:
                return False
                
        return True
        
    def verify_new_tasks_prompt(self, context: str, active_tasks: List[str], ignore_rules: List[str]) -> bool:
        """Verify that the prompt is correctly formatted for new tasks analysis"""
        prompt = self.get_last_prompt()
        if not prompt:
            return False
            
        # Check for system prompt indicators
        if "home organization assistant" not in prompt.lower():
            return False
            
        # Check that context is included
        if context not in prompt:
            return False
            
        # Check that active tasks are mentioned
        for task in active_tasks:
            if task not in prompt:
                return False
                
        # Check that ignore rules are included
        for rule in ignore_rules:
            if rule not in prompt:
                return False
                
        return True

    def add_completion_response(self, completed_task_ids: List[str]):
        """Add a mock response for basic completion analysis (alias for add_completed_tasks_response)"""
        self.add_completed_tasks_response(completed_task_ids)

    def add_confidence_response(self, confidence_data: List[Dict[str, Any]]):
        """Add a mock response for confidence scoring analysis"""
        self.add_response(confidence_data)
