import os
import time
import json
import yaml
import requests
import tempfile
import traceback
from datetime import datetime, timezone, timedelta
from google.generativeai.client import configure
from google.generativeai.generative_models import GenerativeModel
import logging
from PIL import Image

# Import notification system components
try:
    from .notification_engine import NotificationEngine
    from .ignore_rules_manager import IgnoreRulesManager
    from .configuration_manager import ConfigurationManager
except ImportError:
    # Fallback for development/testing
    import sys
    sys.path.append(os.path.dirname(__file__))
    from notification_engine import NotificationEngine
    from ignore_rules_manager import IgnoreRulesManager
    from configuration_manager import ConfigurationManager

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
        valid_personalities = ['default', 'snarky', 'jarvis', 'roaster', 'butler', 'coach', 'zen']
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

        # Initialize component-based notification engine
        notification_config = {
            'notification_personality': personality,
            'webhook_url': zone_config.get('webhook_url'),
            'ha_service': self.notification_service,
            'timeout': zone_config.get('notification_timeout', 10),
            'retry_count': zone_config.get('notification_retry_count', 3)
        }
        self.notification_engine = NotificationEngine(notification_config)

        # Initialize component-based ignore rules manager
        self.ignore_rules_manager = IgnoreRulesManager(self.name)

        # Load existing ignore rules
        self.ignore_rules_manager.load_rules()

        # State and clients
        self.state = state if state is not None else {'tasks': []}
        self.ha_client = ha_client
        self.gemini_client = gemini_client

        # Track last analysis time for UI display
        self.last_analysis_time = None

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
            ignore_rules = [rule['text'] for rule in self.get_ignore_rules()]

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
        Send notification using component-based notification engine.
        - message_type (str): 'task_created', 'task_completed', or 'analysis_complete'.
        - context (dict): Contains task/analysis details for message formatting.
        - Uses the component-based NotificationEngine with personality formatting.
        """
        if not self.notifications_enabled:
            return

        if message_type == 'task_created' and not self.notify_on_create:
            return

        if message_type == 'task_completed' and not self.notify_on_complete:
            return

        try:
            if message_type == 'task_created':
                task_data = {
                    'zone': self.name,
                    'description': context.get('task_description', 'Unknown task'),
                    'priority': context.get('priority', 'normal')
                }
                success = self.notification_engine.send_task_notification(task_data)
            elif message_type == 'task_completed':
                task_data = {
                    'zone': self.name,
                    'description': context.get('task_description', 'Unknown task'),
                    'completion_method': context.get('completion_method', 'manual')
                }
                # Use task notification for completion (template will handle it)
                success = self.notification_engine.send_task_notification(task_data)
            elif message_type == 'analysis_complete':
                analysis_data = {
                    'zone': self.name,
                    'tasks_found': context.get('tasks_found', 0),
                    'tasks_completed': context.get('tasks_completed', 0),
                    'completion_rate': context.get('completion_rate', 0)
                }
                success = self.notification_engine.send_analysis_complete_notification(analysis_data)
            else:
                logging.warning(f"Unknown notification message type: {message_type}")
                return

            if success:
                logging.info(f"Notification sent successfully for zone {self.name}: {message_type}")
            else:
                logging.error(f"Failed to send notification for zone {self.name}: {message_type}")

        except Exception as e:
            logging.error(f"Error sending notification for zone {self.name}: {e}")

    # Old _format_notification_message method removed - now using component-based NotificationEngine

    def add_ignore_rule(self, rule_text: str) -> bool:
        """
        Add an ignore rule for this zone.

        Args:
            rule_text: Text of the rule to add

        Returns:
            bool: True if rule was added successfully, False otherwise
        """
        try:
            result = self.ignore_rules_manager.add_rule(rule_text)
            if result:
                logging.info(f"Added ignore rule for zone {self.name}: {rule_text}")
            return result
        except Exception as e:
            logging.error(f"Error adding ignore rule for zone {self.name}: {e}")
            return False

    def remove_ignore_rule(self, rule_id: str) -> bool:
        """
        Remove an ignore rule by ID.

        Args:
            rule_id: ID of the rule to remove

        Returns:
            bool: True if rule was removed successfully, False otherwise
        """
        try:
            result = self.ignore_rules_manager.remove_rule(rule_id)
            if result:
                logging.info(f"Removed ignore rule for zone {self.name}: {rule_id}")
            return result
        except Exception as e:
            logging.error(f"Error removing ignore rule for zone {self.name}: {e}")
            return False

    def get_ignore_rules(self) -> list:
        """
        Get all ignore rules for this zone.

        Returns:
            list: List of ignore rule dictionaries
        """
        try:
            return self.ignore_rules_manager.get_rules()
        except Exception as e:
            logging.error(f"Error getting ignore rules for zone {self.name}: {e}")
            return []

    def should_ignore_task(self, task_description: str) -> bool:
        """
        Check if a task should be ignored based on ignore rules.

        Args:
            task_description: Description of the task to check

        Returns:
            bool: True if task should be ignored, False otherwise
        """
        try:
            return self.ignore_rules_manager.should_ignore_task(task_description)
        except Exception as e:
            logging.error(f"Error checking ignore rules for zone {self.name}: {e}")
            return False

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

            # Step 2: Enhanced Analyze for completed tasks with retry logic and confidence scoring
            try:
                # Use advanced AI analysis with retry logic
                completed_task_ids = self.analyze_with_retry_logic(image_path, max_retries=3)

                # If basic retry fails, try confidence scoring approach
                if not completed_task_ids:
                    confidence_result = self.analyze_with_confidence_scoring(image_path)
                    if confidence_result and confidence_result.get('completed_tasks'):
                        # Filter by confidence threshold (e.g., 0.7)
                        confidence_scores = confidence_result.get('confidence_scores', {})
                        completed_task_ids = [
                            task_id for task_id in confidence_result['completed_tasks']
                            if confidence_scores.get(task_id, 0) >= 0.7
                        ]
                        logging.info(f"Using confidence-based completion detection with {len(completed_task_ids)} high-confidence tasks")

                if completed_task_ids:
                    self._process_completed_tasks(completed_task_ids)
            except Exception as e:
                logging.error(f"Error processing completed tasks for zone {self.name}: {e}")

            # Step 3: Enhanced Analyze for new tasks with context awareness
            try:
                # Use context-aware task generation for better results
                enhanced_new_tasks = self.generate_context_aware_tasks(image_path)

                # If enhanced generation fails, fall back to basic analysis
                if not enhanced_new_tasks:
                    new_tasks = self.analyze_image_for_new_tasks(image_path)
                    if new_tasks:
                        # Convert to enhanced format
                        enhanced_new_tasks = []
                        for task_desc in new_tasks:
                            priority = self.calculate_task_priority(task_desc)
                            enhanced_new_tasks.append({
                                'description': task_desc,
                                'priority': priority,
                                'context_aware': False,
                                'generated_at': datetime.now(timezone.utc).isoformat()
                            })

                if enhanced_new_tasks:
                    # Process enhanced tasks
                    self._process_enhanced_new_tasks(enhanced_new_tasks)
            except Exception as e:
                logging.error(f"Error processing new tasks for zone {self.name}: {e}")

            # Update Home Assistant sensor
            try:
                self.update_ha_sensor()
            except Exception as e:
                logging.error(f"Error updating HA sensor for zone {self.name}: {e}")

            # Update last analysis time for UI display
            self.last_analysis_time = datetime.now(timezone.utc)

            # Cleanup
            if os.path.exists(image_path):
                os.remove(image_path)

            logging.info(f"Completed analysis cycle for zone {self.name}")
            return self.state

        except Exception as e:
            logging.error(f"Error in analysis cycle for zone {self.name}: {e}")
            return self.state

    # Phase 2: Enhanced State Management Methods

    def validate_task_schema(self, task):
        """
        Validates a task against the required schema
        """
        required_fields = ['id', 'description', 'status', 'created_at']
        valid_statuses = ['active', 'completed', 'expired', 'dismissed']

        # Check required fields
        for field in required_fields:
            if field not in task:
                logging.warning(f"Task missing required field '{field}': {task}")
                return False

        # Validate status
        if task['status'] not in valid_statuses:
            logging.warning(f"Task has invalid status '{task['status']}': {task}")
            return False

        # Validate data types
        if not isinstance(task['description'], str) or not task['description'].strip():
            logging.warning(f"Task description must be non-empty string: {task}")
            return False

        # Validate priority if present
        if 'priority' in task:
            if not isinstance(task['priority'], (int, float)) or not (0 <= task['priority'] <= 10):
                logging.warning(f"Task priority must be number between 0-10: {task}")
                return False

        # Validate confidence score if present
        if 'confidence_score' in task:
            if not isinstance(task['confidence_score'], (int, float)) or not (0 <= task['confidence_score'] <= 1):
                logging.warning(f"Task confidence_score must be number between 0-1: {task}")
                return False

        return True

    def calculate_task_priority(self, task_description):
        """
        Calculates task priority based on description content and context
        """
        description_lower = task_description.lower()

        # High priority keywords (safety, hygiene, urgent)
        high_priority_keywords = [
            'spill', 'leak', 'broken', 'safety', 'urgent', 'emergency',
            'food on floor', 'water damage', 'fire hazard', 'electrical'
        ]

        # Medium priority keywords (cleaning, maintenance)
        medium_priority_keywords = [
            'clean', 'wipe', 'wash', 'scrub', 'disinfect', 'sanitize',
            'empty', 'replace', 'fix', 'repair'
        ]

        # Low priority keywords (organization, aesthetics)
        low_priority_keywords = [
            'organize', 'arrange', 'sort', 'decorate', 'style',
            'books', 'magazines', 'pillows', 'decorative'
        ]

        # Calculate base priority
        if any(keyword in description_lower for keyword in high_priority_keywords):
            base_priority = 8
        elif any(keyword in description_lower for keyword in medium_priority_keywords):
            base_priority = 5
        elif any(keyword in description_lower for keyword in low_priority_keywords):
            base_priority = 2
        else:
            base_priority = 4  # Default priority

        # Adjust based on zone purpose
        if 'kitchen' in self.name.lower() and any(word in description_lower for word in ['food', 'cooking', 'stove']):
            base_priority += 1

        # Ensure priority is within valid range
        return max(1, min(10, base_priority))

    def merge_duplicate_tasks(self):
        """
        Merges duplicate or very similar tasks to reduce redundancy
        """
        tasks = self.state.get('tasks', [])
        active_tasks = [task for task in tasks if task.get('status') == 'active']

        if len(active_tasks) < 2:
            return self.state

        merged_tasks = []
        processed_indices = set()

        for i, task1 in enumerate(active_tasks):
            if i in processed_indices:
                continue

            similar_tasks = [task1]
            similar_indices = {i}

            for j, task2 in enumerate(active_tasks[i+1:], i+1):
                if j in processed_indices:
                    continue

                # Check similarity using simple keyword matching
                if self._tasks_are_similar(task1['description'], task2['description']):
                    similar_tasks.append(task2)
                    similar_indices.add(j)

            if len(similar_tasks) > 1:
                # Merge similar tasks
                merged_task = self._merge_task_group(similar_tasks)
                merged_tasks.append(merged_task)
                processed_indices.update(similar_indices)
            else:
                merged_tasks.append(task1)
                processed_indices.add(i)

        # Add non-active tasks back
        non_active_tasks = [task for task in tasks if task.get('status') != 'active']
        all_merged_tasks = merged_tasks + non_active_tasks

        updated_state = self.state.copy()
        updated_state['tasks'] = all_merged_tasks

        return updated_state

    def expire_old_tasks(self, max_age_days=7):
        """
        Marks old active tasks as expired
        """
        from datetime import datetime, timezone, timedelta

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        updated_tasks = []

        for task in self.state.get('tasks', []):
            if task.get('status') == 'active':
                try:
                    created_at = datetime.fromisoformat(task['created_at'].replace('Z', '+00:00'))
                    if created_at < cutoff_date:
                        # Mark as expired
                        task = task.copy()
                        task['status'] = 'expired'
                        task['expired_at'] = datetime.now(timezone.utc).isoformat()
                        logging.info(f"Expired old task in zone {self.name}: {task['description']}")
                except (ValueError, KeyError) as e:
                    logging.warning(f"Error parsing task date in zone {self.name}: {e}")

            updated_tasks.append(task)

        updated_state = self.state.copy()
        updated_state['tasks'] = updated_tasks

        return updated_state

    def _tasks_are_similar(self, desc1, desc2):
        """
        Determines if two task descriptions are similar enough to merge
        """
        # Simple similarity check using common words
        words1 = set(desc1.lower().split())
        words2 = set(desc2.lower().split())

        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words1 = words1 - stop_words
        words2 = words2 - stop_words

        if not words1 or not words2:
            return False

        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        similarity = intersection / union if union > 0 else 0
        return similarity >= 0.6  # 60% similarity threshold

    def _merge_task_group(self, similar_tasks):
        """
        Merges a group of similar tasks into a single task
        """
        # Use the task with highest priority as base
        base_task = max(similar_tasks, key=lambda t: t.get('priority', 0))

        # Create merged task
        merged_task = base_task.copy()
        merged_task['priority'] = min(10, base_task.get('priority', 0) + 1)  # Increase priority
        merged_task['merged_from'] = [task['id'] for task in similar_tasks if task['id'] != base_task['id']]
        from datetime import datetime, timezone
        merged_task['merged_at'] = datetime.now(timezone.utc).isoformat()

        # Combine descriptions if significantly different
        descriptions = [task['description'] for task in similar_tasks]
        unique_descriptions = []
        for desc in descriptions:
            if not any(self._tasks_are_similar(desc, existing) for existing in unique_descriptions):
                unique_descriptions.append(desc)

        if len(unique_descriptions) > 1:
            merged_task['description'] = f"{base_task['description']} (merged: {', '.join(unique_descriptions[1:])})"

        return merged_task

    # Phase 2: Advanced AI Analysis Methods

    def analyze_with_confidence_scoring(self, image_path):
        """
        Analyzes image with confidence scoring for task completion
        """
        try:
            img = Image.open(image_path)

            # Enhanced prompt with confidence scoring
            prompt = self._format_confidence_scoring_prompt()

            response = self.gemini_client.generate_content([prompt, img])
            result = self._parse_confidence_response(response.text)

            return result

        except Exception as e:
            logging.error(f"Error in confidence scoring analysis for zone {self.name}: {e}")
            return None

    def analyze_with_retry_logic(self, image_path, max_retries=3):
        """
        Analyzes image with retry logic for failed API calls
        """
        import time

        for attempt in range(max_retries):
            try:
                img = Image.open(image_path)
                prompt = self._format_completion_prompt()

                response = self.gemini_client.generate_content([prompt, img])
                return self._parse_gemini_response(response.text)

            except Exception as e:
                # Add full traceback for detailed debugging
                detailed_error = traceback.format_exc()
                logging.error(f"Full exception details for zone {self.name}:\n{detailed_error}")

                # Keep the original warning for context
                logging.warning(f"AI analysis attempt {attempt + 1} failed for zone {self.name}: {e}")

                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = (2 ** attempt) * 1  # 1, 2, 4 seconds
                    time.sleep(wait_time)
                else:
                    logging.error(f"All {max_retries} AI analysis attempts failed for zone {self.name}")
                    return None

    def generate_context_aware_tasks(self, image_path):
        """
        Generates tasks based on zone purpose and historical context
        """
        try:
            img = Image.open(image_path)

            # Enhanced prompt with context awareness
            prompt = self._format_context_aware_prompt()

            response = self.gemini_client.generate_content([prompt, img])
            tasks = self._parse_new_tasks_response(response.text)

            # Add priority and context metadata to tasks
            enhanced_tasks = []
            for task_desc in tasks:
                priority = self.calculate_task_priority(task_desc)
                enhanced_tasks.append({
                    'description': task_desc,
                    'priority': priority,
                    'context_aware': True,
                    'generated_at': datetime.now(timezone.utc).isoformat()
                })

            return enhanced_tasks

        except Exception as e:
            logging.error(f"Error in context-aware task generation for zone {self.name}: {e}")
            return []

    def format_enhanced_completion_prompt(self):
        """
        Formats enhanced prompt for task completion analysis
        """
        active_tasks = [task for task in self.state.get('tasks', []) if task.get('status') == 'active']

        prompt = f"""
        Analyze this image of the {self.name} and determine which of the following active tasks have been completed.

        Zone Purpose: {getattr(self, 'purpose', 'General cleaning and organization')}

        Active Tasks to Check:
        """

        for i, task in enumerate(active_tasks, 1):
            priority_text = f" (Priority: {task.get('priority', 'N/A')})"
            prompt += f"\n{i}. {task['description']}{priority_text}"

        prompt += f"""

        For each completed task, provide:
        1. Task ID: {task['id']}
        2. Confidence Score: 0.0-1.0 (how certain you are it's completed)
        3. Reasoning: Brief explanation of why you think it's completed

        Return ONLY a JSON array of objects with this format:
        [
            {{
                "task_id": "task_id_here",
                "confidence": 0.95,
                "reasoning": "The countertop is now clean and clear"
            }}
        ]

        If no tasks appear completed, return an empty array: []
        """

        return prompt

    def _format_confidence_scoring_prompt(self):
        """
        Formats prompt for confidence scoring analysis
        """
        return self.format_enhanced_completion_prompt()

    def _format_context_aware_prompt(self):
        """
        Formats context-aware prompt for new task generation
        """
        zone_purpose = getattr(self, 'purpose', 'General cleaning and organization')

        # Get completion patterns if available
        patterns = self.state.get('completion_patterns', {})
        pattern_text = ""
        if patterns:
            pattern_text = f"\nUser typically completes: {', '.join([f'{k} ({v:.0%})' for k, v in patterns.items()])}"

        prompt = f"""
        Analyze this image of the {self.name} and identify specific cleaning or organization tasks needed.

        Zone Purpose: {zone_purpose}
        {pattern_text}

        Focus on tasks that are:
        1. Specific and actionable
        2. Relevant to the zone's purpose
        3. Appropriate for the user's typical completion patterns
        4. Clearly visible in the image

        Avoid suggesting tasks for:
        - Items that appear to be intentionally placed
        - Normal wear and tear that doesn't need immediate attention
        - Tasks that would require specialized tools or skills

        Return ONLY a JSON array of task descriptions:
        ["Task description 1", "Task description 2", ...]

        If no tasks are needed, return an empty array: []
        """

        return prompt

    def _parse_confidence_response(self, response_text):
        """
        Parses confidence scoring response from AI
        """
        try:
            import json

            # Clean up response
            cleaned_text = response_text.strip().replace("```json", "").replace("```", "").strip()

            # Parse JSON response
            confidence_data = json.loads(cleaned_text)

            if not isinstance(confidence_data, list):
                return None

            # Extract completed tasks and confidence scores
            completed_tasks = []
            confidence_scores = {}

            for item in confidence_data:
                if isinstance(item, dict) and 'task_id' in item and 'confidence' in item:
                    task_id = item['task_id']
                    confidence = float(item['confidence'])

                    completed_tasks.append(task_id)
                    confidence_scores[task_id] = confidence

            return {
                'completed_tasks': completed_tasks,
                'confidence_scores': confidence_scores
            }

        except Exception as e:
            logging.error(f"Error parsing confidence response: {e}")
            return None

    def _format_completion_prompt(self):
        """
        Formats basic completion prompt for retry logic
        """
        active_tasks = [task for task in self.state.get('tasks', []) if task.get('status') == 'active']

        if not active_tasks:
            return "No active tasks to check for completion."

        prompt = f"Analyze this image of the {self.name} and identify which of these tasks have been completed:\n"

        for i, task in enumerate(active_tasks, 1):
            prompt += f"{i}. {task['description']}\n"

        prompt += "\nReturn ONLY a JSON array of completed task IDs: [\"task_id_1\", \"task_id_2\"]"

        return prompt

    def _parse_gemini_response(self, response_text):
        """
        Parses basic Gemini response for completed task IDs
        """
        try:
            import json

            # Clean up response
            cleaned_text = response_text.strip().replace("```json", "").replace("```", "").strip()

            # Parse JSON response
            task_ids = json.loads(cleaned_text)

            if isinstance(task_ids, list):
                return task_ids
            else:
                return []

        except Exception as e:
            logging.error(f"Error parsing Gemini response: {e}")
            return []

    # Phase 2: Smart Task Features

    def calculate_performance_metrics(self):
        """
        Calculates zone performance metrics
        """
        tasks = self.state.get('tasks', [])
        completed_tasks = [task for task in tasks if task.get('status') == 'completed']
        active_tasks = [task for task in tasks if task.get('status') == 'active']

        total_tasks = len(tasks)
        completed_count = len(completed_tasks)

        # Calculate completion rate
        completion_rate = completed_count / total_tasks if total_tasks > 0 else 0

        # Calculate average completion time
        completion_times = []
        for task in completed_tasks:
            if 'created_at' in task and 'completed_at' in task:
                try:
                    created = datetime.fromisoformat(task['created_at'].replace('Z', '+00:00'))
                    completed = datetime.fromisoformat(task['completed_at'].replace('Z', '+00:00'))
                    completion_time = (completed - created).total_seconds() / 3600  # hours
                    completion_times.append(completion_time)
                except (ValueError, KeyError):
                    continue

        avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0

        # Calculate task creation rate (tasks per day)
        if tasks:
            try:
                earliest_task = min(tasks, key=lambda t: t.get('created_at', ''))
                earliest_date = datetime.fromisoformat(earliest_task['created_at'].replace('Z', '+00:00'))
                days_active = max(1, (datetime.now(timezone.utc) - earliest_date).days)
                task_creation_rate = total_tasks / days_active
            except (ValueError, KeyError):
                task_creation_rate = 0
        else:
            task_creation_rate = 0

        # Calculate efficiency score (completion rate weighted by average priority)
        if completed_tasks:
            avg_priority = sum(task.get('priority', 5) for task in completed_tasks) / len(completed_tasks)
            efficiency_score = completion_rate * (avg_priority / 10)
        else:
            efficiency_score = 0

        return {
            'completion_rate': completion_rate,
            'average_completion_time': avg_completion_time,
            'task_creation_rate': task_creation_rate,
            'efficiency_score': efficiency_score,
            'total_tasks': total_tasks,
            'completed_tasks': completed_count,
            'active_tasks': len(active_tasks)
        }

    def identify_task_dependencies(self):
        """
        Identifies task dependencies and relationships
        """
        tasks = self.state.get('tasks', [])
        active_tasks = [task for task in tasks if task.get('status') == 'active']

        dependencies = {}

        # Define common dependency patterns
        dependency_patterns = [
            # Clear before clean patterns
            (['clear', 'remove', 'put away'], ['clean', 'wipe', 'wash']),
            # Load before start patterns
            (['load', 'fill'], ['start', 'run', 'begin']),
            # Prepare before cook patterns
            (['prepare', 'chop', 'gather'], ['cook', 'bake', 'make']),
            # Clean before organize patterns
            (['clean', 'wash', 'wipe'], ['organize', 'arrange', 'sort'])
        ]

        for task in active_tasks:
            task_deps = []
            task_words = task['description'].lower().split()

            for prerequisite_words, dependent_words in dependency_patterns:
                # Check if this task contains dependent words
                if any(word in task_words for word in dependent_words):
                    # Look for prerequisite tasks
                    for other_task in active_tasks:
                        if other_task['id'] != task['id']:
                            other_words = other_task['description'].lower().split()
                            if any(word in other_words for word in prerequisite_words):
                                # Check if they're related (share common objects)
                                if self._tasks_share_objects(task['description'], other_task['description']):
                                    task_deps.append(other_task['id'])

            if task_deps:
                dependencies[task['id']] = task_deps

        return dependencies

    def optimize_task_scheduling(self):
        """
        Optimizes task scheduling based on priority and dependencies
        """
        tasks = self.state.get('tasks', [])
        active_tasks = [task for task in tasks if task.get('status') == 'active']

        if not active_tasks:
            return []

        # Get dependencies
        dependencies = self.identify_task_dependencies()

        # Sort by priority first
        sorted_tasks = sorted(active_tasks, key=lambda t: t.get('priority', 0), reverse=True)

        # Apply topological sort for dependencies
        scheduled_tasks = []
        remaining_tasks = sorted_tasks.copy()

        while remaining_tasks:
            # Find tasks with no unmet dependencies
            ready_tasks = []
            for task in remaining_tasks:
                task_deps = dependencies.get(task['id'], [])
                scheduled_ids = [t['id'] for t in scheduled_tasks]

                if all(dep_id in scheduled_ids for dep_id in task_deps):
                    ready_tasks.append(task)

            if not ready_tasks:
                # No more dependencies to resolve, add remaining tasks by priority
                ready_tasks = remaining_tasks

            # Add highest priority ready task
            if ready_tasks:
                next_task = max(ready_tasks, key=lambda t: t.get('priority', 0))
                scheduled_tasks.append(next_task)
                remaining_tasks.remove(next_task)

        return scheduled_tasks

    def generate_task_insights(self):
        """
        Generates task insights and recommendations
        """
        tasks = self.state.get('tasks', [])
        completed_tasks = [task for task in tasks if task.get('status') == 'completed']

        # Analyze task patterns
        task_descriptions = [task['description'].lower() for task in tasks]

        # Find most common task types
        task_keywords = {}
        for desc in task_descriptions:
            words = desc.split()
            for word in words:
                if len(word) > 3:  # Skip short words
                    task_keywords[word] = task_keywords.get(word, 0) + 1

        most_common_tasks = sorted(task_keywords.items(), key=lambda x: x[1], reverse=True)[:5]

        # Analyze completion times
        completion_hours = []
        for task in completed_tasks:
            if 'created_at' in task and 'completed_at' in task:
                try:
                    created = datetime.fromisoformat(task['created_at'].replace('Z', '+00:00'))
                    completed = datetime.fromisoformat(task['completed_at'].replace('Z', '+00:00'))
                    hour = completed.hour
                    completion_hours.append(hour)
                except (ValueError, KeyError):
                    continue

        # Find peak activity times
        hour_counts = {}
        for hour in completion_hours:
            hour_counts[hour] = hour_counts.get(hour, 0) + 1

        peak_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        peak_activity_times = [hour for hour, count in peak_hours]

        # Generate recommendations
        recommendations = []
        metrics = self.calculate_performance_metrics()

        if metrics['completion_rate'] < 0.7:
            recommendations.append("Consider breaking down complex tasks into smaller, more manageable steps")

        if metrics['average_completion_time'] > 24:  # More than a day
            recommendations.append("Tasks are taking a long time to complete - consider setting reminders or deadlines")

        if len(most_common_tasks) > 0:
            top_task = most_common_tasks[0][0]
            recommendations.append(f"'{top_task}' tasks are very common - consider creating a routine or automation")

        # Generate efficiency tips
        efficiency_tips = [
            "Group similar tasks together to improve efficiency",
            "Tackle high-priority tasks during your most productive hours",
            "Set up cleaning supplies in convenient locations"
        ]

        if peak_activity_times:
            peak_time_str = ", ".join([f"{hour}:00" for hour in peak_activity_times])
            efficiency_tips.append(f"You're most active at {peak_time_str} - schedule important tasks then")

        return {
            'recommendations': recommendations,
            'patterns': {
                'most_common_tasks': most_common_tasks,
                'peak_activity_times': peak_activity_times,
                'completion_rate': metrics['completion_rate'],
                'average_completion_time': metrics['average_completion_time']
            },
            'efficiency_tips': efficiency_tips
        }

    def apply_adaptive_learning(self):
        """
        Applies adaptive learning from task completion patterns
        """
        learning_data = self.state.get('learning_data', {})
        tasks = self.state.get('tasks', [])

        # Analyze frequently dismissed tasks
        dismissed_tasks = [task for task in tasks if task.get('status') == 'dismissed']
        frequently_dismissed = learning_data.get('frequently_dismissed', [])

        # Update priority based on completion patterns
        updated_priorities = {}
        quickly_completed = learning_data.get('quickly_completed', [])

        for task in tasks:
            if task.get('status') == 'active':
                desc_lower = task['description'].lower()

                # Lower priority for frequently dismissed task types
                if any(dismissed_type in desc_lower for dismissed_type in frequently_dismissed):
                    new_priority = max(1, task.get('priority', 5) - 2)
                    updated_priorities[task['id']] = new_priority

                # Increase priority for quickly completed task types
                elif any(quick_type in desc_lower for quick_type in quickly_completed):
                    new_priority = min(10, task.get('priority', 5) + 1)
                    updated_priorities[task['id']] = new_priority

        # Generate new ignore rules for frequently dismissed tasks
        new_ignore_rules = []
        dismissal_threshold = 3  # If dismissed 3+ times, suggest ignore rule

        for dismissed_type in frequently_dismissed:
            dismissal_count = sum(1 for task in dismissed_tasks
                                if dismissed_type in task['description'].lower())
            if dismissal_count >= dismissal_threshold:
                new_ignore_rules.append(f"ignore tasks containing '{dismissed_type}'")

        # Optimize prompts based on user preferences
        user_prefs = learning_data.get('user_preferences', {})
        optimized_prompts = {}

        if user_prefs.get('prefers_cleaning_over_organizing', 0) > 0.7:
            optimized_prompts['task_generation'] = "Focus more on cleaning tasks than organization"

        if user_prefs.get('responds_well_to_urgent_tasks', 0) > 0.8:
            optimized_prompts['priority_adjustment'] = "Emphasize urgency and importance in task descriptions"

        return {
            'updated_priorities': updated_priorities,
            'new_ignore_rules': new_ignore_rules,
            'optimized_prompts': optimized_prompts,
            'learning_summary': {
                'dismissed_task_types': len(frequently_dismissed),
                'quick_completion_types': len(quickly_completed),
                'user_preference_strength': max(user_prefs.values()) if user_prefs else 0
            }
        }

    def _tasks_share_objects(self, desc1, desc2):
        """
        Determines if two task descriptions reference the same objects
        """
        # Common objects in cleaning tasks
        objects = [
            'counter', 'countertop', 'sink', 'stove', 'dishwasher', 'table',
            'floor', 'surface', 'shelf', 'cabinet', 'drawer', 'appliance'
        ]

        desc1_lower = desc1.lower()
        desc2_lower = desc2.lower()

        shared_objects = []
        for obj in objects:
            if obj in desc1_lower and obj in desc2_lower:
                shared_objects.append(obj)

        return len(shared_objects) > 0

    def _process_enhanced_new_tasks(self, enhanced_tasks):
        """
        Processes enhanced new tasks with priority and context metadata.
        Filters out tasks that match ignore rules.
        """
        for task_data in enhanced_tasks:
            task_description = task_data['description']

            # Check if task should be ignored based on ignore rules
            if self.should_ignore_task(task_description):
                logging.info(f"Ignoring task in zone {self.name} due to ignore rules: {task_description}")
                continue

            task_id = f"task_{int(time.time())}_{self.name.lower().replace(' ', '_')}_{len(self.state.get('tasks', []))}"

            new_task = {
                'id': task_id,
                'description': task_description,
                'status': 'active',
                'created_at': task_data.get('generated_at', datetime.now(timezone.utc).isoformat()),
                'priority': task_data.get('priority', 5),
                'context_aware': task_data.get('context_aware', False)
            }

            # Validate task schema
            if self.validate_task_schema(new_task):
                # Add to state
                if 'tasks' not in self.state:
                    self.state['tasks'] = []

                self.state['tasks'].append(new_task)

                # Send notification if enabled
                if self.notify_on_create:
                    self.send_notification('task_created', {'task': new_task})

                # Add to Home Assistant todo list
                self._add_task_to_ha_todo(new_task)

                logging.info(f"Created enhanced task in zone {self.name}: {new_task['description']} (Priority: {new_task['priority']})")
            else:
                logging.warning(f"Enhanced task failed validation in zone {self.name}: {task_data}")

    def _add_task_to_ha_todo(self, task):
        """
        Adds a task to the Home Assistant todo list
        """
        try:
            success = self.ha_client.add_todo_item(
                entity_id=self.todo_list_entity,
                item=task['description'],
                description=f"Priority: {task.get('priority', 5)} | Created: {task.get('created_at', 'Unknown')}"
            )

            if success:
                logging.info(f"Added task to HA todo list '{self.todo_list_entity}': {task['description']}")
            else:
                logging.warning(f"Failed to add task to HA todo list '{self.todo_list_entity}': {task['description']}")

        except Exception as e:
            logging.error(f"Error adding task to HA todo list: {e}")

    def get_sensor_data(self):
        """
        Gets sensor data for this zone to send to Home Assistant
        """
        tasks = self.state.get('tasks', [])
        active_tasks = [task for task in tasks if task.get('status') == 'active']
        completed_tasks = [task for task in tasks if task.get('status') == 'completed']

        # Calculate performance metrics
        performance_metrics = self.calculate_performance_metrics()

        # Get last analysis time
        last_analysis = None
        if hasattr(self, 'last_analysis_time') and self.last_analysis_time:
            last_analysis = self.last_analysis_time.isoformat()

        # Get task details for UI
        task_details = []
        for task in active_tasks[:5]:  # Limit to 5 most recent for UI
            task_details.append({
                'id': task.get('id'),
                'description': task.get('description'),
                'priority': task.get('priority', 'normal'),
                'created_at': task.get('created_at'),
                'status': task.get('status', 'active')
            })

        return {
            'state': len(active_tasks),  # Number of active tasks as the main state
            'attributes': {
                'zone_name': self.name,
                'display_name': self.name.replace('_', ' ').title(),
                'purpose': getattr(self, 'purpose', 'Keep everything tidy and clean'),
                'total_tasks': len(tasks),
                'active_tasks': len(active_tasks),
                'completed_tasks': len(completed_tasks),
                'completion_rate': performance_metrics.get('completion_rate', 0),
                'efficiency_score': performance_metrics.get('efficiency_score', 0),
                'average_completion_time': performance_metrics.get('average_completion_time', 0),
                'last_analysis': last_analysis,
                'last_updated': datetime.now(timezone.utc).isoformat(),
                'camera_entity': self.camera_entity,
                'todo_list_entity': self.todo_list_entity,
                'update_frequency': self.update_frequency,
                'tasks': task_details,  # Recent tasks for UI display
                'ignore_rules': self.get_ignore_rules(),
                'notifications_enabled': getattr(self, 'notifications_enabled', True),
                'notification_personality': getattr(self, 'notification_personality', 'default'),
                'unit_of_measurement': 'tasks',
                'friendly_name': f"{self.name} Tasks",
                'icon': 'mdi:format-list-checks',
                'device_class': 'aicleaner_zone'
            }
        }

    def update_ha_sensor(self):
        """
        Updates the Home Assistant sensor for this zone
        """
        try:
            sensor_data = self.get_sensor_data()
            sensor_entity_id = f"sensor.aicleaner_{self.name.lower().replace(' ', '_')}_tasks"

            success = self.ha_client.update_sensor(
                entity_id=sensor_entity_id,
                state=sensor_data['state'],
                attributes=sensor_data['attributes']
            )

            if success:
                logging.info(f"Updated HA sensor '{sensor_entity_id}' for zone {self.name}")
            else:
                logging.warning(f"Failed to update HA sensor '{sensor_entity_id}' for zone {self.name}")

        except Exception as e:
            logging.error(f"Error updating HA sensor for zone {self.name}: {e}")

    def _parse_new_tasks_response(self, response_text):
        """
        Parses new tasks response from AI
        """
        try:
            import json

            # Clean up response
            cleaned_text = response_text.strip().replace("```json", "").replace("```", "").strip()

            # Parse JSON response
            tasks = json.loads(cleaned_text)

            if isinstance(tasks, list):
                return [task for task in tasks if isinstance(task, str)]
            else:
                return []

        except Exception as e:
            logging.error(f"Error parsing new tasks response: {e}")
            return []

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
        """Process new tasks: update state, HA todo list, and send notifications.
        Filters out tasks that match ignore rules."""
        timestamp = int(datetime.now(timezone.utc).timestamp())

        for i, description in enumerate(new_task_descriptions):
            # Check if task should be ignored based on ignore rules
            if self.should_ignore_task(description):
                logging.info(f"Ignoring task in zone {self.name} due to ignore rules: {description}")
                continue
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

    def add_todo_item(self, entity_id, item, description=None):
        """Add item to Home Assistant todo list"""
        try:
            url = f"{self.api_url}/api/services/todo/add_item"
            payload = {
                "entity_id": entity_id,
                "item": item
            }
            if description:
                payload["description"] = description

            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            logging.error(f"Error adding todo item: {e}")
            return False

    def update_todo_item(self, entity_id, item, status=None, description=None):
        """Update item in Home Assistant todo list"""
        try:
            url = f"{self.api_url}/api/services/todo/update_item"
            payload = {
                "entity_id": entity_id,
                "item": item
            }
            if status:
                payload["status"] = status
            if description:
                payload["description"] = description

            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            logging.error(f"Error updating todo item: {e}")
            return False

    def remove_todo_item(self, entity_id, item):
        """Remove item from Home Assistant todo list"""
        try:
            url = f"{self.api_url}/api/services/todo/remove_item"
            payload = {
                "entity_id": entity_id,
                "item": item
            }

            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            logging.error(f"Error removing todo item: {e}")
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

        # Initialize configuration manager
        self.config_manager = ConfigurationManager()

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

        # Track last global analysis for UI display
        self.last_global_analysis = None

        # State management configuration
        self.state_schema_version = "2.1.0"
        self.max_backup_files = 10
        self.compression_enabled = True

        logging.info(f"Initialized AICleaner with {len(self.zones)} zones")


    def _load_config(self):
        """
        Loads configuration using ConfigurationManager
        """
        # SUPERVISOR_TOKEN is a reliable indicator of the HA Add-on environment
        if 'SUPERVISOR_TOKEN' in os.environ:
            logging.info("Loading configuration from Home Assistant addon environment")
            return self._load_from_addon_env()
        else:
            logging.info("Loading configuration from local development environment")
            # Use configuration manager for local development
            config = self.config_manager.load_configuration()

            # Add HA API details for local development
            config['ha_api_url'] = os.getenv('HA_API_URL', 'http://localhost:8123/api')
            config['ha_token'] = os.getenv('HA_TOKEN', '')

            return config

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
        """Validates the loaded configuration for v2.0 requirements using ConfigurationManager"""
        logging.info("Validating v2.0 configuration")

        # Use configuration manager for validation
        is_valid = self.config_manager.validate_configuration(self.config)

        if not is_valid:
            errors = self.config_manager.get_validation_errors()
            guidance = self.config_manager.get_startup_guidance()

            # Log detailed error information
            logging.error("Configuration validation failed:")
            for error in errors:
                logging.error(f"  - {error}")

            # Print guidance to console for user visibility
            print("\n" + guidance + "\n")

            # Raise exception with first error for backward compatibility
            raise ValueError(f"Configuration validation failed: {errors[0] if errors else 'Unknown error'}")

        # Check if configuration is complete enough to start
        if not self.config_manager.is_configuration_complete(self.config):
            guidance = self.config_manager.get_startup_guidance()
            print("\n" + guidance + "\n")
            raise ValueError("Configuration is incomplete - missing required settings")

        logging.info(f"Configuration validated successfully with {len(self.config.get('zones', []))} zones")

    def _validate_zone_config(self, zone_config, index):
        """
        Legacy zone validation method - now delegated to ConfigurationManager
        Kept for backward compatibility
        """
        # This method is now handled by ConfigurationManager
        # but kept for any legacy code that might call it directly
        temp_config = {'zones': [zone_config]}
        if not self.config_manager.validate_configuration(temp_config):
            errors = self.config_manager.get_validation_errors()
            if errors:
                raise ValueError(f"Zone {index}: {errors[0]}")

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

        # Update global analysis time for UI display
        self.last_global_analysis = datetime.now(timezone.utc)

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

        # Sync HA integrations after analysis if any zones were processed
        if due_zones:
            try:
                self.sync_all_ha_integrations()
            except Exception as e:
                logging.error(f"Error syncing HA integrations: {e}")

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

    # Home Assistant API Integration Methods

    def update_all_zone_sensors(self):
        """
        Updates Home Assistant sensors for all zones
        """
        logging.info("Updating HA sensors for all zones")

        for zone in self.zones:
            try:
                zone.update_ha_sensor()
            except Exception as e:
                logging.error(f"Error updating HA sensor for zone '{zone.name}': {e}")

    def get_global_sensor_data(self):
        """
        Gets global sensor data across all zones
        """
        total_active_tasks = 0
        total_completed_tasks = 0
        total_tasks = 0
        zones_data = []

        for zone in self.zones:
            zone_sensor_data = zone.get_sensor_data()
            zone_attributes = zone_sensor_data['attributes']

            total_active_tasks += zone_attributes['active_tasks']
            total_completed_tasks += zone_attributes['completed_tasks']
            total_tasks += zone_attributes['total_tasks']

            zones_data.append({
                'name': zone.name,
                'active_tasks': zone_attributes['active_tasks'],
                'completed_tasks': zone_attributes['completed_tasks'],
                'completion_rate': zone_attributes['completion_rate'],
                'efficiency_score': zone_attributes['efficiency_score']
            })

        # Calculate global completion rate
        global_completion_rate = total_completed_tasks / total_tasks if total_tasks > 0 else 0

        # Calculate average efficiency score
        efficiency_scores = [zone_data['efficiency_score'] for zone_data in zones_data]
        avg_efficiency = sum(efficiency_scores) / len(efficiency_scores) if efficiency_scores else 0

        # Get system status
        system_status = 'active' if len(self.zones) > 0 else 'inactive'
        if total_active_tasks > 10:
            system_status = 'busy'
        elif any(zone_data['efficiency_score'] < 0.5 for zone_data in zones_data):
            system_status = 'warning'

        # Get last global analysis time
        last_analysis = None
        if hasattr(self, 'last_global_analysis') and self.last_global_analysis:
            last_analysis = self.last_global_analysis.isoformat()

        return {
            'state': system_status,  # Use status instead of task count for global sensor
            'attributes': {
                'status': system_status,
                'total_active_tasks': total_active_tasks,
                'total_completed_tasks': total_completed_tasks,
                'total_tasks': total_tasks,
                'global_completion_rate': round(global_completion_rate, 3),
                'average_efficiency_score': round(avg_efficiency, 3),
                'total_zones': len(self.zones),
                'zones': zones_data,
                'last_analysis': last_analysis,
                'last_updated': datetime.now(timezone.utc).isoformat(),
                'version': '2.0.0',
                'addon_name': 'AICleaner v2.0',
                'unit_of_measurement': None,
                'friendly_name': 'AICleaner System Status',
                'icon': 'mdi:robot-vacuum',
                'device_class': 'aicleaner_system'
            }
        }

    def update_global_sensor(self):
        """
        Updates the global AICleaner sensor in Home Assistant
        """
        try:
            sensor_data = self.get_global_sensor_data()
            sensor_entity_id = "sensor.aicleaner_system_status"

            success = self.ha_client.update_sensor(
                entity_id=sensor_entity_id,
                state=sensor_data['state'],
                attributes=sensor_data['attributes']
            )

            if success:
                logging.info(f"Updated global HA sensor '{sensor_entity_id}'")
            else:
                logging.warning(f"Failed to update global HA sensor '{sensor_entity_id}'")

        except Exception as e:
            logging.error(f"Error updating global HA sensor: {e}")

    def sync_all_ha_integrations(self):
        """
        Synchronizes all Home Assistant integrations (sensors and todo lists)
        """
        logging.info("Synchronizing all HA integrations")

        try:
            # Update all zone sensors
            self.update_all_zone_sensors()

            # Update global sensor
            self.update_global_sensor()

            logging.info("HA integration synchronization completed")

        except Exception as e:
            logging.error(f"Error during HA integration synchronization: {e}")

    # Advanced State Management Methods

    def get_state_schema_version(self):
        """Returns the current state schema version"""
        return self.state_schema_version

    def migrate_state_to_current_version(self, old_state):
        """
        Migrates state from older versions to current schema
        """
        # Detect current version
        current_version = old_state.get('schema_version', '1.0.0')

        if current_version == self.state_schema_version:
            return old_state

        logging.info(f"Migrating state from version {current_version} to {self.state_schema_version}")

        migrated_state = old_state.copy()

        # Migration from v1.0.0 to v2.0.0+
        if current_version.startswith('1.'):
            migrated_state = self._migrate_from_v1_to_v2(old_state)

        # Migration from v2.0.0 to v2.1.0
        if current_version.startswith('2.0'):
            migrated_state = self._migrate_from_v2_0_to_v2_1(migrated_state)

        # Set current schema version
        migrated_state['schema_version'] = self.state_schema_version
        migrated_state['migrated_at'] = datetime.now(timezone.utc).isoformat()

        logging.info(f"State migration completed to version {self.state_schema_version}")
        return migrated_state

    def create_state_backup(self):
        """
        Creates a backup of the current state file
        """
        import shutil
        from datetime import datetime

        state_path = '/data/state.json'
        if not os.path.exists(state_path):
            logging.warning("No state file exists to backup")
            return None

        # Create backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f'/data/backups/state_backup_{timestamp}.json'

        # Ensure backup directory exists
        backup_dir = os.path.dirname(backup_path)
        os.makedirs(backup_dir, exist_ok=True)

        try:
            # Copy state file to backup location
            shutil.copy2(state_path, backup_path)

            # Compress backup if enabled
            if self.compression_enabled:
                compressed_path = backup_path + '.gz'
                self._compress_file(backup_path, compressed_path)
                os.remove(backup_path)  # Remove uncompressed version
                backup_path = compressed_path

            # Clean up old backups
            self._cleanup_old_backups()

            logging.info(f"State backup created: {backup_path}")
            return backup_path

        except Exception as e:
            logging.error(f"Error creating state backup: {e}")
            return None

    def compress_state(self, state_data):
        """
        Compresses state data using gzip
        """
        import gzip
        import json

        try:
            # Convert state to JSON string
            json_str = json.dumps(state_data, separators=(',', ':'))  # Compact format

            # Compress using gzip
            compressed_data = gzip.compress(json_str.encode('utf-8'))

            return compressed_data

        except Exception as e:
            logging.error(f"Error compressing state: {e}")
            return None

    def decompress_state(self, compressed_data):
        """
        Decompresses state data from gzip format
        """
        import gzip
        import json

        try:
            # Decompress data
            json_str = gzip.decompress(compressed_data).decode('utf-8')

            # Parse JSON
            state_data = json.loads(json_str)

            return state_data

        except Exception as e:
            logging.error(f"Error decompressing state: {e}")
            return None

    def detect_state_corruption(self, state_data):
        """
        Detects corruption in state data
        """
        try:
            # Check basic structure
            if not isinstance(state_data, dict):
                logging.warning("State is not a dictionary")
                return True

            # Check each zone's state
            for zone_name, zone_state in state_data.items():
                if zone_name in ['schema_version', 'migrated_at', 'last_backup']:
                    continue  # Skip metadata fields

                if not isinstance(zone_state, dict):
                    logging.warning(f"Zone state for '{zone_name}' is not a dictionary")
                    return True

                # Check tasks array
                tasks = zone_state.get('tasks', [])
                if not isinstance(tasks, list):
                    logging.warning(f"Tasks for zone '{zone_name}' is not a list")
                    return True

                # Validate each task
                for i, task in enumerate(tasks):
                    if not self._validate_task_for_corruption(task, zone_name, i):
                        return True

            return False  # No corruption detected

        except Exception as e:
            logging.error(f"Error during corruption detection: {e}")
            return True  # Assume corruption if we can't validate

    def recover_from_corruption(self, corrupted_state):
        """
        Attempts to recover from state corruption
        """
        logging.info("Attempting to recover from state corruption")

        recovered_state = {
            'schema_version': self.state_schema_version,
            'recovered_at': datetime.now(timezone.utc).isoformat()
        }

        # Try to recover each zone
        for zone_name, zone_state in corrupted_state.items():
            if zone_name in ['schema_version', 'migrated_at', 'last_backup', 'recovered_at']:
                continue  # Skip metadata fields

            try:
                recovered_zone_state = self._recover_zone_state(zone_state, zone_name)
                recovered_state[zone_name] = recovered_zone_state

            except Exception as e:
                logging.error(f"Could not recover zone '{zone_name}': {e}")
                # Create minimal valid state for this zone
                recovered_state[zone_name] = {'tasks': []}

        logging.info("State recovery completed")
        return recovered_state

    def get_state_analytics(self):
        """
        Provides analytics and monitoring data for the state
        """
        try:
            state_path = '/data/state.json'

            # Calculate state size
            state_size_bytes = 0
            if os.path.exists(state_path):
                state_size_bytes = os.path.getsize(state_path)

            # Count total tasks and zones
            total_tasks = 0
            total_zones = len(self.state)
            active_tasks = 0
            completed_tasks = 0

            # Ensure state is a dictionary
            if not isinstance(self.state, dict):
                logging.warning(f"State is not a dictionary: {type(self.state)}")
                return {
                    'total_tasks': 0,
                    'total_zones': 0,
                    'state_size_bytes': state_size_bytes,
                    'health_score': 0.0,
                    'error': 'Invalid state format'
                }

            for zone_name, zone_state in self.state.items():
                if zone_name in ['schema_version', 'migrated_at', 'last_backup']:
                    total_zones -= 1  # Don't count metadata as zones
                    continue

                tasks = zone_state.get('tasks', [])
                total_tasks += len(tasks)

                for task in tasks:
                    status = task.get('status', 'unknown')
                    if status == 'active':
                        active_tasks += 1
                    elif status == 'completed':
                        completed_tasks += 1

            # Calculate health score
            health_score = self._calculate_state_health_score()

            # Get last modified time
            last_modified = None
            if os.path.exists(state_path):
                last_modified = datetime.fromtimestamp(os.path.getmtime(state_path)).isoformat()

            return {
                'total_tasks': total_tasks,
                'active_tasks': active_tasks,
                'completed_tasks': completed_tasks,
                'total_zones': total_zones,
                'state_size_bytes': state_size_bytes,
                'state_size_mb': round(state_size_bytes / (1024 * 1024), 2),
                'last_modified': last_modified,
                'health_score': health_score,
                'schema_version': self.state.get('schema_version', 'unknown') if isinstance(self.state, dict) else 'unknown'
            }

        except Exception as e:
            logging.error(f"Error generating state analytics: {e}")
            return {
                'total_tasks': 0,
                'total_zones': 0,
                'state_size_bytes': 0,
                'health_score': 0.0,
                'error': str(e)
            }

    def optimize_state_performance(self, state_data):
        """
        Optimizes state for better performance
        """
        optimized_state = state_data.copy()

        # Remove expired tasks older than 30 days
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)

        for zone_name, zone_state in optimized_state.items():
            if zone_name in ['schema_version', 'migrated_at', 'last_backup']:
                continue

            tasks = zone_state.get('tasks', [])
            filtered_tasks = []

            for task in tasks:
                # Keep active and recently completed tasks
                if task.get('status') == 'active':
                    filtered_tasks.append(task)
                elif task.get('status') == 'completed':
                    try:
                        completed_at = datetime.fromisoformat(task.get('completed_at', '').replace('Z', '+00:00'))
                        if completed_at > cutoff_date:
                            filtered_tasks.append(task)
                    except (ValueError, TypeError):
                        # Keep task if we can't parse date
                        filtered_tasks.append(task)
                elif task.get('status') == 'expired':
                    # Remove expired tasks
                    continue
                else:
                    # Keep other statuses
                    filtered_tasks.append(task)

            zone_state['tasks'] = filtered_tasks

        # Add optimization metadata
        optimized_state['last_optimized'] = datetime.now(timezone.utc).isoformat()

        return optimized_state

    def measure_state_performance(self, state_data):
        """
        Measures performance metrics for state operations
        """
        import time
        import json
        import sys

        # Measure load time
        start_time = time.time()
        json_str = json.dumps(state_data)
        load_time_ms = (time.time() - start_time) * 1000

        # Measure save time
        start_time = time.time()
        parsed_state = json.loads(json_str)
        save_time_ms = (time.time() - start_time) * 1000

        # Estimate memory usage (approximate)
        memory_usage_mb = sys.getsizeof(state_data) / (1024 * 1024)

        return {
            'load_time_ms': round(load_time_ms, 2),
            'save_time_ms': round(save_time_ms, 2),
            'memory_usage_mb': round(memory_usage_mb, 2),
            'state_size_bytes': len(json_str),
            'task_count': self._count_total_tasks(state_data)
        }

    # Helper methods for advanced state management

    def _migrate_from_v1_to_v2(self, v1_state):
        """Migrates state from v1.0 format to v2.0 format"""
        v2_state = {}

        # If v1 state has tasks at root level, move to Kitchen zone
        if 'tasks' in v1_state:
            v2_state['Kitchen'] = {
                'tasks': []
            }

            for task in v1_state['tasks']:
                # Add missing v2.0 fields
                migrated_task = task.copy()
                if 'created_at' not in migrated_task:
                    migrated_task['created_at'] = datetime.now(timezone.utc).isoformat()
                if 'priority' not in migrated_task:
                    migrated_task['priority'] = 5  # Default priority

                v2_state['Kitchen']['tasks'].append(migrated_task)

        return v2_state

    def _migrate_from_v2_0_to_v2_1(self, v2_0_state):
        """Migrates state from v2.0 to v2.1 format"""
        v2_1_state = v2_0_state.copy()

        # Add new v2.1 features
        for zone_name, zone_state in v2_1_state.items():
            if zone_name in ['schema_version', 'migrated_at']:
                continue

            # Add analytics data if missing
            if 'analytics' not in zone_state:
                zone_state['analytics'] = {
                    'task_frequency': {},
                    'completion_times': {},
                    'peak_hours': []
                }

        return v2_1_state

    def _validate_task_for_corruption(self, task, zone_name, task_index):
        """Validates a single task for corruption"""
        if not isinstance(task, dict):
            logging.warning(f"Task {task_index} in zone '{zone_name}' is not a dictionary")
            return False

        # Check required fields
        required_fields = ['id', 'description', 'status']
        for field in required_fields:
            if field not in task:
                logging.warning(f"Task {task_index} in zone '{zone_name}' missing field '{field}'")
                return False

        # Validate field types and values
        if not isinstance(task['description'], str) or not task['description'].strip():
            logging.warning(f"Task {task_index} in zone '{zone_name}' has invalid description")
            return False

        valid_statuses = ['active', 'completed', 'expired', 'dismissed']
        if task['status'] not in valid_statuses:
            logging.warning(f"Task {task_index} in zone '{zone_name}' has invalid status: {task['status']}")
            return False

        return True

    def _recover_zone_state(self, zone_state, zone_name):
        """Recovers a single zone's state from corruption"""
        if not isinstance(zone_state, dict):
            return {'tasks': []}

        recovered_tasks = []
        tasks = zone_state.get('tasks', [])

        if isinstance(tasks, list):
            for i, task in enumerate(tasks):
                try:
                    recovered_task = self._recover_single_task(task, zone_name, i)
                    if recovered_task:
                        recovered_tasks.append(recovered_task)
                except Exception as e:
                    logging.warning(f"Could not recover task {i} in zone '{zone_name}': {e}")

        return {
            'tasks': recovered_tasks,
            'recovered_at': datetime.now(timezone.utc).isoformat()
        }

    def _recover_single_task(self, task, zone_name, task_index):
        """Recovers a single corrupted task"""
        if not isinstance(task, dict):
            return None

        # Create minimal valid task
        recovered_task = {
            'id': task.get('id', f'recovered_{zone_name}_{task_index}_{int(time.time())}'),
            'description': str(task.get('description', 'Recovered task')).strip() or 'Recovered task',
            'status': 'active' if task.get('status') not in ['active', 'completed', 'expired', 'dismissed'] else task['status'],
            'created_at': task.get('created_at', datetime.now(timezone.utc).isoformat()),
            'recovered': True
        }

        # Add optional fields if valid
        if 'priority' in task and isinstance(task['priority'], (int, float)) and 0 <= task['priority'] <= 10:
            recovered_task['priority'] = task['priority']
        else:
            recovered_task['priority'] = 5

        return recovered_task

    def _calculate_state_health_score(self):
        """Calculates overall health score for the state (0.0 to 1.0)"""
        try:
            total_score = 0.0
            factors = 0

            # Factor 1: Corruption check (0.4 weight)
            try:
                if not self.detect_state_corruption(self.state):
                    total_score += 0.4
            except Exception:
                pass  # Skip corruption check if it fails
            factors += 0.4

            # Factor 2: Task validity (0.3 weight)
            valid_tasks = 0
            total_tasks = 0

            if isinstance(self.state, dict):
                for zone_name, zone_state in self.state.items():
                    if zone_name in ['schema_version', 'migrated_at', 'last_backup']:
                        continue

                    if isinstance(zone_state, dict):
                        tasks = zone_state.get('tasks', [])
                        for task in tasks:
                            total_tasks += 1
                            if self._validate_task_for_corruption(task, zone_name, 0):
                                valid_tasks += 1

            if total_tasks > 0:
                task_validity_score = valid_tasks / total_tasks
                total_score += task_validity_score * 0.3
            else:
                total_score += 0.3  # Perfect score if no tasks
            factors += 0.3

            # Factor 3: Schema version compatibility (0.2 weight)
            if isinstance(self.state, dict):
                current_version = self.state.get('schema_version', '1.0.0')
                if current_version == self.state_schema_version:
                    total_score += 0.2
            factors += 0.2

            # Factor 4: Recent activity (0.1 weight)
            state_path = '/data/state.json'
            if os.path.exists(state_path):
                last_modified = os.path.getmtime(state_path)
                hours_since_modified = (time.time() - last_modified) / 3600

                if hours_since_modified < 24:  # Modified within last day
                    total_score += 0.1
                elif hours_since_modified < 168:  # Modified within last week
                    total_score += 0.05
            factors += 0.1

            return min(1.0, total_score / factors) if factors > 0 else 0.0

        except Exception as e:
            logging.error(f"Error calculating health score: {e}")
            return 0.0

    def _compress_file(self, source_path, target_path):
        """Compresses a file using gzip"""
        import gzip
        import shutil

        with open(source_path, 'rb') as f_in:
            with gzip.open(target_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

    def _cleanup_old_backups(self):
        """Removes old backup files beyond the maximum limit"""
        backup_dir = '/data/backups'
        if not os.path.exists(backup_dir):
            return

        try:
            # Get all backup files
            backup_files = []
            for filename in os.listdir(backup_dir):
                if filename.startswith('state_backup_'):
                    filepath = os.path.join(backup_dir, filename)
                    backup_files.append((filepath, os.path.getmtime(filepath)))

            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x[1], reverse=True)

            # Remove old backups beyond the limit
            for filepath, _ in backup_files[self.max_backup_files:]:
                os.remove(filepath)
                logging.info(f"Removed old backup: {filepath}")

        except Exception as e:
            logging.error(f"Error cleaning up old backups: {e}")

    def _count_total_tasks(self, state_data):
        """Counts total tasks across all zones"""
        total = 0
        if isinstance(state_data, dict):
            for zone_name, zone_state in state_data.items():
                if zone_name in ['schema_version', 'migrated_at', 'last_backup', 'last_optimized']:
                    continue
                if isinstance(zone_state, dict):
                    total += len(zone_state.get('tasks', []))
        return total

    def _create_large_test_state(self, task_count):
        """Creates a large state for testing compression (test helper)"""
        large_state = {
            'schema_version': self.state_schema_version,
            'Kitchen': {'tasks': []},
            'Living Room': {'tasks': []},
            'Bedroom': {'tasks': []}
        }

        zones = ['Kitchen', 'Living Room', 'Bedroom']
        for i in range(task_count):
            zone = zones[i % len(zones)]
            task = {
                'id': f'test_task_{i}',
                'description': f'Test task number {i} with some description text',
                'status': 'active' if i % 2 == 0 else 'completed',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'priority': (i % 10) + 1
            }
            large_state[zone]['tasks'].append(task)

        return large_state

    def _create_unoptimized_test_state(self):
        """Creates an unoptimized state for testing performance (test helper)"""
        # Create state with many expired tasks and redundant data
        old_date = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()

        unoptimized_state = {
            'schema_version': self.state_schema_version,
            'Kitchen': {
                'tasks': []
            }
        }

        # Add many expired tasks
        for i in range(100):
            task = {
                'id': f'expired_task_{i}',
                'description': f'Old expired task {i}',
                'status': 'expired',
                'created_at': old_date,
                'expired_at': old_date,
                'priority': 5
            }
            unoptimized_state['Kitchen']['tasks'].append(task)

        # Add some active tasks
        for i in range(10):
            task = {
                'id': f'active_task_{i}',
                'description': f'Active task {i}',
                'status': 'active',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'priority': 5
            }
            unoptimized_state['Kitchen']['tasks'].append(task)

        return unoptimized_state




if __name__ == "__main__":
    try:
        logging.info("Initializing AICleaner v2.0 application")
        cleaner = AICleaner()
        cleaner.run()
    except Exception as e:
        logging.critical(f"AICleaner v2.0 application failed to initialize or run: {e}")