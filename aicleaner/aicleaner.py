import os
import time
import yaml
import requests
import google.generativeai as genai
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AICleaner:
    def __init__(self):
        """
        Initializes the AICleaner application.
        """
        self.config = self._load_config()
        self._validate_config()
        # Home Assistant Configuration
        self.ha_url = self.config['home_assistant']['api_url']
        # In the add-on environment, the token is the SUPERVISOR_TOKEN
        self.ha_token = self.config['home_assistant']['token']
        self.ha_headers = {
            "Authorization": f"Bearer {self.ha_token}",
            "content-type": "application/json",
        }
        self.camera_entity_id = self.config['home_assistant']['camera_entity_id']
        self.sensor_entity_id = self.config['home_assistant']['sensor_entity_id']
        # Handle the todolist entity, defaulting if not provided.
        self.todolist_entity_id = self._handle_todolist()
        
        # Gemini Configuration
        gemini_api_key = self.config['google_gemini']['api_key']
        if not gemini_api_key:
            raise ValueError("Google Gemini API key is not configured.")
        genai.configure(api_key=gemini_api_key)
        self.gemini_model = genai.GenerativeModel('gemini-pro-vision')


    def _load_config(self):
        """
        Loads configuration from environment variables (for HA Add-on)
        or from a YAML file (for local development).
        """
        # SUPERVISOR_TOKEN is a reliable indicator of the HA Add-on environment
        if 'SUPERVISOR_TOKEN' in os.environ:
            logging.info("Loading configuration from Home Assistant environment variables.")
            return self._load_from_env()
        else:
            logging.info("Loading configuration from local YAML file.")
            return self._load_from_yaml('aicleaner/config.yaml')

    def _load_from_env(self):
        """Loads configuration from environment variables."""
        # The supervisor hostname provides a reliable way to construct the API URL.
        # The base URL for Home Assistant's API is http://supervisor/core
        ha_api_url = "http://supervisor/core"
        
        supervisor_token = os.environ.get('SUPERVISOR_TOKEN')
        if not supervisor_token:
            # This is a critical failure, as we can't authenticate.
            raise ValueError("SUPERVISOR_TOKEN environment variable not found. Cannot authenticate with Home Assistant.")

        return {
            "home_assistant": {
                "api_url": ha_api_url,
                "token": supervisor_token,
                "camera_entity_id": os.environ.get('CAMERA_ENTITY'),
                "todolist_entity_id": os.environ.get('TODO_LIST'),
                "sensor_entity_id": os.environ.get('SENSOR_ENTITY'),
            },
            "google_gemini": {
                "api_key": os.environ.get('API_KEY'),
            },
        }

    def _load_from_yaml(self, config_path):
        """Loads the configuration from a YAML file."""
        logging.info(f"Loading YAML configuration from {config_path}")
        if not os.path.exists(config_path):
             # Fallback for running from root directory
            config_path = 'config.yaml'
        
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _validate_config(self):
        """
        Validates the loaded configuration to ensure critical keys are present.
        Raises ValueError if a required key is missing.
        """
        logging.info("Validating configuration.")
        # Only camera and api_key are strictly required for the script to function.
        # The others have defaults or are handled gracefully.
        required_ha_keys = ["api_url", "token", "camera_entity_id"]
        required_gemini_keys = ["api_key"]
        
        if "home_assistant" not in self.config:
            raise ValueError("Missing 'home_assistant' configuration block.")
        
        for key in required_ha_keys:
            if key not in self.config["home_assistant"] or not self.config["home_assistant"][key]:
                raise ValueError(f"Missing required Home Assistant configuration key: '{key}'")

        if "google_gemini" not in self.config:
            raise ValueError("Missing 'google_gemini' configuration block.")
            
        for key in required_gemini_keys:
            if key not in self.config["google_gemini"] or not self.config["google_gemini"][key]:
                raise ValueError(f"Missing required Google Gemini configuration key: '{key}'")
        
        logging.info("Configuration validation successful.")

    def _handle_todolist(self):
        """
        Returns the configured to-do list entity ID or a default.
        """
        configured_list = self.config['home_assistant'].get('todolist_entity_id')
        if configured_list:
            logging.info(f"Using user-configured to-do list: {configured_list}")
            return configured_list
        else:
            default_list = "todo.ai_cleaner_tasks"
            logging.info(f"No to-do list configured. Defaulting to '{default_list}'.")
            logging.warning(f"Please ensure the to-do list '{default_list}' exists in Home Assistant.")
            return default_list

    def get_camera_snapshot(self):
        """
        Connects to the specified Home Assistant camera entity and saves a snapshot.
        Returns the path to the saved snapshot file, or None on failure.
        """
        logging.info(f"Getting snapshot from {self.camera_entity_id}")
        snapshot_url = f"{self.ha_url}/api/camera_proxy/{self.camera_entity_id}"
        snapshot_path = "snapshot.jpg"

        try:
            response = requests.get(snapshot_url, headers=self.ha_headers, timeout=10)
            response.raise_for_status()  # Raise an exception for bad status codes
            
            with open(snapshot_path, 'wb') as f:
                f.write(response.content)
            
            logging.info(f"Successfully saved snapshot to {snapshot_path}")
            return snapshot_path
        except requests.exceptions.RequestException as e:
            logging.error(f"Error getting camera snapshot: {e}")
            return None

    def analyze_image_with_gemini(self, image_path):
        """
        Submits the image snapshot to the Google Gemini Vision API.
        Returns a dictionary containing the 'score' and 'tasks'.
        """
        if not image_path or not os.path.exists(image_path):
            logging.error(f"Invalid image path provided: {image_path}")
            return None

        logging.info(f"Analyzing image: {image_path}")
        try:
            image_file = genai.upload_file(path=image_path)
            prompt = """
            Analyze the provided image of a room and perform the following tasks:
            1.  Rate the overall cleanliness of the room on a scale of 1 to 100, where 1 is extremely messy and 100 is perfectly clean.
            2.  Identify specific, actionable tasks that would improve the room's cleanliness. The tasks should be clear and concise.

            Return the output ONLY in a valid JSON format with two keys:
            - "score": An integer representing the cleanliness score.
            - "tasks": A list of strings, where each string is a cleaning task.

            Example:
            {
              "score": 75,
              "tasks": [
                "Pick up the clothes from the floor.",
                "Make the bed.",
                "Wipe down the dusty shelves."
              ]
            }
            """
            response = self.gemini_model.generate_content([prompt, image_file])
            return self._parse_gemini_response(response.text)
            
        except Exception as e:
            logging.error(f"Error analyzing image with Gemini: {e}")
            return None

    def _parse_gemini_response(self, response_text):
        """
        Parses the JSON response from Gemini.
        """
        try:
            # Clean up the response text to remove markdown code block fences
            cleaned_text = response_text.strip().replace("```json", "").replace("```", "").strip()
            data = yaml.safe_load(cleaned_text) # Use yaml loader for more robust JSON parsing
            
            # Basic validation
            if "score" in data and "tasks" in data:
                logging.info(f"Successfully parsed Gemini response. Score: {data['score']}")
                return data
            else:
                logging.error("Gemini response missing 'score' or 'tasks' key.")
                return None
        except Exception as e:
            logging.error(f"Error parsing Gemini JSON response: {e}")
            logging.error(f"Raw response was: {response_text}")
            return None

    def update_ha_sensor(self, score):
        """
        Creates or updates the Home Assistant sensor with the new cleanliness score.
        """
        if score is None:
            logging.warning("No score provided to update HA sensor.")
            return

        logging.info(f"Updating sensor {self.sensor_entity_id} with score: {score}")
        url = f"{self.ha_url}/api/states/{self.sensor_entity_id}"
        payload = {
            "state": score,
            "attributes": {
                "unit_of_measurement": "%",
                "friendly_name": "Room Cleanliness Score"
            }
        }
        try:
            response = requests.post(url, headers=self.ha_headers, json=payload, timeout=10)
            response.raise_for_status()
            logging.info(f"Successfully updated sensor {self.sensor_entity_id}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error updating Home Assistant sensor: {e}")

    def update_ha_todolist(self, tasks):
        """
        Populates the specified Home Assistant to-do list with tasks from Gemini.
        """
        if not tasks or not self.todolist_entity_id:
            logging.info("No tasks to add or to-do list entity is not configured.")
            return

        logging.info(f"Updating todolist {self.todolist_entity_id} with {len(tasks)} tasks.")
        url = f"{self.ha_url}/api/services/todo/add_item"
        
        for task in tasks:
            payload = {
                "entity_id": self.todolist_entity_id,
                "item": task
            }
            try:
                response = requests.post(url, headers=self.ha_headers, json=payload, timeout=10)
                response.raise_for_status()
                logging.info(f"Successfully added task: '{task}'")
            except requests.exceptions.RequestException as e:
                logging.error(f"Error adding task '{task}' to Home Assistant to-do list: {e}")

    def run(self):
        """
        Runs a single analysis cycle.
        """
        logging.info("Starting new analysis cycle.")
        # 1. Get camera snapshot
        image_path = self.get_camera_snapshot()

        if image_path:
            # 2. Analyze with Gemini
            analysis = self.analyze_image_with_gemini(image_path)
            
            if analysis:
                score = analysis.get("score")
                tasks = analysis.get("tasks")

                # 3. Update Home Assistant
                if score is not None:
                    self.update_ha_sensor(score)
                if tasks:
                    self.update_ha_todolist(tasks)
            
            # Clean up the snapshot file
            os.remove(image_path)
        
        logging.info("Analysis cycle complete.")


if __name__ == "__main__":
    try:
        logging.info("Initializing AICleaner application.")
        cleaner = AICleaner()
        cleaner.run()
    except Exception as e:
        logging.critical(f"Application failed to initialize or run: {e}")