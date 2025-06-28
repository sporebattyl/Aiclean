"""
Test suite for Lovelace card loading and registration using TDD and AAA principles.

This module tests that the AICleaner Lovelace card loads correctly and
appears in the Home Assistant dashboard card picker.
"""

import pytest
import requests
import json
import re
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import sys

# Add the parent directory to sys.path to import our components
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lovelace_card_installer import LovelaceCardInstaller


class TestLovelaceCardLoading:
    """Test class for Lovelace card loading functionality."""
    
    def test_card_file_accessibility(self):
        """
        Test that the card JavaScript file is accessible via HTTP.
        
        Arrange: Static file server running on port 8099
        Act: Request the card file
        Assert: File is accessible and returns valid JavaScript
        """
        # Arrange
        card_url = "http://localhost:8099/aicleaner-card.js"
        
        # Act
        try:
            response = requests.get(card_url, timeout=10)
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Card file not accessible: {e}")
        
        # Assert
        assert response.status_code == 200, f"Card file should be accessible, got {response.status_code}"
        assert response.headers.get('content-type') == 'text/javascript', \
            "Content type should be text/javascript"
        assert len(response.text) > 1000, "Card file should contain substantial JavaScript code"
    
    def test_card_javascript_syntax(self):
        """
        Test that the card JavaScript has valid syntax and structure.
        
        Arrange: Card JavaScript content
        Act: Parse and validate JavaScript structure
        Assert: Contains required Lovelace card elements
        """
        # Arrange
        card_url = "http://localhost:8099/aicleaner-card.js"
        response = requests.get(card_url, timeout=10)
        card_content = response.text
        
        # Act & Assert
        assert "class AICleanerCard extends HTMLElement" in card_content, \
            "Card should define AICleanerCard class"
        assert "customElements.define('aicleaner-card'" in card_content, \
            "Card should register custom element"
        assert "window.customCards" in card_content, \
            "Card should register with customCards"
        assert "setConfig" in card_content, \
            "Card should have setConfig method"
        assert "set hass" in card_content, \
            "Card should have hass setter"
    
    def test_card_registration_structure(self):
        """
        Test that the card registration follows Home Assistant conventions.
        
        Arrange: Card JavaScript content
        Act: Extract registration code
        Assert: Registration follows HA Lovelace card conventions
        """
        # Arrange
        card_url = "http://localhost:8099/aicleaner-card.js"
        response = requests.get(card_url, timeout=10)
        card_content = response.text
        
        # Act
        # Look for customCards registration
        custom_cards_match = re.search(
            r'window\.customCards\.push\(\s*\{([^}]+)\}\s*\)', 
            card_content, 
            re.DOTALL
        )
        
        # Assert
        assert custom_cards_match is not None, \
            "Card should register with window.customCards"
        
        registration_content = custom_cards_match.group(1)
        assert "type:" in registration_content and "aicleaner-card" in registration_content, \
            "Registration should specify correct card type"
        assert "name:" in registration_content, \
            "Registration should specify card name"
        assert "description:" in registration_content, \
            "Registration should specify card description"
    
    def test_card_editor_file_accessibility(self):
        """
        Test that the card editor file is accessible.
        
        Arrange: Static file server running
        Act: Request the card editor file
        Assert: Editor file is accessible
        """
        # Arrange
        editor_url = "http://localhost:8099/aicleaner-card-editor.js"
        
        # Act
        try:
            response = requests.get(editor_url, timeout=10)
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Card editor file not accessible: {e}")
        
        # Assert
        assert response.status_code == 200, \
            f"Card editor should be accessible, got {response.status_code}"
        assert len(response.text) > 100, \
            "Card editor should contain JavaScript code"


class TestLovelaceResourceConfiguration:
    """Test class for Lovelace resource configuration."""
    
    def test_resource_url_format(self):
        """
        Test that the resource URL format is correct for Home Assistant.
        
        Arrange: Expected resource URL format
        Act: Validate URL structure
        Assert: URL follows HA resource conventions
        """
        # Arrange
        expected_url = "/addons/aicleaner/aicleaner-card.js"
        
        # Act & Assert
        assert expected_url.startswith("/"), "Resource URL should start with /"
        assert expected_url.endswith(".js"), "Resource URL should end with .js"
        assert "aicleaner-card" in expected_url, "URL should contain card name"
    
    def test_resource_accessibility_via_ha_proxy(self):
        """
        Test that the resource is accessible via Home Assistant proxy.
        
        Arrange: Home Assistant running with addon
        Act: Request resource via HA proxy path
        Assert: Resource is accessible through HA
        """
        # This test would require HA API access
        # Skip for now but structure is ready
        pytest.skip("Requires Home Assistant API access for proxy testing")


class TestCardLoadingDiagnostics:
    """Diagnostic tests for card loading issues."""
    
    def test_browser_console_error_simulation(self):
        """
        Test for common browser console errors that prevent card loading.
        
        Arrange: Card JavaScript content
        Act: Check for common error patterns
        Assert: No obvious syntax or loading issues
        """
        # Arrange
        card_url = "http://localhost:8099/aicleaner-card.js"
        response = requests.get(card_url, timeout=10)
        card_content = response.text
        
        # Act & Assert - Check for common issues
        assert "console.error" not in card_content.lower(), \
            "Card should not contain console.error calls"
        
        # Check for proper ES6 class syntax
        class_matches = re.findall(r'class\s+\w+\s+extends\s+HTMLElement', card_content)
        assert len(class_matches) >= 1, \
            "Card should have at least one proper class definition"
        
        # Check for proper method definitions
        assert "constructor()" in card_content, \
            "Card class should have constructor"
    
    def test_card_dependencies(self):
        """
        Test that the card doesn't have unmet dependencies.
        
        Arrange: Card JavaScript content
        Act: Check for external dependencies
        Assert: No unmet dependencies that could prevent loading
        """
        # Arrange
        card_url = "http://localhost:8099/aicleaner-card.js"
        response = requests.get(card_url, timeout=10)
        card_content = response.text
        
        # Act & Assert
        # Check for import statements that might fail
        import_matches = re.findall(r'import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]', card_content)
        
        # If there are imports, they should be relative or known libraries
        for import_path in import_matches:
            assert not import_path.startswith('http'), \
                f"Card should not import from external URLs: {import_path}"
    
    def test_card_size_reasonable(self):
        """
        Test that the card file size is reasonable for loading.
        
        Arrange: Card file
        Act: Check file size
        Assert: File size is reasonable for web loading
        """
        # Arrange
        card_url = "http://localhost:8099/aicleaner-card.js"
        response = requests.get(card_url, timeout=10)
        
        # Act
        file_size = len(response.content)
        
        # Assert
        assert file_size > 1000, "Card file should contain substantial code"
        assert file_size < 1000000, "Card file should not be excessively large (>1MB)"
        
        print(f"Card file size: {file_size} bytes")


class TestCardRegistrationDebugging:
    """Tests to debug card registration issues."""
    
    def test_custom_element_name_uniqueness(self):
        """
        Test that the custom element name is unique and properly formatted.
        
        Arrange: Card registration code
        Act: Extract custom element name
        Assert: Name follows conventions and is unique
        """
        # Arrange
        card_url = "http://localhost:8099/aicleaner-card.js"
        response = requests.get(card_url, timeout=10)
        card_content = response.text
        
        # Act
        element_match = re.search(r"customElements\.define\(['\"]([^'\"]+)['\"]", card_content)
        
        # Assert
        assert element_match is not None, "Should find customElements.define call"
        element_name = element_match.group(1)
        
        assert element_name == "aicleaner-card", \
            f"Element name should be 'aicleaner-card', got '{element_name}'"
        assert "-" in element_name, \
            "Custom element name should contain hyphen"
        assert element_name.islower(), \
            "Custom element name should be lowercase"
    
    def test_card_type_consistency(self):
        """
        Test that card type is consistent across registration points.
        
        Arrange: Card content with multiple registration points
        Act: Extract card type from different locations
        Assert: Card type is consistent everywhere
        """
        # Arrange
        card_url = "http://localhost:8099/aicleaner-card.js"
        response = requests.get(card_url, timeout=10)
        card_content = response.text
        
        # Act
        # Find customElements.define
        element_match = re.search(r"customElements\.define\(['\"]([^'\"]+)['\"]", card_content)
        
        # Find window.customCards registration
        cards_match = re.search(r"type:\s*['\"]([^'\"]+)['\"]", card_content)
        
        # Assert
        assert element_match is not None, "Should find element registration"
        assert cards_match is not None, "Should find customCards registration"
        
        element_type = element_match.group(1)
        cards_type = cards_match.group(1)
        
        assert element_type == cards_type, \
            f"Card type should be consistent: element='{element_type}', cards='{cards_type}'"


class TestLovelaceCardInstaller:
    """Test class for Lovelace card installer component."""

    def test_installer_initialization(self):
        """
        Test installer initialization.

        Arrange: LovelaceCardInstaller class
        Act: Initialize installer
        Assert: Installer initializes with correct defaults
        """
        # Arrange & Act
        installer = LovelaceCardInstaller()

        # Assert
        assert installer.ha_www_path == Path("/homeassistant/www"), \
            "Default www path should be set correctly"
        assert "aicleaner-card.js" in installer.card_files, \
            "Card files should include main card file"
        assert "aicleaner-card-editor.js" in installer.card_files, \
            "Card files should include editor file"

    def test_check_ha_www_directory_exists(self):
        """
        Test checking Home Assistant www directory when it exists.

        Arrange: Temporary directory as www path
        Act: Check directory
        Assert: Returns True for accessible directory
        """
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            installer = LovelaceCardInstaller(temp_dir)

            # Act
            result = installer.check_ha_www_directory()

            # Assert
            assert result is True, "Should return True for accessible directory"

    def test_check_ha_www_directory_missing(self):
        """
        Test checking Home Assistant www directory when it doesn't exist.

        Arrange: Non-existent directory path
        Act: Check directory
        Assert: Returns False for missing directory
        """
        # Arrange
        installer = LovelaceCardInstaller("/nonexistent/path")

        # Act
        result = installer.check_ha_www_directory()

        # Assert
        assert result is False, "Should return False for missing directory"

    def test_find_card_source_files_success(self):
        """
        Test finding card source files when they exist.

        Arrange: Temporary directory with card files
        Act: Find source files
        Assert: Returns correct file mapping
        """
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock card files
            card_file = Path(temp_dir) / "aicleaner-card.js"
            editor_file = Path(temp_dir) / "aicleaner-card-editor.js"
            card_file.write_text("// Mock card file")
            editor_file.write_text("// Mock editor file")

            installer = LovelaceCardInstaller()

            # Act
            found_files = installer.find_card_source_files(temp_dir)

            # Assert
            assert "aicleaner-card.js" in found_files, \
                "Should find main card file"
            assert "aicleaner-card-editor.js" in found_files, \
                "Should find editor file"
            assert found_files["aicleaner-card.js"] == card_file, \
                "Should return correct path for card file"

    def test_install_card_files_success(self):
        """
        Test successful installation of card files.

        Arrange: Source files and destination directory
        Act: Install files
        Assert: Files are copied correctly
        """
        # Arrange
        with tempfile.TemporaryDirectory() as source_dir, \
             tempfile.TemporaryDirectory() as dest_dir:

            # Create source files
            source_file = Path(source_dir) / "aicleaner-card.js"
            source_file.write_text("// Test card content")

            source_files = {"aicleaner-card.js": source_file}
            installer = LovelaceCardInstaller(dest_dir)

            # Act
            result = installer.install_card_files(source_files)

            # Assert
            assert result is True, "Installation should succeed"
            dest_file = Path(dest_dir) / "aicleaner-card.js"
            assert dest_file.exists(), "File should be copied to destination"
            assert dest_file.read_text() == "// Test card content", \
                "File content should be preserved"
