# AICleaner - AI-Powered Room Cleanliness Monitor for Home Assistant

AICleaner is a Home Assistant add-on that uses the Google Gemini Vision API to analyze images from a camera, determine a room's cleanliness, and create a to-do list for tidying up.

## Features

*   **Cleanliness Scoring:** Rates room cleanliness on a scale of 1-100.
*   **Automated To-Do Lists:** Generates a list of actionable cleaning tasks.
*   **Home Assistant Integration:**
    *   Creates a sensor to track the cleanliness score over time.
    *   Populates a to-do list entity with cleaning tasks.
*   **Configurable:** Set your camera, to-do list, and analysis frequency.

## Installation

1.  **Add Custom Repository:**
    *   In Home Assistant, navigate to **Settings > Add-ons > Add-on Store**.
    *   Click the three-dot menu in the top right and select **Repositories**.
    *   Add the URL to this repository.
2.  **Install the Add-on:**
    *   Find the "AICleaner" add-on in the store and click **Install**.

## Configuration

Before starting the add-on, you must configure it with the necessary API keys and entity IDs.

| Option                 | Description                                                                                                                             |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `CAMERA_ENTITY`        | The `entity_id` of the camera to use for snapshots (e.g., `camera.living_room`).                                                        |
| `TODO_LIST`            | The `entity_id` of the to-do list to populate (e.g., `todo.cleaning_list`).                                                             |
| `SENSOR_ENTITY`        | The `entity_id` for the cleanliness score sensor (e.g., `sensor.room_cleanliness_score`). This will be created if it doesn't exist.      |
| `API_KEY`              | Your Google Gemini API key. You can get one from [Google AI Studio](https://aistudio.google.com/app/apikey).                             |
| `FREQUENCY`            | The interval, in hours, between each analysis (e.g., `24` for daily).                                                                   |

## Usage

1.  **Start the Add-on:**
    *   Navigate to **Settings > Add-ons > AICleaner**.
    *   Click **Start**.
2.  **Check the Logs:**
    *   The add-on will log its activity in the **Log** tab. Check here for any errors.
3.  **View in Home Assistant:**
    *   A new sensor (e.g., `sensor.room_cleanliness_score`) will appear in your Home Assistant dashboard.
    *   The to-do list you specified will be populated with cleaning tasks.

## For Developers

This project's technical design, including its architecture, testing strategy, and API patterns, is detailed in the [`DesignDocument.md`](DesignDocument.md) file.