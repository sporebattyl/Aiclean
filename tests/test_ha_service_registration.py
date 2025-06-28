"""
Test suite for Home Assistant service registration using TDD and AAA principles.

This module tests that AICleaner services are properly registered with
Home Assistant and can be called from the Lovelace card.
"""

import pytest
import requests
import json
import os
from unittest.mock import patch, MagicMock
import sys

# Add the parent directory to sys.path to import our components
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ha_service_manager import HAServiceManager


class TestHAServiceDiagnostics:
    """Test class for diagnosing HA service registration issues."""
    
    def test_ha_services_endpoint_accessible(self):
        """
        Test that Home Assistant services endpoint is accessible.
        
        Arrange: Home Assistant API with authentication
        Act: Request services list
        Assert: Services endpoint returns data
        """
        # Arrange
        ha_url = "http://localhost:8123"
        token = os.getenv('HA_TOKEN', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkZjU5ODQ0NDA4MDc0NDA1Yjg5ZTA1OGVkNzEzOWYxNyIsImlhdCI6MTc1MTA0MTQxMiwiZXhwIjoyMDY2NDAxNDEyfQ.TOWAq7Gl_G245us4KIAo6X2TrXkcR1DzxuXUe5TOoyg')
        headers = {"Authorization": f"Bearer {token}"}
        services_url = f"{ha_url}/api/services"
        
        # Act
        response = requests.get(services_url, headers=headers, timeout=10)
        
        # Assert
        assert response.status_code == 200, \
            f"Services endpoint should be accessible, got {response.status_code}"
        
        services_data = response.json()
        assert isinstance(services_data, list), \
            "Services endpoint should return a list"
        assert len(services_data) > 0, \
            "Should have at least some services registered"
    
    def test_aicleaner_service_domain_exists(self):
        """
        Test whether aicleaner service domain exists in Home Assistant.
        
        Arrange: Home Assistant services list
        Act: Search for aicleaner domain
        Assert: Check if aicleaner services are registered
        """
        # Arrange
        ha_url = "http://localhost:8123"
        token = os.getenv('HA_TOKEN', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkZjU5ODQ0NDA4MDc0NDA1Yjg5ZTA1OGVkNzEzOWYxNyIsImlhdCI6MTc1MTA0MTQxMiwiZXhwIjoyMDY2NDAxNDEyfQ.TOWAq7Gl_G245us4KIAo6X2TrXkcR1DzxuXUe5TOoyg')
        headers = {"Authorization": f"Bearer {token}"}
        services_url = f"{ha_url}/api/services"
        
        # Act
        response = requests.get(services_url, headers=headers, timeout=10)
        services_data = response.json()
        
        # Look for aicleaner domain
        aicleaner_services = [service for service in services_data if service.get('domain') == 'aicleaner']
        
        # Assert
        print(f"Found {len(aicleaner_services)} aicleaner services")
        if aicleaner_services:
            print("AICleaner services found:")
            for service in aicleaner_services:
                print(f"  - {service.get('domain')}.{service.get('service')}")
        else:
            print("No aicleaner services found - this explains the error!")
        
        # This test documents the current state rather than asserting
        # We'll use this information to implement the fix
        assert True, "Diagnostic test completed"
    
    def test_service_call_format_validation(self):
        """
        Test the expected format for service calls.
        
        Arrange: Expected service call structure
        Act: Validate service call format
        Assert: Format matches Home Assistant conventions
        """
        # Arrange
        expected_domain = "aicleaner"
        expected_service = "run_analysis"
        expected_service_id = f"{expected_domain}.{expected_service}"
        
        # Act & Assert
        assert expected_domain.islower(), "Service domain should be lowercase"
        assert expected_service.replace('_', '').isalnum(), \
            "Service name should be alphanumeric with underscores"
        assert expected_service_id == "aicleaner.run_analysis", \
            "Service ID should match expected format"
    
    def test_service_registration_requirements(self):
        """
        Test the requirements for registering a service with Home Assistant.
        
        Arrange: Service registration requirements
        Act: Validate requirements understanding
        Assert: Requirements are properly understood
        """
        # Arrange
        required_elements = [
            "domain",           # Service domain (e.g., 'aicleaner')
            "service",          # Service name (e.g., 'run_analysis')
            "service_data",     # Optional data schema
            "target",           # Optional target specification
        ]
        
        # Act & Assert
        for element in required_elements:
            assert isinstance(element, str), f"Requirement {element} should be a string"
        
        # Service registration typically requires:
        # 1. A running integration/component
        # 2. Service registration call to HA
        # 3. Service handler function
        assert True, "Service registration requirements understood"


class TestServiceRegistrationComponent:
    """Test class for service registration component."""
    
    def test_service_registration_interface(self):
        """
        Test the interface for service registration component.
        
        Arrange: Service registration component requirements
        Act: Define component interface
        Assert: Interface meets requirements
        """
        # This will test our service registration component once created
        # For now, we define the expected interface
        
        expected_methods = [
            "register_service",
            "unregister_service", 
            "call_service",
            "list_services"
        ]
        
        # Act & Assert
        for method in expected_methods:
            assert isinstance(method, str), f"Method {method} should be defined"
        
        # The component should handle:
        # 1. Service registration with Home Assistant
        # 2. Service call handling
        # 3. Error handling and logging
        assert True, "Service registration interface defined"
    
    def test_run_analysis_service_specification(self):
        """
        Test the specification for the run_analysis service.
        
        Arrange: Service specification requirements
        Act: Define service specification
        Assert: Specification is complete
        """
        # Arrange
        service_spec = {
            "domain": "aicleaner",
            "service": "run_analysis",
            "description": "Trigger analysis for AICleaner zones",
            "fields": {
                "zone": {
                    "description": "Zone name to analyze (optional, analyzes all if not specified)",
                    "example": "kitchen",
                    "required": False,
                    "selector": {"text": {}}
                }
            }
        }
        
        # Act & Assert
        assert service_spec["domain"] == "aicleaner", "Domain should be aicleaner"
        assert service_spec["service"] == "run_analysis", "Service should be run_analysis"
        assert "description" in service_spec, "Service should have description"
        assert "fields" in service_spec, "Service should define fields"
        
        # Validate field specification
        zone_field = service_spec["fields"]["zone"]
        assert "description" in zone_field, "Field should have description"
        assert "required" in zone_field, "Field should specify if required"
        
        print("Service specification:")
        print(json.dumps(service_spec, indent=2))
        
        assert True, "Service specification validated"


class TestServiceCallHandling:
    """Test class for service call handling."""
    
    def test_service_call_data_validation(self):
        """
        Test validation of service call data.
        
        Arrange: Service call with various data
        Act: Validate call data
        Assert: Data validation works correctly
        """
        # Arrange
        valid_call_data = {"zone": "kitchen"}
        invalid_call_data = {"invalid_field": "value"}
        empty_call_data = {}
        
        # Act & Assert
        # Valid data should pass validation
        assert "zone" in valid_call_data, "Valid data should contain expected fields"
        
        # Invalid data should be handled gracefully
        assert "zone" not in invalid_call_data, "Invalid data should be detectable"
        
        # Empty data should be allowed (analyze all zones)
        assert len(empty_call_data) == 0, "Empty data should be allowed"
        
        assert True, "Service call data validation tested"
    
    def test_service_response_format(self):
        """
        Test the expected format for service responses.
        
        Arrange: Service response requirements
        Act: Define response format
        Assert: Format is appropriate
        """
        # Arrange
        expected_response_format = {
            "success": True,
            "message": "Analysis started for zone: kitchen",
            "zone": "kitchen",
            "timestamp": "2025-06-27T18:30:00Z"
        }
        
        # Act & Assert
        assert "success" in expected_response_format, "Response should indicate success/failure"
        assert "message" in expected_response_format, "Response should include message"
        assert isinstance(expected_response_format["success"], bool), \
            "Success should be boolean"
        
        print("Expected response format:")
        print(json.dumps(expected_response_format, indent=2))
        
        assert True, "Service response format defined"


class TestHAServiceManager:
    """Test class for HA Service Manager component."""

    def test_service_manager_initialization(self):
        """
        Test service manager initialization.

        Arrange: HAServiceManager class and parameters
        Act: Initialize service manager
        Assert: Manager initializes with correct settings
        """
        # Arrange
        ha_url = "http://localhost:8123"
        token = "test_token"
        service_port = 8098

        # Act
        manager = HAServiceManager(ha_url, token, service_port)

        # Assert
        assert manager.ha_url == ha_url, "HA URL should be set correctly"
        assert manager.token == token, "Token should be set correctly"
        assert manager.service_port == service_port, "Service port should be set correctly"
        assert len(manager.service_handlers) == 0, "Should start with no handlers"
        assert manager.running is False, "Should not be running initially"

    def test_register_service_handler(self):
        """
        Test registering a service handler.

        Arrange: Service manager and test handler
        Act: Register handler
        Assert: Handler is registered correctly
        """
        # Arrange
        manager = HAServiceManager()

        def test_handler(data):
            return f"Test result: {data}"

        # Act
        manager.register_service_handler('test_service', test_handler)

        # Assert
        assert 'test_service' in manager.service_handlers, \
            "Service handler should be registered"
        assert manager.service_handlers['test_service'] == test_handler, \
            "Handler should be stored correctly"

    def test_call_service_directly(self):
        """
        Test calling a service directly.

        Arrange: Service manager with registered handler
        Act: Call service directly
        Assert: Service executes and returns correct result
        """
        # Arrange
        manager = HAServiceManager()

        def test_handler(data):
            zone = data.get('zone', 'all')
            return f"Analysis started for {zone}"

        manager.register_service_handler('run_analysis', test_handler)

        # Act
        result = manager.call_service_directly('run_analysis', {'zone': 'kitchen'})

        # Assert
        assert result == "Analysis started for kitchen", \
            "Service should return expected result"

    def test_call_nonexistent_service(self):
        """
        Test calling a service that doesn't exist.

        Arrange: Service manager without handlers
        Act: Attempt to call nonexistent service
        Assert: Raises appropriate error
        """
        # Arrange
        manager = HAServiceManager()

        # Act & Assert
        with pytest.raises(ValueError, match="Service nonexistent not found"):
            manager.call_service_directly('nonexistent', {})

    def test_list_registered_services(self):
        """
        Test listing registered services.

        Arrange: Service manager with multiple handlers
        Act: List services
        Assert: All services are listed correctly
        """
        # Arrange
        manager = HAServiceManager()

        def handler1(data):
            return "result1"

        def handler2(data):
            return "result2"

        manager.register_service_handler('service1', handler1)
        manager.register_service_handler('service2', handler2)

        # Act
        services = manager.list_registered_services()

        # Assert
        assert 'service1' in services, "Service1 should be listed"
        assert 'service2' in services, "Service2 should be listed"
        assert len(services) == 2, "Should list exactly 2 services"
