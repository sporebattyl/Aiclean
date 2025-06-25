# AI Cleaning Assistant - Design Document

This document is the single source of truth for all code structure, patterns, and style for the AICleaner Home Assistant add-on.

---

## 1. Core Principles

*   **Inch-by-Inch:** Build and test in the smallest possible increments.
*   **Log Everything:** Use extensive logging for clear debugging.
*   **Mock First:** Mock all external dependencies (APIs, services) before implementing real calls.

---

## 2. Python Application Structure (`aicleaner.py`)

The application will be structured around a single class, `AICleaner`, to manage state, configuration, and all interactions with external services.

```python
# aicleaner.py

class AICleaner:
    def __init__(self, config_path):
        """
        Initializes the AICleaner application.
        - Loads configuration from config.yaml.
        - Initializes clients for Home Assistant and Google Gemini.
        """
        pass

    def get_camera_snapshot(self):
        """
        Connects to the specified Home Assistant camera entity and saves a snapshot.
        """
        pass

    def analyze_image_with_gemini(self, image_path):
        """
        Submits the image snapshot to the Google Gemini Vision API.
        - Returns a cleanliness score and a to-do list.
        """
        pass

    def update_ha_sensor(self, score):
        """
        Creates or updates the Home Assistant sensor with the new cleanliness score.
        """
        pass

    def update_ha_todolist(self, tasks):
        """
        Populates the specified Home Assistant to-do list with tasks from Gemini.
        """
        pass

    def run(self):
        """
        The main application loop.
        - Runs periodically based on the configured interval.
        - Orchestrates the process: snapshot -> analyze -> update HA.
        """
        pass

if __name__ == "__main__":
    # Main execution block
    cleaner = AICleaner(config_path='config.yaml')
    cleaner.run()
```

---

## 3. Configuration Management

Configuration will be managed via the `config.yaml` file. The `AICleaner` class will load this file at initialization.

**`config.yaml` Structure:**

```yaml
home_assistant:
  api_url: "http://homeassistant.local:8123"
  token: "YOUR_HA_TOKEN"
  camera_entity_id: "camera.living_room"
  todolist_entity_id: "todo.cleaning_list"
  sensor_entity_id: "sensor.room_cleanliness_score"

google_gemini:
  api_key: "YOUR_GEMINI_API_KEY"

application:
  analysis_interval_minutes: 60
```

The `AICleaner` class will use a dedicated method, `_load_config`, to parse this YAML file and store the values as instance attributes.

---

## 4. API Interaction (Gemini & Home Assistant)

API interactions will be handled by dedicated methods within the `AICleaner` class.

### Home Assistant API
- **Authentication:** Uses a long-lived access token provided in `config.yaml`.
- **Actions:**
    - `camera/snapshot`: To get an image from the specified camera entity.
    - `states/<sensor_entity_id>`: To create or update the cleanliness score sensor.
    - `todo/add_item`: To add tasks to the specified to-do list.
- **Library:** The `requests` library will be used for making direct HTTP requests to the Home Assistant REST API.

### Google Gemini API
- **Authentication:** Uses an API key provided in `config.yaml`.
- **Action:** Submits a `POST` request to the Gemini Vision API endpoint with the image data and a prompt asking for a cleanliness score and to-do list.
- **Library:** The `google-generativeai` Python client library will be used for simplicity and robustness.

---
---

## 5. Testing Strategy

Testing will be divided into three layers to ensure robustness and reliability.

### 5.1. Unit Tests
- **Framework:** `pytest`
- **Focus:** Test individual methods of the `AICleaner` class in complete isolation.
- **Mocks:** Use `pytest-mock` to patch all external dependencies, including:
    - `requests` library calls to the Home Assistant API.
    - `google-generativeai` library calls to the Gemini API.
    - File system operations (e.g., saving a camera snapshot).
- **Examples:**
    - Test `_load_config` with a sample `config.yaml`.
    - Test that `update_ha_sensor` constructs the correct API request payload.

### 5.2. Integration Tests
- **Framework:** `pytest`
- **Focus:** Test the collaboration between methods within the `AICleaner` class and mocked external services.
- **Mocks:**
    - A mock Home Assistant server (e.g., using `requests-mock`) that responds to API calls for snapshots, sensors, and to-do lists.
    - A mock Gemini API that returns predictable scores and task lists for given images.
- **Example:**
    - An integration test will run the full `run()` loop, verifying that a (mocked) camera snapshot is correctly processed, a (mocked) Gemini analysis is triggered, and the (mocked) Home Assistant entities are updated as expected.

### 5.3. End-to-End (E2E) Manual Testing
- **Environment:** A live Home Assistant OS instance with the add-on installed.
- **Procedure:**
    1. Configure the add-on with a valid camera entity, API keys, and to-do list.
    2. Manually trigger the add-on's execution.
    3. Verify that a new sensor for the cleanliness score is created or updated in Home Assistant.
    4. Verify that the specified to-do list is populated with actionable tasks.
    5. Check the add-on logs for any errors or unexpected behavior.