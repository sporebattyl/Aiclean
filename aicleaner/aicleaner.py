import os
import time
import json
import yaml
import requests
import tempfile
from datetime import datetime, timezone
from google.generativeai.client import configure
from google.generativeai.generative_models import GenerativeModel
import logging
from PIL import Image

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Zone:
    """
    Represents a single configured "Space" (e.g., Kitchen).
    Encapsulates all logic and state for one area.
    """

    def __init__(self, zone_config, state, ha_client, gemini_client):
        """
        Manages an individual zone.
        - zone_config (dict): The specific configuration for this zone from options.json.
        - state (dict): The persistent state for this zone (active/completed tasks).
        - ha_client: An initialized Home Assistant API client instance.
        - gemini_client: An initialized Gemini API client instance.
        """
        # Validate required parameters
        if not zone_config:
            raise ValueError("Zone configuration is required")
        if ha_client is None:
            raise ValueError("Home Assistant client is required")
        if gemini_client is None:
            raise ValueError("Gemini client is required")

        # Validate required configuration fields
        required_fields = ['name', 'camera_entity', 'todo_list_entity', 'update_frequency']
        for field in required_fields:
            if field not in zone_config or not zone_config[field]:
                raise ValueError(f"Missing required zone configuration field: '{field}'")

        # Validate update frequency
        if not isinstance(zone_config['update_frequency'], int) or zone_config['update_frequency'] < 1:
            raise ValueError("update_frequency must be an integer >= 1")

        # Validate notification personality
        valid_personalities = ['default', 'roaster', 'comedian', 'jarvis', 'sargent', 'snarky']
        personality = zone_config.get('notification_personality', 'default')
        if personality not in valid_personalities:
            raise ValueError(f"Invalid notification_personality: {personality}. Must be one of {valid_personalities}")

        # Set zone attributes
        self.name = zone_config['name']
        self.camera_entity = zone_config['camera_entity']
        self.todo_list_entity = zone_config['todo_list_entity']
        self.update_frequency = zone_config['update_frequency']
        self.icon = zone_config.get('icon', 'mdi:home')
        self.purpose = zone_config.get('purpose', 'Keep tidy and clean')

        # Notification settings
        self.notifications_enabled = zone_config.get('notifications_enabled', False)
        self.notification_service = zone_config.get('notification_service', '')
        self.notification_personality = personality
        self.notify_on_create = zone_config.get('notify_on_create', False)
        self.notify_on_complete = zone_config.get('notify_on_complete', False)

        # State and clients
        self.state = state if state is not None else {'tasks': []}
        self.ha_client = ha_client
        self.gemini_client = gemini_client

        logging.info(f"Initialized zone '{self.name}' with {len(self.state.get('tasks', []))} tasks")

    def get_camera_snapshot(self):
        """
        Calls the Home Assistant camera.snapshot service and saves the image to a temporary file.
        Returns the file path.
        """
        logging.info(f"Getting snapshot from camera {self.camera_entity} for zone {self.name}")

        try:
            filename = f"/tmp/{self.name}_latest.jpg"
            success = self.ha_client.get_camera_snapshot(self.camera_entity, filename)

            if success and os.path.exists(filename):
                logging.info(f"Successfully saved snapshot to {filename}")
                return filename
            else:
                logging.error(f"Failed to get camera snapshot for zone {self.name}")
                return None

        except Exception as e:
            logging.error(f"Error getting camera snapshot for zone {self.name}: {e}")
            return None

    def analyze_image_for_completed_tasks(self, image_path):
        """
        Analyzes an image against the current active_tasks list.
        - Constructs a specific prompt for Gemini asking to identify completed tasks.
        - Parses the response and returns a list of task IDs that are now complete.
        """
        if not image_path or not os.path.exists(image_path):
            logging.error(f"Invalid image path provided: {image_path}")
            return None

        # Get active tasks from state
        active_tasks = [task for task in self.state.get('tasks', []) if task.get('status') == 'active']

        if not active_tasks:
            logging.info(f"No active tasks to check for completion in zone {self.name}")
            return []

        logging.info(f"Analyzing image for completed tasks in zone {self.name}")

        try:
            img = Image.open(image_path)

            # Construct the prompt as specified in DesignDocument.md
            system_prompt = "You are a state verification assistant. Your job is to determine which of the provided tasks are completed by analyzing the image. Respond ONLY with a JSON array of the string IDs of the completed tasks."

            # Format active tasks for the prompt
            active_tasks_data = {
                "active_tasks": [
                    {"id": task["id"], "description": task["description"]}
                    for task in active_tasks
                ]
            }

            user_prompt = f"{json.dumps(active_tasks_data)}\n\nBased on the provided image, which tasks from the active_tasks list are now complete?"

            full_prompt = f"{system_prompt}\n\n{user_prompt}"

            response = self.gemini_client.generate_content([full_prompt, img])

            # Parse the response
            completed_task_ids = self._parse_gemini_json_response(response.text)

            if completed_task_ids is None:
                logging.error(f"Failed to parse Gemini response for completed tasks in zone {self.name}")
                return []

            logging.info(f"Found {len(completed_task_ids)} completed tasks in zone {self.name}")
            return completed_task_ids

        except Exception as e:
            logging.error(f"Error analyzing image for completed tasks in zone {self.name}: {e}")
            raise

    def analyze_image_for_new_tasks(self, image_path):
        """
        Analyzes an image to find new tasks.
        - Constructs a prompt for Gemini, providing context about existing tasks and ignore rules to prevent duplicates.
        - Returns a list of new task descriptions.
        """
        if not image_path or not os.path.exists(image_path):
            logging.error(f"Invalid image path provided: {image_path}")
            return None

        logging.info(f"Analyzing image for new tasks in zone {self.name}")

        try:
            img = Image.open(image_path)

            # Construct the prompt as specified in DesignDocument.md
            system_prompt = "You are a home organization assistant. Your job is to identify cleaning or tidying tasks from an image and describe them as clear, actionable to-do items. Do not suggest tasks that are already listed as active. Adhere to all ignore rules. Respond ONLY with a JSON array of new task descriptions."

            # Get context data
            context = f"This is the {self.name}. The goal is to '{self.purpose}'."
            active_task_descriptions = [task["description"] for task in self.state.get('tasks', []) if task.get('status') == 'active']
            ignore_rules = self.state.get('ignore_rules', [])

            # Format the context data
            context_data = {
                "context": context,
                "active_tasks": active_task_descriptions,
                "ignore_rules": ignore_rules
            }

            user_prompt = f"{json.dumps(context_data)}\n\nBased on the provided image and the context above, what new tidying tasks need to be done?"

            full_prompt = f"{system_prompt}\n\n{user_prompt}"

            response = self.gemini_client.generate_content([full_prompt, img])

            # Parse the response
            new_tasks = self._parse_gemini_json_response(response.text)

            if new_tasks is None:
                logging.error(f"Failed to parse Gemini response for new tasks in zone {self.name}")
                return []

            logging.info(f"Found {len(new_tasks)} new tasks in zone {self.name}")
            return new_tasks

        except Exception as e:
            logging.error(f"Error analyzing image for new tasks in zone {self.name}: {e}")
            raise

    def _parse_gemini_json_response(self, response_text):
        """
        Parses the JSON response from Gemini.
        """
        try:
            # Clean up the response text to remove markdown code block fences
            cleaned_text = response_text.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned_text)

            logging.info(f"Successfully parsed Gemini response")
            return data

        except Exception as e:
            logging.error(f"Error parsing Gemini JSON response: {e}")
            logging.error(f"Raw response was: {response_text}")
            return None

    def send_notification(self, message_type, context):
        """
        Constructs and sends a notification message via the configured HA service.
        - message_type (str): 'task_created' or 'task_completed'.
        - context (dict): Contains task details for message formatting.
        - Uses the configured 'personality' to format the final message string.
        """
        if not self.notifications_enabled:
            return

        if message_type == 'task_created' and not self.notify_on_create:
            return

        if message_type == 'task_completed' and not self.notify_on_complete:
            return

        if not self.notification_service:
            logging.warning(f"Notification service not configured for zone {self.name}")
            return

        try:
            # Format message based on personality
            message = self._format_notification_message(message_type, context)

            # Send notification via HA
            success = self.ha_client.send_notification(
                service=self.notification_service,
                message=message,
                title=f"AI Cleaner - {self.name}"
            )

            if success:
                logging.info(f"Sent {message_type} notification for zone {self.name}")
            else:
                logging.error(f"Failed to send {message_type} notification for zone {self.name}")

        except Exception as e:
            logging.error(f"Error sending notification for zone {self.name}: {e}")

    def _format_notification_message(self, message_type, context):
        """Format notification message based on personality"""
        task_desc = context.get('task_description', 'Unknown task')
        zone_name = context.get('zone_name', self.name)

        if message_type == 'task_created':
            base_message = f"New task in {zone_name}: {task_desc}"
        else:  # task_completed
            base_message = f"Task completed in {zone_name}: {task_desc}"

        # Apply personality formatting
        if self.notification_personality == 'snarky':
            if message_type == 'task_created':
                return f"Oh look, another mess in {zone_name}. Really? {task_desc}"
            else:
                return f"Finally! Someone actually cleaned up in {zone_name}. {task_desc} is done."

        elif self.notification_personality == 'jarvis':
            if message_type == 'task_created':
                return f"Sir, I've identified a task requiring attention in {zone_name}: {task_desc}"
            else:
                return f"Excellent work, sir. The task '{task_desc}' in {zone_name} has been completed."

        elif self.notification_personality == 'roaster':
            if message_type == 'task_created':
                return f"What a disaster in {zone_name}! This mess needs fixing: {task_desc}"
            else:
                return f"About time! The chaos in {zone_name} is slightly less chaotic. {task_desc} is done."

        elif self.notification_personality == 'comedian':
            if message_type == 'task_created':
                return f"Breaking news: {zone_name} has achieved new levels of messiness! Task: {task_desc}"
            else:
                return f"Plot twist: Someone actually cleaned in {zone_name}! {task_desc} is complete."

        elif self.notification_personality == 'sargent':
            if message_type == 'task_created':
                return f"ATTENTION! Mission identified in {zone_name}: {task_desc}. Move out!"
            else:
                return f"MISSION ACCOMPLISHED! Task '{task_desc}' in {zone_name} completed. Outstanding work!"

        else:  # default
            return base_message

    def run_analysis_cycle(self):
        """
        Orchestrates the full, stateful analysis loop for this single zone.
        1. Get camera snapshot.
        2. Analyze for completed tasks -> Update state & HA to-do list. Trigger notifications.
        3. Analyze for new tasks -> Update state & HA to-do list. Trigger notifications.
        4. Return the updated state for this zone.
        """
        logging.info(f"Starting analysis cycle for zone {self.name}")

        try:
            # Step 1: Get camera snapshot
            image_path = self.get_camera_snapshot()
            if not image_path:
                logging.error(f"Failed to get camera snapshot for zone {self.name}, aborting analysis cycle")
                return self.state

            # Step 2: Analyze for completed tasks
            try:
                completed_task_ids = self.analyze_image_for_completed_tasks(image_path)
                if completed_task_ids:
                    self._process_completed_tasks(completed_task_ids)
            except Exception as e:
                logging.error(f"Error processing completed tasks for zone {self.name}: {e}")

            # Step 3: Analyze for new tasks
            try:
                new_tasks = self.analyze_image_for_new_tasks(image_path)
                if new_tasks:
                    self._process_new_tasks(new_tasks)
            except Exception as e:
                logging.error(f"Error processing new tasks for zone {self.name}: {e}")

            # Cleanup
            if os.path.exists(image_path):
                os.remove(image_path)

            logging.info(f"Completed analysis cycle for zone {self.name}")
            return self.state

        except Exception as e:
            logging.error(f"Error in analysis cycle for zone {self.name}: {e}")
            return self.state

    def _process_completed_tasks(self, completed_task_ids):
        """Process completed tasks: update state, HA todo list, and send notifications"""
        for task_id in completed_task_ids:
            # Find the task in state
            task = None
            for t in self.state.get('tasks', []):
                if t.get('id') == task_id:
                    task = t
                    break

            if not task:
                logging.warning(f"Completed task ID {task_id} not found in state for zone {self.name}")
                continue

            # Update task status
            task['status'] = 'completed'
            task['completed_at'] = datetime.now(timezone.utc).isoformat()

            # Update HA todo list
            try:
                self.ha_client.update_todo_item(
                    entity_id=self.todo_list_entity,
                    item=task['description'],
                    status='completed'
                )
            except Exception as e:
                logging.error(f"Error updating HA todo item for completed task in zone {self.name}: {e}")

            # Send notification
            context = {
                'task_description': task['description'],
                'zone_name': self.name
            }
            self.send_notification('task_completed', context)

    def _process_new_tasks(self, new_task_descriptions):
        """Process new tasks: update state, HA todo list, and send notifications"""
        timestamp = int(datetime.now(timezone.utc).timestamp())

        for i, description in enumerate(new_task_descriptions):
            # Create task object
            task_id = f"task_{timestamp}_{self.name.lower().replace(' ', '_')}_{i}"
            task = {
                'id': task_id,
                'description': description,
                'status': 'active',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'completed_at': None
            }

            # Add to state
            if 'tasks' not in self.state:
                self.state['tasks'] = []
            self.state['tasks'].append(task)

            # Add to HA todo list
            try:
                self.ha_client.add_todo_item(
                    entity_id=self.todo_list_entity,
                    item=description
                )
            except Exception as e:
                logging.error(f"Error adding HA todo item for new task in zone {self.name}: {e}")

            # Send notification
            context = {
                'task_description': description,
                'zone_name': self.name
            }
            self.send_notification('task_created', context)


class HAClient:
    """Home Assistant API client for v2.0 architecture"""

    def __init__(self, api_url, token):
        self.api_url = api_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "content-type": "application/json",
        }

    def get_camera_snapshot(self, entity_id, filename):
        """Get camera snapshot and save to file"""
        try:
            snapshot_url = f"{self.api_url}/api/camera_proxy/{entity_id}"
            response = requests.get(snapshot_url, headers=self.headers, timeout=10)
            response.raise_for_status()

            with open(filename, 'wb') as f:
                f.write(response.content)
            return True
        except Exception as e:
            logging.error(f"Error getting camera snapshot: {e}")
            return False

    def add_todo_item(self, entity_id, item):
        """Add item to todo list"""
        try:
            url = f"{self.api_url}/api/services/todo/add_item"
            payload = {"entity_id": entity_id, "item": item}
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            logging.error(f"Error adding todo item: {e}")
            return False

    def update_todo_item(self, entity_id, item, status):
        """Update todo item status"""
        try:
            url = f"{self.api_url}/api/services/todo/update_item"
            payload = {"entity_id": entity_id, "item": item, "status": status}
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            logging.error(f"Error updating todo item: {e}")
            return False

    def update_sensor(self, entity_id, state, attributes=None):
        """Update sensor state"""
        try:
            url = f"{self.api_url}/api/states/{entity_id}"
            payload = {"state": state, "attributes": attributes or {}}
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            logging.error(f"Error updating sensor: {e}")
            return False

    def send_notification(self, service, message, title=None):
        """Send notification via Home Assistant"""
        try:
            url = f"{self.api_url}/api/services/notify/{service.replace('notify.', '')}"
            payload = {"message": message}
            if title:
                payload["title"] = title
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            logging.error(f"Error sending notification: {e}")
            return False


class AICleaner:
    """
    Main controller class for the v2.0 multi-zone AI Cleaning Assistant.
    Manages multiple Zone instances, coordinates analysis cycles, and handles persistent state.
    """

    def __init__(self):
        """
        Initializes the AICleaner v2.0 application with multi-zone support.
        """
        logging.info("Initializing AICleaner v2.0 with multi-zone support")

        # Load and validate configuration
        self.config = self._load_config()
        self._validate_config()

        # Initialize API clients
        self.ha_client = self._create_ha_client()
        self.gemini_client = self._create_gemini_client()

        # Load persistent state
        self.state = self._load_persistent_state()

        # Initialize zones
        self.zones = self._create_zones()

        # Track last analysis times for scheduling
        self.last_analysis_times = {}

        logging.info(f"Initialized AICleaner with {len(self.zones)} zones")


    def _load_config(self):
        """
        Loads configuration from environment variables (for HA Add-on)
        or from a YAML file (for local development).
        """
        # SUPERVISOR_TOKEN is a reliable indicator of the HA Add-on environment
        if 'SUPERVISOR_TOKEN' in os.environ:
            logging.info("Loading configuration from Home Assistant addon environment")
            return self._load_from_addon_env()
        else:
            logging.info("Loading configuration from local development environment")
            return self._load_from_local_env()

    def _load_from_addon_env(self):
        """Loads configuration from Home Assistant addon environment"""
        # In addon environment, configuration comes from /data/options.json
        options_path = '/data/options.json'
        if not os.path.exists(options_path):
            raise FileNotFoundError(f"Addon options file not found: {options_path}")

        with open(options_path, 'r') as f:
            options = json.load(f)

        supervisor_token = os.environ.get('SUPERVISOR_TOKEN')
        if not supervisor_token:
            raise ValueError("SUPERVISOR_TOKEN environment variable not found")

        return {
            'gemini_api_key': options.get('gemini_api_key'),
            'display_name': options.get('display_name', 'User'),
            'zones': options.get('zones', []),
            'ha_api_url': 'http://supervisor/core/api',
            'ha_token': supervisor_token
        }

    def _load_from_local_env(self):
        """Loads configuration from local development environment"""
        config_path = 'aicleaner/config.yaml'
        if not os.path.exists(config_path):
            config_path = 'config.yaml'  # Fallback

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Transform local config to v2.0 format if needed
        if 'google_gemini' in config:
            # Old format - transform to new format
            transformed_config = {
                'gemini_api_key': config['google_gemini']['api_key'],
                'display_name': config.get('display_name', 'User'),
                'zones': config.get('zones', []),
                'ha_api_url': config.get('home_assistant', {}).get('api_url', 'http://localhost:8123/api'),
                'ha_token': config.get('home_assistant', {}).get('token', '')
            }
            return transformed_config
        else:
            # New format - add HA API details
            config['ha_api_url'] = config.get('home_assistant', {}).get('api_url', 'http://localhost:8123/api')
            config['ha_token'] = config.get('home_assistant', {}).get('token', '')
            return config

    def _validate_config(self):
        """Validates the loaded configuration for v2.0 requirements"""
        logging.info("Validating v2.0 configuration")

        # Check required top-level keys
        if 'gemini_api_key' not in self.config or not self.config['gemini_api_key']:
            raise ValueError("Missing required configuration: 'gemini_api_key'")

        if 'zones' not in self.config:
            raise ValueError("Missing required configuration: 'zones'")

        # Validate each zone configuration
        for i, zone_config in enumerate(self.config['zones']):
            self._validate_zone_config(zone_config, i)

        logging.info(f"Configuration validated successfully with {len(self.config['zones'])} zones")

    def _validate_zone_config(self, zone_config, index):
        """Validates a single zone configuration"""
        required_fields = ['name', 'camera_entity', 'todo_list_entity', 'update_frequency']

        for field in required_fields:
            if field not in zone_config or not zone_config[field]:
                raise ValueError(f"Zone {index}: Missing required field '{field}'")

        # Validate update frequency
        if not isinstance(zone_config['update_frequency'], int) or zone_config['update_frequency'] < 1:
            raise ValueError(f"Zone {index}: update_frequency must be an integer >= 1")

        # Validate notification personality if specified
        if 'notification_personality' in zone_config:
            valid_personalities = ['default', 'roaster', 'comedian', 'jarvis', 'sargent', 'snarky']
            if zone_config['notification_personality'] not in valid_personalities:
                raise ValueError(f"Zone {index}: Invalid notification_personality")

    def _create_ha_client(self):
        """Creates Home Assistant API client"""
        api_url = self.config.get('ha_api_url')
        token = self.config.get('ha_token')

        if not api_url or not token:
            raise ValueError("Missing Home Assistant API configuration")

        return HAClient(api_url, token)

    def _create_gemini_client(self):
        """Creates Gemini API client"""
        api_key = self.config['gemini_api_key']
        configure(api_key=api_key)
        return GenerativeModel('gemini-1.5-pro')

    def _load_persistent_state(self):
        """Loads persistent state from /data/state.json"""
        state_path = '/data/state.json'

        if not os.path.exists(state_path):
            logging.info("No existing state file found, starting with empty state")
            return {}

        try:
            with open(state_path, 'r') as f:
                state = json.load(f)
            logging.info(f"Loaded persistent state with {len(state)} zones")
            return state
        except Exception as e:
            logging.error(f"Error loading persistent state: {e}")
            return {}

    def _save_persistent_state(self):
        """Saves persistent state to /data/state.json using atomic operation"""
        state_path = '/data/state.json'
        temp_path = state_path + '.tmp'

        try:
            # Write to temporary file first
            with open(temp_path, 'w') as f:
                json.dump(self.state, f, indent=2)

            # Atomic rename
            os.rename(temp_path, state_path)
            logging.debug("Persistent state saved successfully")
        except Exception as e:
            logging.error(f"Error saving persistent state: {e}")
            # Clean up temp file if it exists
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise

    def _create_zones(self):
        """Creates Zone instances from configuration"""
        zones = []

        for zone_config in self.config['zones']:
            zone_name = zone_config['name']

            # Get or create zone state
            if zone_name not in self.state:
                self.state[zone_name] = {'tasks': []}

            zone_state = self.state[zone_name]

            # Create zone instance
            zone = Zone(zone_config, zone_state, self.ha_client, self.gemini_client)
            zones.append(zone)

            logging.info(f"Created zone '{zone_name}' with {len(zone_state.get('tasks', []))} tasks")

        return zones

    def get_zone_by_name(self, name):
        """Gets a zone by name"""
        for zone in self.zones:
            if zone.name == name:
                return zone
        return None

    def update_zone_state(self, zone_name, new_state):
        """Updates state for a specific zone"""
        zone = self.get_zone_by_name(zone_name)
        if zone:
            zone.state = new_state
            self.state[zone_name] = new_state
            self._save_persistent_state()

    def get_zones_due_for_analysis(self):
        """Gets zones that are due for analysis based on their schedules"""
        current_time = time.time()
        due_zones = []

        for zone in self.zones:
            last_analysis = self.last_analysis_times.get(zone.name, 0)  # 0 means never analyzed
            frequency_seconds = zone.update_frequency * 3600  # Convert hours to seconds

            # If never analyzed (last_analysis == 0) or enough time has passed
            if last_analysis == 0 or (current_time - last_analysis >= frequency_seconds):
                due_zones.append(zone)

        return due_zones

    def run_single_cycle(self):
        """Runs a single analysis cycle for all zones"""
        logging.info("Starting single analysis cycle for all zones")

        for zone in self.zones:
            try:
                logging.info(f"Running analysis cycle for zone '{zone.name}'")
                updated_state = zone.run_analysis_cycle()

                # Update persistent state
                self.state[zone.name] = updated_state

                # Update last analysis time
                self.last_analysis_times[zone.name] = time.time()

            except Exception as e:
                logging.error(f"Error in analysis cycle for zone '{zone.name}': {e}")

        # Save persistent state after all zones
        try:
            self._save_persistent_state()
        except Exception as e:
            logging.error(f"Error saving persistent state: {e}")

        logging.info("Completed single analysis cycle for all zones")

    def run_scheduled_analysis(self):
        """Runs analysis for zones that are due based on their schedules"""
        due_zones = self.get_zones_due_for_analysis()

        if not due_zones:
            logging.debug("No zones due for analysis")
            return

        logging.info(f"Running scheduled analysis for {len(due_zones)} zones")

        for zone in due_zones:
            try:
                logging.info(f"Running scheduled analysis for zone '{zone.name}'")
                updated_state = zone.run_analysis_cycle()

                # Update persistent state
                self.state[zone.name] = updated_state

                # Update last analysis time
                self.last_analysis_times[zone.name] = time.time()

            except Exception as e:
                logging.error(f"Error in scheduled analysis for zone '{zone.name}': {e}")

        # Save persistent state after all zones
        try:
            self._save_persistent_state()
        except Exception as e:
            logging.error(f"Error saving persistent state: {e}")

    def run(self):
        """Main application loop - runs scheduled analysis continuously"""
        logging.info("Starting AICleaner v2.0 main application loop")

        try:
            while True:
                self.run_scheduled_analysis()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logging.info("Application stopped by user")
        except Exception as e:
            logging.error(f"Error in main application loop: {e}")
            raise




if __name__ == "__main__":
    try:
        logging.info("Initializing AICleaner v2.0 application")
        cleaner = AICleaner()
        cleaner.run()
    except Exception as e:
        logging.critical(f"AICleaner v2.0 application failed to initialize or run: {e}")