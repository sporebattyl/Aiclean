"""
AI Analyzer - Enhanced AI analysis with ignore rules and comparison capabilities
"""
import os
import json
import hashlib
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from PIL import Image
import requests
from google.generativeai.client import configure
from google.generativeai.generative_models import GenerativeModel

from ..data import AIAnalysisResult, IgnoreRuleRepository, Zone


class AIAnalyzer:
    """Enhanced AI analyzer with ignore rules and stateful analysis"""
    
    def __init__(self, gemini_api_key: str):
        self.logger = logging.getLogger(__name__)
        self.ignore_rule_repo = IgnoreRuleRepository()
        
        if not gemini_api_key:
            raise ValueError("Google Gemini API key is required")
        
        configure(api_key=gemini_api_key)
        self.gemini_model = GenerativeModel('gemini-1.5-pro')
        
        # Analysis configuration
        self.max_retries = 3
        self.timeout_seconds = 30
    
    def analyze_zone_image(self, zone: Zone, image_path: str = None) -> AIAnalysisResult:
        """
        Analyze an image for a specific zone with ignore rules applied
        
        Args:
            zone: Zone configuration
            image_path: Path to image file (if None, will capture from camera)
            
        Returns:
            AIAnalysisResult with cleanliness score, tasks, and metadata
        """
        start_time = datetime.now()
        
        try:
            # Capture image if not provided
            if not image_path:
                image_path = self._capture_zone_image(zone)
                if not image_path:
                    return AIAnalysisResult(
                        cleanliness_score=0,
                        tasks=[],
                        error_message="Failed to capture image from camera"
                    )
            
            # Calculate image hash for duplicate detection
            image_hash = self._calculate_image_hash(image_path)
            
            # Get ignore rules for this zone
            ignore_rules = self.ignore_rule_repo.get_by_zone(zone.id, enabled_only=True)
            
            # Perform AI analysis
            raw_analysis = self._analyze_with_gemini(image_path, zone, ignore_rules)
            
            if not raw_analysis:
                return AIAnalysisResult(
                    cleanliness_score=0,
                    tasks=[],
                    error_message="AI analysis failed"
                )
            
            # Apply ignore rules to filter tasks
            filtered_tasks = self._apply_ignore_rules(raw_analysis.get('tasks', []), ignore_rules)
            
            # Limit tasks based on zone configuration
            if len(filtered_tasks) > zone.max_tasks_per_analysis:
                filtered_tasks = filtered_tasks[:zone.max_tasks_per_analysis]
                self.logger.info(f"Limited tasks to {zone.max_tasks_per_analysis} for zone {zone.name}")
            
            # Calculate analysis duration
            analysis_duration = (datetime.now() - start_time).total_seconds()
            
            result = AIAnalysisResult(
                cleanliness_score=raw_analysis.get('score', 0),
                tasks=filtered_tasks,
                confidence_scores=raw_analysis.get('confidence_scores', [0.8] * len(filtered_tasks)),
                analysis_duration=analysis_duration,
                tokens_used=raw_analysis.get('tokens_used', 0),
                image_hash=image_hash
            )
            
            self.logger.info(f"Analysis complete for zone {zone.name}: "
                           f"score={result.cleanliness_score}, tasks={len(result.tasks)}, "
                           f"duration={analysis_duration:.2f}s")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to analyze zone {zone.name}: {e}")
            return AIAnalysisResult(
                cleanliness_score=0,
                tasks=[],
                error_message=str(e),
                analysis_duration=(datetime.now() - start_time).total_seconds()
            )
        finally:
            # Clean up temporary image file if we created it
            if image_path and image_path.startswith('temp_') and os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except Exception as e:
                    self.logger.warning(f"Failed to clean up temporary image {image_path}: {e}")
    
    def _capture_zone_image(self, zone: Zone) -> Optional[str]:
        """Capture image from zone's camera"""
        try:
            # This would integrate with Home Assistant API
            # For now, return a placeholder
            ha_url = os.environ.get('HA_URL', 'http://supervisor/core')
            ha_token = os.environ.get('SUPERVISOR_TOKEN')
            
            if not ha_token:
                self.logger.error("No Home Assistant token available")
                return None
            
            snapshot_url = f"{ha_url}/api/camera_proxy/{zone.camera_entity_id}"
            headers = {
                "Authorization": f"Bearer {ha_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(snapshot_url, headers=headers, timeout=self.timeout_seconds)
            response.raise_for_status()
            
            # Save to temporary file
            temp_path = f"temp_snapshot_{zone.id}_{int(datetime.now().timestamp())}.jpg"
            with open(temp_path, 'wb') as f:
                f.write(response.content)
            
            self.logger.info(f"Captured image for zone {zone.name}: {temp_path}")
            return temp_path
            
        except Exception as e:
            self.logger.error(f"Failed to capture image for zone {zone.name}: {e}")
            return None
    
    def _calculate_image_hash(self, image_path: str) -> str:
        """Calculate hash of image for duplicate detection"""
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            return hashlib.md5(image_data).hexdigest()
        except Exception as e:
            self.logger.warning(f"Failed to calculate image hash: {e}")
            return ""
    
    def _analyze_with_gemini(self, image_path: str, zone: Zone, ignore_rules: List) -> Optional[Dict[str, Any]]:
        """Perform AI analysis with Gemini"""
        try:
            img = Image.open(image_path)
            
            # Build prompt with ignore rules
            prompt = self._build_analysis_prompt(zone, ignore_rules)
            
            # Perform analysis with retries
            for attempt in range(self.max_retries):
                try:
                    response = self.gemini_model.generate_content([prompt, img])
                    result = self._parse_gemini_response(response.text)
                    
                    if result:
                        # Add metadata
                        result['tokens_used'] = getattr(response, 'usage_metadata', {}).get('total_token_count', 0)
                        return result
                    
                except Exception as e:
                    self.logger.warning(f"Gemini analysis attempt {attempt + 1} failed: {e}")
                    if attempt == self.max_retries - 1:
                        raise
            
            return None
            
        except Exception as e:
            self.logger.error(f"Gemini analysis failed: {e}")
            return None
    
    def _build_analysis_prompt(self, zone: Zone, ignore_rules: List) -> str:
        """Build analysis prompt with zone-specific instructions and ignore rules"""
        base_prompt = f"""
        Analyze the provided image of a room ({zone.display_name}) and perform the following tasks:
        
        1. Rate the overall cleanliness of the room on a scale of 1 to 100, where 1 is extremely messy and 100 is perfectly clean.
        2. Identify specific, actionable tasks that would improve the room's cleanliness. The tasks should be clear and concise.
        3. For each task, provide a confidence score (0.0 to 1.0) indicating how certain you are about the task.
        
        IMPORTANT IGNORE RULES - Do NOT include tasks related to these items:
        """
        
        # Add ignore rules to prompt
        if ignore_rules:
            for rule in ignore_rules:
                if rule.rule_type.value == 'object':
                    base_prompt += f"\n- Ignore any tasks related to: {rule.rule_value}"
                elif rule.rule_type.value == 'area':
                    base_prompt += f"\n- Ignore the area: {rule.rule_value}"
                elif rule.rule_type.value == 'keyword':
                    base_prompt += f"\n- Ignore tasks containing the word: {rule.rule_value}"
        else:
            base_prompt += "\n- No specific ignore rules for this zone"
        
        base_prompt += f"""
        
        Additional guidelines:
        - Focus on tasks that can be completed in under 15 minutes
        - Prioritize safety and hygiene issues
        - Be specific about locations (e.g., "on the floor", "on the counter")
        - Maximum {zone.max_tasks_per_analysis} tasks
        
        Return the output ONLY in a valid JSON format with these keys:
        - "score": An integer representing the cleanliness score (1-100)
        - "tasks": A list of strings, where each string is a cleaning task
        - "confidence_scores": A list of floats (0.0-1.0) corresponding to each task
        
        Example:
        {{
          "score": 75,
          "tasks": [
            "Pick up the clothes from the floor",
            "Make the bed",
            "Wipe down the dusty shelves"
          ],
          "confidence_scores": [0.9, 0.8, 0.7]
        }}
        """
        
        return base_prompt
    
    def _parse_gemini_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse JSON response from Gemini"""
        try:
            # Clean up the response text
            cleaned_text = response_text.strip()
            
            # Remove markdown code block fences if present
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith('```'):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]
            
            cleaned_text = cleaned_text.strip()
            
            # Parse JSON
            data = json.loads(cleaned_text)
            
            # Validate required fields
            if "score" not in data or "tasks" not in data:
                self.logger.error("Gemini response missing required fields")
                return None
            
            # Ensure confidence scores match tasks
            tasks = data["tasks"]
            confidence_scores = data.get("confidence_scores", [])
            
            if len(confidence_scores) != len(tasks):
                # Fill missing confidence scores with default value
                confidence_scores = confidence_scores[:len(tasks)]  # Truncate if too many
                while len(confidence_scores) < len(tasks):
                    confidence_scores.append(0.8)  # Default confidence
                data["confidence_scores"] = confidence_scores
            
            self.logger.info(f"Successfully parsed Gemini response: score={data['score']}, tasks={len(tasks)}")
            return data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse Gemini JSON response: {e}")
            self.logger.error(f"Raw response: {response_text}")
            return None
        except Exception as e:
            self.logger.error(f"Error processing Gemini response: {e}")
            return None
    
    def _apply_ignore_rules(self, tasks: List[str], ignore_rules: List) -> List[str]:
        """Apply ignore rules to filter out unwanted tasks"""
        if not ignore_rules:
            return tasks
        
        filtered_tasks = []
        
        for task in tasks:
            should_ignore = False
            
            for rule in ignore_rules:
                if rule.matches(task):
                    should_ignore = True
                    # Update rule usage statistics
                    self.ignore_rule_repo.update_usage(rule.id)
                    self.logger.debug(f"Task '{task}' ignored by rule: {rule.rule_description or rule.rule_value}")
                    break
            
            if not should_ignore:
                filtered_tasks.append(task)
        
        if len(filtered_tasks) != len(tasks):
            self.logger.info(f"Filtered {len(tasks) - len(filtered_tasks)} tasks using ignore rules")
        
        return filtered_tasks
    
    def test_zone_analysis(self, zone: Zone, test_image_path: str) -> Dict[str, Any]:
        """Test analysis for a zone with a specific image (for debugging)"""
        try:
            result = self.analyze_zone_image(zone, test_image_path)
            
            return {
                'zone_id': zone.id,
                'zone_name': zone.name,
                'success': result.error_message is None,
                'cleanliness_score': result.cleanliness_score,
                'task_count': len(result.tasks),
                'tasks': result.tasks,
                'confidence_scores': result.confidence_scores,
                'analysis_duration': result.analysis_duration,
                'tokens_used': result.tokens_used,
                'error_message': result.error_message
            }
            
        except Exception as e:
            return {
                'zone_id': zone.id,
                'zone_name': zone.name,
                'success': False,
                'error_message': str(e)
            }
