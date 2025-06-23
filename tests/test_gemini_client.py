import pytest
import logging
from unittest.mock import patch, MagicMock
from aicleaner.gemini_client import GeminiClient

@pytest.fixture
def gemini_client():
    """Pytest fixture for an initialized GeminiClient."""
    with patch('google.generativeai.configure'), patch('google.generativeai.GenerativeModel'):
        return GeminiClient(api_key="fake-key")

def test_client_initialization():
    """Tests that the client initializes correctly."""
    with patch('google.generativeai.configure') as mock_configure, \
         patch('google.generativeai.GenerativeModel') as mock_model:
        
        client = GeminiClient(api_key="test-key")
        mock_configure.assert_called_once_with(api_key="test-key")
        mock_model.assert_called_once_with('gemini-pro-vision')
        assert client.model is not None

def test_client_initialization_fails():
    """Tests that initialization fails without an API key."""
    with pytest.raises(ValueError, match="Google Gemini API key is required."):
        GeminiClient(api_key=None)

def test_analyze_image_success(gemini_client, caplog):
    """Tests the analyze_image method for a successful analysis."""
    mock_gemini_response = MagicMock()
    mock_gemini_response.text = '```json\n{"score": 85, "tasks": ["Clean the floor"]}\n```'
    gemini_client.model.generate_content.return_value = mock_gemini_response

    with patch('os.path.exists', return_value=True):
        with patch('google.generativeai.upload_file') as mock_upload:
            with caplog.at_level(logging.INFO):
                analysis = gemini_client.analyze_image('fake/path.jpg')

                mock_upload.assert_called_once_with(path='fake/path.jpg')
                assert analysis['score'] == 85
                assert analysis['tasks'] == ["Clean the floor"]
                assert "Successfully parsed Gemini response. Score: 85" in caplog.text

def test_analyze_image_invalid_path(gemini_client, caplog):
    """Tests analyze_image with an invalid file path."""
    with patch('os.path.exists', return_value=False):
        analysis = gemini_client.analyze_image('nonexistent/path.jpg')
        assert analysis is None
        assert "Invalid image path provided: nonexistent/path.jpg" in caplog.text

def test_analyze_image_api_error(gemini_client, caplog):
    """Tests analyze_image when the Gemini API call fails."""
    gemini_client.model.generate_content.side_effect = Exception("API Failure")

    with patch('os.path.exists', return_value=True):
        with patch('google.generativeai.upload_file'):
            analysis = gemini_client.analyze_image('fake/path.jpg')
            assert analysis is None
            assert "Error analyzing image with Gemini: API Failure" in caplog.text

def test_analyze_image_bad_response(gemini_client, caplog):
    """Tests analyze_image with a malformed response from the API."""
    mock_gemini_response = MagicMock()
    mock_gemini_response.text = '{"score": 90, "missing_tasks_key": []}'
    gemini_client.model.generate_content.return_value = mock_gemini_response

    with patch('os.path.exists', return_value=True):
        with patch('google.generativeai.upload_file'):
            analysis = gemini_client.analyze_image('fake/path.jpg')
            assert analysis is None
            assert "Gemini response missing 'score' or 'tasks' key." in caplog.text