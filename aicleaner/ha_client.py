import requests
import logging

class HomeAssistantClient:
    """
    A client for interacting with the Home Assistant API.
    """
    def __init__(self, api_url, token):
        """
        Initializes the Home Assistant client.
        """
        if not api_url or not token:
            raise ValueError("Home Assistant API URL and token are required.")
        
        self.api_url = api_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "content-type": "application/json",
        }

    def get_camera_snapshot(self, camera_entity_id, snapshot_path="snapshot.jpg"):
        """
        Connects to the specified Home Assistant camera entity and saves a snapshot.
        Returns the path to the saved snapshot file, or None on failure.
        """
        logging.info(f"Getting snapshot from {camera_entity_id}")
        snapshot_url = f"{self.api_url}/api/camera_proxy/{camera_entity_id}"

        try:
            response = requests.get(snapshot_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            with open(snapshot_path, 'wb') as f:
                f.write(response.content)
            
            logging.info(f"Successfully saved snapshot to {snapshot_path}")
            return snapshot_path
        except requests.exceptions.RequestException as e:
            logging.error(f"Error getting camera snapshot: {e}")
            return None

    def update_sensor(self, sensor_entity_id, score, friendly_name="Room Cleanliness Score"):
        """
        Creates or updates a Home Assistant sensor with a new score.
        """
        logging.info(f"Updating sensor {sensor_entity_id} with score: {score}")
        url = f"{self.api_url}/api/states/{sensor_entity_id}"
        payload = {
            "state": score,
            "attributes": {
                "unit_of_measurement": "%",
                "friendly_name": friendly_name
            }
        }
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            logging.info(f"Successfully updated sensor {sensor_entity_id}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error updating Home Assistant sensor: {e}")

    def add_task_to_todolist(self, todolist_entity_id, task):
        """
        Adds a single task to the specified Home Assistant to-do list.
        """
        logging.info(f"Adding task to {todolist_entity_id}: '{task}'")
        url = f"{self.api_url}/api/services/todo/add_item"
        payload = {
            "entity_id": todolist_entity_id,
            "item": task
        }
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            logging.info(f"Successfully added task: '{task}'")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error adding task '{task}' to Home Assistant to-do list: {e}")