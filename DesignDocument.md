AI Cleaning Assistant - Design Document (v2.0)
This document is the single source of truth for all backend code structure, data models, API interactions, and style for the AICleaner Home Assistant add-on, Version 2.0.

1. Core Principles
Inch-by-Inch: Build and test in the smallest possible increments.

Log Everything: Use extensive, structured logging for clear debugging.

Mock First: Mock all external dependencies (APIs, services) before implementing real calls.

State is Sacred: Treat the persistent state file as a database. Ensure all read/write operations are atomic and fault-tolerant.

2. Python Application Structure (aicleaner.py)
The application is architected around a central AICleaner controller that manages multiple Zone objects. This decouples global management from the specific logic for each configured area.

2.1 Zone Class
Represents a single configured "Space" (e.g., Kitchen). It encapsulates all logic and state for one area.

# aicleaner.py

class Zone:
    def __init__(self, zone_config, state, ha_client, gemini_client):
        """
        Manages an individual zone.
        - zone_config (dict): The specific configuration for this zone from options.json.
        - state (dict): The persistent state for this zone (active/completed tasks).
        - ha_client: An initialized Home Assistant API client instance.
        - gemini_client: An initialized Gemini API client instance.
        """
        self.name = zone_config['name']
        self.camera_entity = zone_config['camera_entity']
        # ... other config attributes ...
        self.state = state
        self.ha_client = ha_client
        self.gemini_client = gemini_client

    def get_camera_snapshot(self):
        """Calls the Home Assistant camera.snapshot service and saves the image to a temporary file. Returns the file path."""
        pass

    def analyze_image_for_completed_tasks(self, image_path):
        """
        Analyzes an image against the current active_tasks list.
        - Constructs a specific prompt for Gemini asking to identify completed tasks.
        - Parses the response and returns a list of task IDs that are now complete.
        """
        pass

    def analyze_image_for_new_tasks(self, image_path):
        """
        Analyzes an image to find new tasks.
        - Constructs a prompt for Gemini, providing context about existing tasks and ignore rules to prevent duplicates.
        - Returns a list of new task descriptions.
        """
        pass

    def send_notification(self, message_type, context):
        """
        Constructs and sends a notification message via the configured HA service.
        - message_type (str): 'task_created' or 'task_completed'.
        - context (dict): Contains task details for message formatting.
        - Uses the configured 'personality' to format the final message string.
        """
        pass

    def run_analysis_cycle(self):
        """
        Orchestrates the full, stateful analysis loop for this single zone.
        1. Get camera snapshot.
        2. Analyze for completed tasks -> Update state & HA to-do list. Trigger notifications.
        3. Analyze for new tasks -> Update state & HA to-do list. Trigger notifications.
        4. Return the updated state for this zone.
        """
        pass

2.2 AICleaner Class
The main application controller. It manages the lifecycle of the addon, schedules zone analyses, and handles state persistence.

# aicleaner.py

class AICleaner:
    def __init__(self):
        """
        Initializes the main application controller.
        - Loads global configuration from /data/options.json.
        - Loads the persistent state from /data/state.json.
        - Initializes API clients (HA, Gemini).
        - Instantiates a Zone object for each configured zone, passing the relevant config slice and state slice.
        """
        self.config = self._load_config()
        self.state = self._load_persistent_state()
        self.ha_client = # ...
        self.gemini_client = # ...
        self.zones = [Zone(z_conf, self.state.get(z_conf['name'], {}), self.ha_client, self.gemini_client) for z_conf in self.config['zones']]


    def _load_config(self):
        """Loads and validates /data/options.json."""
        pass

    def _load_persistent_state(self):
        """
        Loads /data/state.json.
        If the file doesn't exist, returns an empty dict.
        Handles JSON decoding errors gracefully.
        """
        pass

    def _save_persistent_state(self):
        """
        Saves the current self.state to /data/state.json atomically.
        Writes to a temporary file first, then renames to prevent corruption on failure.
        """
        pass

    def run(self):
        """
        The main application loop.
        - Uses a scheduler (like 'schedule' library) to run the analysis for each zone.
        - Each zone is scheduled independently based on its 'update_frequency'.
        - After each zone's analysis_cycle, it receives the updated state and saves it.
        """
        pass

if __name__ == "__main__":
    cleaner = AICleaner()
    cleaner.run()

3. Configuration & State Management
State Persistence (/data/state.json)
This file is the addon's memory. Its integrity is critical.

Task Object Structure: Each task will be a dictionary with a stable ID.

{
  "id": "task_1687392000_kitchen_0", // Unix timestamp + zone + index
  "description": "Load the dirty dishes from the counter into the dishwasher.",
  "status": "active", // or "completed"
  "created_at": "2023-06-21T18:00:00Z",
  "completed_at": null
}

File Structure:

{
  "Kitchen": {
    "tasks": [ /* list of task objects */ ]
  },
  "Living Room": {
    "tasks": [ /* list of task objects */ ]
  }
}

Atomic Save Process: To prevent data loss if the addon crashes mid-write, the _save_persistent_state method must follow this pattern:

json.dump(self.state, 'state.json.tmp')

os.rename('state.json.tmp', 'state.json')

4. API Interaction & Logic
4.1 Stateful Task Analysis Flow - Detailed Prompts
Prompt 1: Checking for Completed Tasks
The goal is to get a structured, parseable response with minimal extra tokens.

System Prompt: You are a state verification assistant. Your job is to determine which of the provided tasks are completed by analyzing the image. Respond ONLY with a JSON array of the string IDs of the completed tasks.

User Prompt:

{
  "active_tasks": [
    {"id": "task_1", "description": "Return the cooking oil bottles from the counter into their cabinet."},
    {"id": "task_2", "description": "Load the dirty dishes and cups from the counter into the dishwasher."}
  ]
}

Based on the provided image, which tasks from the active_tasks list are now complete?

Prompt 2: Discovering New Tasks
This prompt provides more context to avoid creating duplicate or irrelevant tasks.

System Prompt: You are a home organization assistant. Your job is to identify cleaning or tidying tasks from an image and describe them as clear, actionable to-do items. Do not suggest tasks that are already listed as active. Adhere to all ignore rules. Respond ONLY with a JSON array of new task descriptions.

User Prompt:

{
  "context": "This is the Kitchen. The goal is to 'Keep everything Tidy and Clean'.",
  "active_tasks": [
    "A pot is soaking in the sink."
  ],
  "ignore_rules": [
    "Ignore the fruit bowl on the counter.",
    "The decorative vase on the shelf is supposed to be there."
  ]
}

Based on the provided image and the context above, what new tidying tasks need to be done?

4.2 Home Assistant API Services
camera.snapshot:

entity_id: self.camera_entity

filename: /tmp/{self.name}_latest.jpg

todo.add_item:

entity_id: self.todo_list_entity

item: (Task description from Gemini)

todo.update_item:

entity_id: self.todo_list_entity

item: (ID or full description of the task to update)

status: completed

notify.<service_name>:

message: (Formatted string from send_notification)

Sensors for UI: The addon will create and update sensors for the Lovelace card, e.g.:

sensor.aicleaner_kitchen_active_tasks

sensor.aicleaner_kitchen_completion_rate_30d