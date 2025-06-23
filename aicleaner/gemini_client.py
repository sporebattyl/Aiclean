import os
import yaml
import google.generativeai as genai
import logging

class GeminiClient:
    """
    A client for interacting with the Google Gemini API.
    """
    def __init__(self, api_key):
        """
        Initializes the Gemini client.
        """
        if not api_key:
            raise ValueError("Google Gemini API key is required.")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro-vision')

    def analyze_image(self, image_path):
        """
        Submits an image to the Gemini Vision API for analysis.
        Returns a dictionary containing the 'score' and 'tasks'.
        """
        if not image_path or not os.path.exists(image_path):
            logging.error(f"Invalid image path provided: {image_path}")
            return None

        logging.info(f"Analyzing image with Gemini: {image_path}")
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
            response = self.model.generate_content([prompt, image_file])
            return self._parse_response(response.text)
            
        except Exception as e:
            logging.error(f"Error analyzing image with Gemini: {e}")
            return None

    def _parse_response(self, response_text):
        """
        Parses the JSON response from Gemini.
        """
        try:
            cleaned_text = response_text.strip().replace("```json", "").replace("```", "").strip()
            data = yaml.safe_load(cleaned_text)
            
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