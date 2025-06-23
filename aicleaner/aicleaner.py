import os
import time
import yaml
import logging
from .ha_client import HomeAssistantClient
from .gemini_client import GeminiClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AICleaner:
    def __init__(self):
        """
        Initializes the AICleaner application.
        """
        self.config = self._load_config()
        self._validate_config()
        # Home Assistant Client
        self.ha_client = HomeAssistantClient(
            api_url=self.config['home_assistant']['api_url'],
            token=self.config['home_assistant']['token']
        )
        self.camera_entity_id = self.config['home_assistant']['camera_entity_id']
        self.todolist_entity_id = self.config['home_assistant']['todolist_entity_id']
        self.sensor_entity_id = self.config['home_assistant']['sensor_entity_id']
        
        # Gemini Client
        self.gemini_client = GeminiClient(
            api_key=self.config['google_gemini']['api_key']
        )

        # Application Configuration
        self.analysis_interval = self.config['application']['analysis_interval_minutes'] * 60

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
        supervisor_api = os.environ.get('SUPERVISOR_API')
        if not supervisor_api:
            raise ValueError("SUPERVISOR_API environment variable not found. Cannot determine Home Assistant URL.")

        return {
            "home_assistant": {
                "api_url": supervisor_api.replace("/api",""), # Get base URL
                "token": os.environ.get('SUPERVISOR_TOKEN'),
                "camera_entity_id": os.environ.get('CAMERA_ENTITY'),
                "todolist_entity_id": os.environ.get('TODO_LIST'),
                "sensor_entity_id": os.environ.get('SENSOR_ENTITY'),
            },
            "google_gemini": {
                "api_key": os.environ.get('API_KEY'),
            },
            "application": {
                # Update frequency from run.sh is in hours, convert to minutes
                "analysis_interval_minutes": int(os.environ.get('FREQUENCY', 24))
            }
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
        Validates the loaded configuration to ensure all required keys are present.
        Raises ValueError if a required key is missing.
        """
        logging.info("Validating configuration.")
        required_ha_keys = [
            "api_url", "token", "camera_entity_id",
            "todolist_entity_id", "sensor_entity_id"
        ]
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

# This space is intentionally left blank.

    def run(self):
        """
        The main application loop.
        """
        logging.info("Starting AICleaner main loop.")
        while True:
            logging.info("Starting new analysis cycle.")
            # 1. Get camera snapshot
            image_path = self.ha_client.get_camera_snapshot(self.camera_entity_id)

            if image_path:
                # 2. Analyze with Gemini
                analysis = self.gemini_client.analyze_image(image_path)
                
                if analysis:
                    score = analysis.get("score")
                    tasks = analysis.get("tasks")

                    # 3. Update Home Assistant
                    if score is not None:
                        self.ha_client.update_sensor(self.sensor_entity_id, score)
                    if tasks:
                        for task in tasks:
                            self.ha_client.add_task_to_todolist(self.todolist_entity_id, task)
                
                # Clean up the snapshot file
                os.remove(image_path)
            
            logging.info(f"Sleeping for {self.analysis_interval / 60} minutes.")
            time.sleep(self.analysis_interval)


if __name__ == "__main__":
    try:
        logging.info("Initializing AICleaner application.")
        cleaner = AICleaner()
        cleaner.run()
    except Exception as e:
        logging.critical(f"Application failed to initialize or run: {e}")