"""
Advanced AI Analyzer - Enhanced image analysis with multiple AI models and techniques
"""
import logging
import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
import base64

from .gemini_client import GeminiClient
from .model_manager import AIModelManager, ModelType
from .prompt_engineer import PromptEngineer, PromptType, PromptComplexity
from ..data.models import Task, IgnoreRule, PersonalityMode
from ..data.repositories import TaskRepository, IgnoreRuleRepository


class AdvancedAnalyzer:
    """Advanced AI analyzer with multiple analysis techniques"""
    
    def __init__(self, model_manager: AIModelManager, task_repo: TaskRepository,
                 ignore_repo: IgnoreRuleRepository):
        self.logger = logging.getLogger(__name__)
        self.model_manager = model_manager
        self.prompt_engineer = PromptEngineer()
        self.task_repo = task_repo
        self.ignore_repo = ignore_repo
        
        # Analysis configuration
        self.config = {
            'multi_pass_analysis': True,
            'confidence_threshold': 0.7,
            'max_tasks_per_analysis': 10,
            'enable_visual_overlay': True,
            'use_context_awareness': True,
            'enable_progressive_analysis': True
        }
        
        # Analysis models and techniques
        self.analysis_techniques = [
            'detailed_scan',
            'contextual_analysis',
            'priority_assessment',
            'confidence_scoring'
        ]
        
        self.logger.info("Advanced analyzer initialized")
    
    async def analyze_image_advanced(self, image_data: bytes, zone_id: int, 
                                   zone_config: Dict[str, Any]) -> Dict[str, Any]:
        """Perform advanced multi-pass image analysis"""
        analysis_start = time.time()
        
        try:
            # Load and preprocess image
            image = Image.open(io.BytesIO(image_data))
            preprocessed_image = self._preprocess_image(image, zone_config)
            
            # Get zone context
            zone_context = await self._build_zone_context(zone_id, zone_config)
            
            # Perform multi-pass analysis
            analysis_results = []
            
            if self.config['multi_pass_analysis']:
                # Pass 1: General overview
                overview_result = await self._analyze_overview(preprocessed_image, zone_context)
                analysis_results.append(overview_result)
                
                # Pass 2: Detailed scan
                detailed_result = await self._analyze_detailed(preprocessed_image, zone_context, overview_result)
                analysis_results.append(detailed_result)
                
                # Pass 3: Context-aware refinement
                if self.config['use_context_awareness']:
                    refined_result = await self._analyze_contextual(preprocessed_image, zone_context, analysis_results)
                    analysis_results.append(refined_result)
            else:
                # Single pass analysis
                single_result = await self._analyze_single_pass(preprocessed_image, zone_context)
                analysis_results.append(single_result)
            
            # Consolidate results
            consolidated_tasks = self._consolidate_analysis_results(analysis_results, zone_config)
            
            # Apply ignore rules
            filtered_tasks = await self._apply_ignore_rules(consolidated_tasks, zone_id)
            
            # Score and prioritize tasks
            scored_tasks = self._score_and_prioritize_tasks(filtered_tasks, zone_context)
            
            # Limit task count
            final_tasks = self._limit_task_count(scored_tasks, zone_config.get('max_tasks_per_analysis', 10))
            
            # Generate visual overlay if enabled
            overlay_image = None
            if self.config['enable_visual_overlay']:
                overlay_image = self._generate_visual_overlay(image, final_tasks)
            
            analysis_duration = time.time() - analysis_start
            
            return {
                'success': True,
                'tasks': final_tasks,
                'analysis_metadata': {
                    'duration_seconds': analysis_duration,
                    'passes_completed': len(analysis_results),
                    'total_tasks_found': len(consolidated_tasks),
                    'tasks_after_filtering': len(filtered_tasks),
                    'final_task_count': len(final_tasks),
                    'techniques_used': self.analysis_techniques,
                    'confidence_threshold': self.config['confidence_threshold']
                },
                'visual_overlay': overlay_image,
                'zone_context': zone_context
            }
            
        except Exception as e:
            self.logger.error(f"Advanced analysis failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'tasks': [],
                'analysis_metadata': {
                    'duration_seconds': time.time() - analysis_start,
                    'error_occurred': True
                }
            }
    
    def _preprocess_image(self, image: Image.Image, zone_config: Dict[str, Any]) -> Image.Image:
        """Preprocess image for optimal analysis"""
        # Resize if too large
        max_size = 1920
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Enhance contrast if needed
        sensitivity = zone_config.get('optimal_settings', {}).get('analysis_sensitivity', 'medium')
        if sensitivity == 'high':
            # Apply slight contrast enhancement for high sensitivity
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.1)
        
        return image
    
    async def _build_zone_context(self, zone_id: int, zone_config: Dict[str, Any]) -> Dict[str, Any]:
        """Build contextual information about the zone"""
        # Get recent task history (placeholder - would need to implement this method)
        recent_tasks = []  # self.task_repo.get_recent_tasks(zone_id, limit=20)

        # Get ignore rules (placeholder - would need to implement this method)
        ignore_rules = []  # self.ignore_repo.get_ignore_rules(zone_id)
        
        # Analyze task patterns
        task_patterns = self._analyze_task_patterns(recent_tasks)
        
        return {
            'zone_id': zone_id,
            'zone_name': zone_config.get('display_name', 'Unknown Zone'),
            'personality_mode': zone_config.get('personality_mode', 'concise'),
            'cleanliness_threshold': zone_config.get('cleanliness_threshold', 75),
            'recent_task_count': len(recent_tasks),
            'ignore_rule_count': len(ignore_rules),
            'task_patterns': task_patterns,
            'optimal_settings': zone_config.get('optimal_settings', {}),
            'common_tasks': zone_config.get('common_tasks', [])
        }
    
    def _analyze_task_patterns(self, recent_tasks: List[Task]) -> Dict[str, Any]:
        """Analyze patterns in recent tasks"""
        if not recent_tasks:
            return {'pattern_confidence': 0.0}
        
        # Analyze task frequency
        task_descriptions = [task.description for task in recent_tasks]
        task_frequency = {}
        
        for description in task_descriptions:
            # Simple keyword extraction
            keywords = description.lower().split()
            for keyword in keywords:
                if len(keyword) > 3:  # Skip short words
                    task_frequency[keyword] = task_frequency.get(keyword, 0) + 1
        
        # Find most common patterns
        common_patterns = sorted(task_frequency.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'pattern_confidence': min(len(recent_tasks) / 10.0, 1.0),
            'common_keywords': [pattern[0] for pattern in common_patterns],
            'task_frequency': dict(common_patterns),
            'total_recent_tasks': len(recent_tasks)
        }
    
    async def _analyze_overview(self, image: Image.Image, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform overview analysis pass"""
        # Generate optimized prompt
        room_type = context.get('zone_name', 'room').lower().replace(' ', '_')
        personality = context.get('personality_mode', PersonalityMode.CONCISE)

        prompt = self.prompt_engineer.generate_prompt(
            PromptType.OVERVIEW,
            room_type,
            personality,
            context,
            PromptComplexity.MODERATE
        )

        # Use model manager for analysis
        result = await self.model_manager.analyze_with_best_model(image, prompt)

        if result.get('success'):
            return self._parse_analysis_response(result['response'], 'overview')
        else:
            return {
                'success': False,
                'analysis_type': 'overview',
                'error': result.get('error', 'Analysis failed')
            }
    
    async def _analyze_detailed(self, image: Image.Image, context: Dict[str, Any],
                               overview: Dict[str, Any]) -> Dict[str, Any]:
        """Perform detailed analysis pass"""
        # Add previous analysis to context
        detailed_context = context.copy()
        detailed_context['previous_analysis'] = overview.get('data', {})

        # Generate optimized prompt
        room_type = context.get('zone_name', 'room').lower().replace(' ', '_')
        personality = context.get('personality_mode', PersonalityMode.CONCISE)

        prompt = self.prompt_engineer.generate_prompt(
            PromptType.DETAILED,
            room_type,
            personality,
            detailed_context,
            PromptComplexity.COMPLEX
        )

        # Use model manager for analysis
        result = await self.model_manager.analyze_with_best_model(image, prompt)

        if result.get('success'):
            return self._parse_analysis_response(result['response'], 'detailed')
        else:
            return {
                'success': False,
                'analysis_type': 'detailed',
                'error': result.get('error', 'Analysis failed')
            }
    
    async def _analyze_contextual(self, image: Image.Image, context: Dict[str, Any], 
                                 previous_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform context-aware refinement analysis"""
        # Combine previous results
        all_tasks = []
        for result in previous_results:
            if result.get('success') and 'data' in result:
                data = result['data']
                if 'obvious_tasks' in data:
                    all_tasks.extend(data['obvious_tasks'])
                if 'detailed_tasks' in data:
                    all_tasks.extend(data['detailed_tasks'])
        
        prompt = f"""
        Refine and validate the cleaning task analysis for this {context['zone_name']}.
        
        Previously identified tasks:
        {[task.get('description', '') for task in all_tasks[:8]]}
        
        Zone-specific considerations:
        - Personality mode: {context['personality_mode']}
        - Optimal settings: {context.get('optimal_settings', {})}
        - Ignore patterns: Items that should typically be ignored in this room
        
        Refine the task list by:
        1. Removing duplicate or similar tasks
        2. Adjusting priorities based on room type
        3. Adding any missed important tasks
        4. Validating task relevance
        
        Respond in JSON format:
        {{
            "refined_tasks": [
                {{
                    "description": "refined task description",
                    "location": {{"x": 0.0-1.0, "y": 0.0-1.0}},
                    "priority": "high|medium|low",
                    "confidence": 0.0-1.0,
                    "refinement_reason": "why this task was refined/added"
                }}
            ],
            "removed_tasks": ["task descriptions that were removed"],
            "refinement_confidence": 0.0-1.0
        }}
        """
        
        response = await self.gemini.analyze_image_with_prompt(image, prompt)
        return self._parse_analysis_response(response, 'contextual')
    
    async def _analyze_single_pass(self, image: Image.Image, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform single-pass comprehensive analysis"""
        prompt = f"""
        Analyze this {context['zone_name']} image for cleaning tasks in a single comprehensive pass.
        
        Zone Context:
        - Room: {context['zone_name']}
        - Cleanliness threshold: {context['cleanliness_threshold']}/100
        - Personality: {context['personality_mode']}
        - Common tasks: {context.get('common_tasks', [])[:5]}
        
        Identify cleaning tasks with:
        1. Specific descriptions
        2. Priority levels
        3. Confidence scores
        4. Location estimates
        
        Respond in JSON format:
        {{
            "tasks": [
                {{
                    "description": "specific cleaning task",
                    "location": {{"x": 0.0-1.0, "y": 0.0-1.0}},
                    "priority": "high|medium|low",
                    "confidence": 0.0-1.0,
                    "category": "surface|floor|storage|maintenance"
                }}
            ],
            "overall_assessment": {{
                "cleanliness_score": 0-100,
                "task_count": 0,
                "analysis_confidence": 0.0-1.0
            }}
        }}
        """
        
        response = await self.gemini.analyze_image_with_prompt(image, prompt)
        return self._parse_analysis_response(response, 'single_pass')
    
    def _parse_analysis_response(self, response: str, analysis_type: str) -> Dict[str, Any]:
        """Parse and validate analysis response"""
        try:
            import json
            
            # Clean up response (remove markdown formatting if present)
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            
            data = json.loads(cleaned_response)
            
            return {
                'success': True,
                'analysis_type': analysis_type,
                'data': data,
                'raw_response': response
            }
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse {analysis_type} analysis response: {e}")
            return {
                'success': False,
                'analysis_type': analysis_type,
                'error': f"JSON parsing failed: {e}",
                'raw_response': response
            }
    
    def _consolidate_analysis_results(self, results: List[Dict[str, Any]], 
                                    zone_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Consolidate multiple analysis results into unified task list"""
        all_tasks = []
        
        for result in results:
            if not result.get('success'):
                continue
            
            data = result.get('data', {})
            analysis_type = result.get('analysis_type', 'unknown')
            
            # Extract tasks based on analysis type
            if analysis_type == 'overview':
                tasks = data.get('obvious_tasks', [])
            elif analysis_type == 'detailed':
                tasks = data.get('detailed_tasks', [])
            elif analysis_type == 'contextual':
                tasks = data.get('refined_tasks', [])
            elif analysis_type == 'single_pass':
                tasks = data.get('tasks', [])
            else:
                continue
            
            # Add source information
            for task in tasks:
                task['analysis_source'] = analysis_type
                all_tasks.append(task)
        
        # Remove duplicates and merge similar tasks
        consolidated_tasks = self._deduplicate_tasks(all_tasks)
        
        return consolidated_tasks
    
    def _deduplicate_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate and very similar tasks"""
        if not tasks:
            return []
        
        unique_tasks = []
        
        for task in tasks:
            description = task.get('description', '').lower()
            is_duplicate = False
            
            for existing_task in unique_tasks:
                existing_desc = existing_task.get('description', '').lower()
                
                # Simple similarity check
                if self._calculate_similarity(description, existing_desc) > 0.8:
                    # Merge tasks - keep the one with higher confidence
                    if task.get('confidence', 0) > existing_task.get('confidence', 0):
                        unique_tasks.remove(existing_task)
                        unique_tasks.append(task)
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_tasks.append(task)
        
        return unique_tasks
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings"""
        # Simple word-based similarity
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    async def _apply_ignore_rules(self, tasks: List[Dict[str, Any]], zone_id: int) -> List[Dict[str, Any]]:
        """Apply ignore rules to filter out unwanted tasks"""
        # Placeholder - would need to implement get_ignore_rules method
        ignore_rules = []  # self.ignore_repo.get_ignore_rules(zone_id)

        if not ignore_rules:
            return tasks
        
        filtered_tasks = []
        
        for task in tasks:
            description = task.get('description', '').lower()
            should_ignore = False
            
            for rule in ignore_rules:
                if self._task_matches_ignore_rule(description, rule):
                    should_ignore = True
                    break
            
            if not should_ignore:
                filtered_tasks.append(task)
        
        return filtered_tasks
    
    def _task_matches_ignore_rule(self, task_description: str, rule: IgnoreRule) -> bool:
        """Check if a task matches an ignore rule"""
        rule_value = rule.rule_value.lower()
        
        if rule.rule_type == 'contains':
            return rule_value in task_description
        elif rule.rule_type == 'starts_with':
            return task_description.startswith(rule_value)
        elif rule.rule_type == 'ends_with':
            return task_description.endswith(rule_value)
        elif rule.rule_type == 'exact':
            return task_description == rule_value
        elif rule.rule_type == 'regex':
            import re
            try:
                return bool(re.search(rule_value, task_description))
            except re.error:
                return False
        
        return False
    
    def _score_and_prioritize_tasks(self, tasks: List[Dict[str, Any]], 
                                  context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Score and prioritize tasks based on various factors"""
        priority_weights = context.get('optimal_settings', {}).get('task_priority_weights', {})
        
        for task in tasks:
            score = 0.0
            
            # Base confidence score
            confidence = task.get('confidence', 0.5)
            score += confidence * 0.4
            
            # Priority level score
            priority = task.get('priority', 'medium')
            priority_scores = {'high': 1.0, 'medium': 0.6, 'low': 0.3}
            score += priority_scores.get(priority, 0.6) * 0.3
            
            # Category-based scoring
            category = task.get('category', 'general')
            category_weight = priority_weights.get(category, 0.5)
            score += category_weight * 0.3
            
            task['calculated_score'] = score
        
        # Sort by score (highest first)
        return sorted(tasks, key=lambda x: x.get('calculated_score', 0), reverse=True)
    
    def _limit_task_count(self, tasks: List[Dict[str, Any]], max_tasks: int) -> List[Dict[str, Any]]:
        """Limit the number of tasks to the specified maximum"""
        if len(tasks) <= max_tasks:
            return tasks
        
        # Take the highest scored tasks
        return tasks[:max_tasks]
    
    def _generate_visual_overlay(self, image: Image.Image, tasks: List[Dict[str, Any]]) -> Optional[str]:
        """Generate visual overlay showing task locations"""
        try:
            # Create a copy of the image
            overlay_image = image.copy()
            draw = ImageDraw.Draw(overlay_image)
            
            # Try to load a font
            try:
                font = ImageFont.truetype("arial.ttf", 16)
            except:
                font = ImageFont.load_default()
            
            # Draw task markers
            for i, task in enumerate(tasks):
                location = task.get('location', {})
                x = location.get('x', 0.5) * image.width
                y = location.get('y', 0.5) * image.height
                
                # Draw circle marker
                radius = 15
                priority = task.get('priority', 'medium')
                color = {'high': 'red', 'medium': 'orange', 'low': 'yellow'}.get(priority, 'blue')
                
                draw.ellipse([x-radius, y-radius, x+radius, y+radius], outline=color, width=3)
                
                # Draw task number
                draw.text((x-5, y-8), str(i+1), fill='white', font=font)
            
            # Convert to base64
            buffer = io.BytesIO()
            overlay_image.save(buffer, format='PNG')
            buffer.seek(0)
            
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
            
        except Exception as e:
            self.logger.error(f"Failed to generate visual overlay: {e}")
            return None
