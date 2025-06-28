#!/usr/bin/env python3
"""
Debug script to understand why integration tests are failing
"""
import sys
import os
sys.path.append('tests')

from unittest.mock import Mock, patch
from tests.fixtures.test_configs import get_valid_zone_config
from tests.fixtures.test_states import get_single_zone_with_active_tasks
from tests.mocks.mock_ha_api import MockHAClient
from tests.mocks.mock_gemini_api import MockGeminiClient

# Mock external dependencies
with patch.dict('sys.modules', {
    'google': Mock(),
    'google.generativeai': Mock(),
    'google.generativeai.client': Mock(),
    'google.generativeai.generative_models': Mock(),
}):
    from aicleaner.aicleaner import Zone

def test_debug():
    print("=== DEBUG INTEGRATION TEST ===")
    
    # Arrange - exact same as integration test
    zone_config = get_valid_zone_config()
    zone_state = get_single_zone_with_active_tasks()['Kitchen']
    ha_client = MockHAClient()
    gemini_client = MockGeminiClient()
    
    # Configure responses
    completed_task_ids = ['task_1687392000_kitchen_0']
    new_tasks = ['Clean the microwave inside and out', 'Organize the spice rack']
    gemini_client.add_completed_tasks_response(completed_task_ids)
    gemini_client.add_new_tasks_response(new_tasks)
    
    print(f"Gemini responses configured: {len(gemini_client.responses)}")
    
    zone = Zone(zone_config, zone_state, ha_client, gemini_client)
    print(f"Zone created: {zone.name}")
    
    # Test camera snapshot
    print("\n--- Testing camera snapshot ---")
    image_path = zone.get_camera_snapshot()
    print(f"Image path: {image_path}")
    print(f"File exists: {os.path.exists(image_path) if image_path else False}")
    
    if image_path and os.path.exists(image_path):
        print(f"File size: {os.path.getsize(image_path)} bytes")
        
        # Test PIL directly
        try:
            from PIL import Image
            img = Image.open(image_path)
            print(f"PIL can open: {img.size}")
        except Exception as e:
            print(f"PIL error: {e}")
            return
    
    # Test individual analysis methods
    print("\n--- Testing individual analysis methods ---")
    
    try:
        print("Testing analyze_with_retry_logic...")
        result1 = zone.analyze_with_retry_logic(image_path, max_retries=1)
        print(f"Result: {result1}")
        print(f"Gemini calls so far: {gemini_client.call_count()}")
    except Exception as e:
        print(f"analyze_with_retry_logic failed: {e}")
    
    try:
        print("Testing analyze_with_confidence_scoring...")
        result2 = zone.analyze_with_confidence_scoring(image_path)
        print(f"Result: {result2}")
        print(f"Gemini calls so far: {gemini_client.call_count()}")
    except Exception as e:
        print(f"analyze_with_confidence_scoring failed: {e}")
    
    # Test full analysis cycle
    print("\n--- Testing full analysis cycle ---")
    try:
        # Reset gemini client
        gemini_client.reset()
        gemini_client.add_completed_tasks_response(completed_task_ids)
        gemini_client.add_new_tasks_response(new_tasks)
        
        updated_state = zone.run_analysis_cycle()
        print(f"Analysis cycle completed")
        print(f"Final Gemini calls: {gemini_client.call_count()}")
        print(f"Expected: 2")
        
        if gemini_client.call_count() == 2:
            print("✅ SUCCESS: Integration test should pass!")
        else:
            print("❌ FAILURE: Integration test will fail")
            
    except Exception as e:
        print(f"Full analysis cycle failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_debug()
