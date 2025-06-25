"""
Prompt Engineer - Advanced prompt generation and optimization for AI analysis
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

from ..data.models import PersonalityMode


class PromptType(Enum):
    """Types of analysis prompts"""
    OVERVIEW = "overview"
    DETAILED = "detailed"
    CONTEXTUAL = "contextual"
    SINGLE_PASS = "single_pass"
    VALIDATION = "validation"


class PromptComplexity(Enum):
    """Prompt complexity levels"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXPERT = "expert"


class PromptEngineer:
    """Advanced prompt engineering for optimal AI analysis results"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Prompt templates and components
        self.base_templates = self._initialize_base_templates()
        self.personality_modifiers = self._initialize_personality_modifiers()
        self.room_specific_contexts = self._initialize_room_contexts()
        self.analysis_techniques = self._initialize_analysis_techniques()
        
        # Prompt optimization settings
        self.optimization_config = {
            'use_chain_of_thought': True,
            'include_examples': True,
            'use_structured_output': True,
            'adaptive_complexity': True,
            'context_aware_prompting': True
        }
        
        self.logger.info("Prompt Engineer initialized")
    
    def _initialize_base_templates(self) -> Dict[str, str]:
        """Initialize base prompt templates"""
        return {
            'overview': """
            You are an expert home organization assistant analyzing a {room_type} for cleaning and organization tasks.
            
            {context_section}
            
            Analyze this image and provide:
            1. Overall cleanliness assessment (0-100 scale)
            2. Major areas requiring attention
            3. Most obvious cleaning/organization tasks
            4. General room condition evaluation
            
            {personality_instruction}
            
            {output_format}
            """,
            
            'detailed': """
            You are conducting a detailed cleaning analysis of a {room_type}.
            
            {context_section}
            
            {previous_analysis}
            
            Perform a thorough examination focusing on:
            1. Specific cleaning tasks with precise descriptions
            2. Location coordinates for each task (as percentages of image dimensions)
            3. Priority levels based on urgency and impact
            4. Confidence scores for each identified task
            5. Task categorization (surface, floor, storage, maintenance)
            
            {analysis_guidelines}
            
            {output_format}
            """,
            
            'contextual': """
            You are refining and optimizing a cleaning task analysis for a {room_type}.
            
            {context_section}
            
            {previous_results}
            
            Your role is to:
            1. Eliminate duplicate or redundant tasks
            2. Adjust priorities based on room-specific importance
            3. Add any critical tasks that were missed
            4. Validate task relevance and feasibility
            5. Optimize task descriptions for clarity
            
            {refinement_criteria}
            
            {output_format}
            """,
            
            'single_pass': """
            You are performing a comprehensive single-pass analysis of a {room_type}.
            
            {context_section}
            
            Conduct a complete analysis including:
            1. Overall assessment and cleanliness scoring
            2. Comprehensive task identification
            3. Priority assignment and confidence scoring
            4. Location estimation for visual overlay
            5. Task categorization and organization
            
            {analysis_strategy}
            
            {output_format}
            """
        }
    
    def _initialize_personality_modifiers(self) -> Dict[PersonalityMode, Dict[str, str]]:
        """Initialize personality-specific prompt modifiers"""
        return {
            PersonalityMode.CONCISE: {
                'instruction': "Provide direct, factual analysis without unnecessary elaboration.",
                'tone': "professional and efficient",
                'task_style': "Clear, actionable task descriptions",
                'examples': "Example: 'Put books back on shelf' rather than 'Organize the scattered books'"
            },
            
            PersonalityMode.SNARKY: {
                'instruction': "Add subtle humor and wit to your analysis while remaining helpful.",
                'tone': "clever and slightly sarcastic but constructive",
                'task_style': "Witty but clear task descriptions",
                'examples': "Example: 'Rescue those poor socks from floor exile' rather than 'Pick up socks'"
            },
            
            PersonalityMode.ENCOURAGING: {
                'instruction': "Provide positive, motivating analysis that encourages action.",
                'tone': "supportive and uplifting",
                'task_style': "Encouraging, achievement-focused task descriptions",
                'examples': "Example: 'Create a beautiful, organized space by arranging these items' rather than 'Clean up mess'"
            }
        }
    
    def _initialize_room_contexts(self) -> Dict[str, Dict[str, Any]]:
        """Initialize room-specific context information"""
        return {
            'living_room': {
                'focus_areas': ['seating areas', 'entertainment center', 'coffee table', 'floor space'],
                'common_items': ['remote controls', 'throw pillows', 'blankets', 'books', 'magazines'],
                'priority_tasks': ['surface clearing', 'furniture arrangement', 'floor cleaning'],
                'ignore_hints': ['decorative items', 'furniture', 'electronics', 'artwork']
            },
            
            'kitchen': {
                'focus_areas': ['countertops', 'sink area', 'stovetop', 'dining table'],
                'common_items': ['dishes', 'utensils', 'appliances', 'food items', 'cleaning supplies'],
                'priority_tasks': ['dish management', 'counter clearing', 'appliance cleaning'],
                'ignore_hints': ['permanent appliances', 'cabinets', 'fixtures']
            },
            
            'bedroom': {
                'focus_areas': ['bed area', 'dresser', 'nightstands', 'floor', 'closet area'],
                'common_items': ['clothing', 'bedding', 'personal items', 'shoes'],
                'priority_tasks': ['bed making', 'clothing organization', 'surface clearing'],
                'ignore_hints': ['furniture', 'decor', 'electronics', 'permanent fixtures']
            },
            
            'bathroom': {
                'focus_areas': ['counter/vanity', 'shower/tub area', 'toilet area', 'floor'],
                'common_items': ['toiletries', 'towels', 'personal care items', 'cleaning supplies'],
                'priority_tasks': ['toiletry organization', 'towel arrangement', 'surface cleaning'],
                'ignore_hints': ['fixtures', 'permanent installations', 'built-in storage']
            },
            
            'office': {
                'focus_areas': ['desk surface', 'computer area', 'filing area', 'seating'],
                'common_items': ['papers', 'office supplies', 'electronics', 'books'],
                'priority_tasks': ['desk organization', 'paper management', 'supply organization'],
                'ignore_hints': ['computer equipment', 'office furniture', 'permanent installations']
            }
        }
    
    def _initialize_analysis_techniques(self) -> Dict[str, str]:
        """Initialize analysis technique descriptions"""
        return {
            'systematic_scan': "Scan the image systematically from left to right, top to bottom",
            'priority_focus': "Focus first on high-impact areas that affect overall room appearance",
            'category_grouping': "Group similar tasks together for efficient completion",
            'visual_hierarchy': "Identify tasks based on visual prominence and accessibility",
            'functional_analysis': "Consider how each area is used and what organization would be most functional"
        }
    
    def generate_prompt(self, prompt_type: PromptType, room_type: str, 
                       personality: PersonalityMode, context: Dict[str, Any] = None,
                       complexity: PromptComplexity = PromptComplexity.MODERATE) -> str:
        """Generate optimized prompt for specific analysis type"""
        
        # Get base template
        template = self.base_templates.get(prompt_type.value, "")
        if not template:
            raise ValueError(f"Unknown prompt type: {prompt_type}")
        
        # Build context section
        context_section = self._build_context_section(room_type, context or {})
        
        # Get personality modifiers
        personality_info = self.personality_modifiers.get(personality, {})
        personality_instruction = personality_info.get('instruction', '')
        
        # Build analysis guidelines
        analysis_guidelines = self._build_analysis_guidelines(room_type, complexity)
        
        # Build output format specification
        output_format = self._build_output_format(prompt_type, complexity)
        
        # Handle prompt-specific sections
        additional_sections = self._build_additional_sections(prompt_type, context or {})
        
        # Assemble final prompt
        prompt = template.format(
            room_type=room_type,
            context_section=context_section,
            personality_instruction=personality_instruction,
            analysis_guidelines=analysis_guidelines,
            output_format=output_format,
            **additional_sections
        )
        
        # Apply optimizations
        if self.optimization_config['use_chain_of_thought']:
            prompt = self._add_chain_of_thought(prompt, complexity)
        
        if self.optimization_config['include_examples']:
            prompt = self._add_examples(prompt, prompt_type, personality)
        
        return prompt.strip()
    
    def _build_context_section(self, room_type: str, context: Dict[str, Any]) -> str:
        """Build context section for the prompt"""
        sections = []
        
        # Room-specific context
        room_context = self.room_specific_contexts.get(room_type, {})
        if room_context:
            sections.append(f"Room Type: {room_type.replace('_', ' ').title()}")
            sections.append(f"Focus Areas: {', '.join(room_context.get('focus_areas', []))}")
            sections.append(f"Common Items: {', '.join(room_context.get('common_items', []))}")
        
        # Zone-specific context
        if 'cleanliness_threshold' in context:
            sections.append(f"Cleanliness Target: {context['cleanliness_threshold']}/100")
        
        if 'recent_task_patterns' in context:
            patterns = context['recent_task_patterns']
            if patterns.get('common_keywords'):
                sections.append(f"Recent Task Patterns: {', '.join(patterns['common_keywords'][:3])}")
        
        if 'common_tasks' in context:
            common_tasks = context['common_tasks'][:5]
            sections.append(f"Typical Tasks for This Room: {', '.join(common_tasks)}")
        
        return '\n'.join(sections) if sections else "Standard room analysis requested."
    
    def _build_analysis_guidelines(self, room_type: str, complexity: PromptComplexity) -> str:
        """Build analysis guidelines based on room type and complexity"""
        guidelines = []
        
        # Room-specific guidelines
        room_context = self.room_specific_contexts.get(room_type, {})
        priority_tasks = room_context.get('priority_tasks', [])
        if priority_tasks:
            guidelines.append(f"Priority Focus: {', '.join(priority_tasks)}")
        
        ignore_hints = room_context.get('ignore_hints', [])
        if ignore_hints:
            guidelines.append(f"Typically Ignore: {', '.join(ignore_hints)}")
        
        # Complexity-based guidelines
        if complexity in [PromptComplexity.COMPLEX, PromptComplexity.EXPERT]:
            guidelines.extend([
                "Use systematic scanning approach",
                "Consider functional workflow optimization",
                "Assess visual impact of each task",
                "Evaluate task interdependencies"
            ])
        
        return '\n'.join(f"- {guideline}" for guideline in guidelines)
    
    def _build_output_format(self, prompt_type: PromptType, complexity: PromptComplexity) -> str:
        """Build output format specification"""
        if not self.optimization_config['use_structured_output']:
            return "Provide your analysis in clear, organized text."
        
        # Base JSON structure
        base_structure = {
            PromptType.OVERVIEW: {
                "overall_cleanliness": "0-100",
                "major_areas": ["area1", "area2"],
                "obvious_tasks": [
                    {"description": "task", "priority": "high|medium|low", "confidence": "0.0-1.0"}
                ],
                "room_condition": "excellent|good|fair|poor"
            },
            
            PromptType.DETAILED: {
                "detailed_tasks": [
                    {
                        "description": "specific task description",
                        "location": {"x": "0.0-1.0", "y": "0.0-1.0"},
                        "priority": "high|medium|low",
                        "confidence": "0.0-1.0",
                        "category": "surface|floor|storage|maintenance"
                    }
                ],
                "analysis_confidence": "0.0-1.0"
            },
            
            PromptType.CONTEXTUAL: {
                "refined_tasks": [
                    {
                        "description": "refined task description",
                        "location": {"x": "0.0-1.0", "y": "0.0-1.0"},
                        "priority": "high|medium|low",
                        "confidence": "0.0-1.0",
                        "refinement_reason": "why this task was refined/added"
                    }
                ],
                "removed_tasks": ["task descriptions that were removed"],
                "refinement_confidence": "0.0-1.0"
            },
            
            PromptType.SINGLE_PASS: {
                "tasks": [
                    {
                        "description": "specific cleaning task",
                        "location": {"x": "0.0-1.0", "y": "0.0-1.0"},
                        "priority": "high|medium|low",
                        "confidence": "0.0-1.0",
                        "category": "surface|floor|storage|maintenance"
                    }
                ],
                "overall_assessment": {
                    "cleanliness_score": "0-100",
                    "task_count": "number",
                    "analysis_confidence": "0.0-1.0"
                }
            }
        }
        
        structure = base_structure.get(prompt_type, {})
        
        if complexity == PromptComplexity.EXPERT:
            # Add additional fields for expert analysis
            if "tasks" in structure or "detailed_tasks" in structure:
                task_key = "tasks" if "tasks" in structure else "detailed_tasks"
                if structure[task_key] and isinstance(structure[task_key][0], dict):
                    structure[task_key][0].update({
                        "estimated_time_minutes": "number",
                        "difficulty": "easy|medium|hard",
                        "tools_needed": ["tool1", "tool2"]
                    })
        
        import json
        formatted_json = json.dumps(structure, indent=2)
        
        return f"Respond in JSON format:\n{formatted_json}"
    
    def _build_additional_sections(self, prompt_type: PromptType, context: Dict[str, Any]) -> Dict[str, str]:
        """Build additional sections specific to prompt type"""
        sections = {}
        
        if prompt_type == PromptType.DETAILED:
            sections['previous_analysis'] = self._format_previous_analysis(context.get('previous_analysis', {}))
        
        elif prompt_type == PromptType.CONTEXTUAL:
            sections['previous_results'] = self._format_previous_results(context.get('previous_results', []))
            sections['refinement_criteria'] = self._build_refinement_criteria(context)
        
        elif prompt_type == PromptType.SINGLE_PASS:
            sections['analysis_strategy'] = self._build_analysis_strategy(context)
        
        return sections
    
    def _format_previous_analysis(self, previous_analysis: Dict[str, Any]) -> str:
        """Format previous analysis results for context"""
        if not previous_analysis:
            return "No previous analysis available."
        
        sections = []
        if 'overall_cleanliness' in previous_analysis:
            sections.append(f"Previous Overall Score: {previous_analysis['overall_cleanliness']}/100")
        
        if 'major_areas' in previous_analysis:
            sections.append(f"Previously Identified Areas: {', '.join(previous_analysis['major_areas'])}")
        
        return '\n'.join(sections) if sections else "Previous analysis data available."
    
    def _format_previous_results(self, previous_results: List[Dict[str, Any]]) -> str:
        """Format previous results for contextual analysis"""
        if not previous_results:
            return "No previous results to refine."
        
        all_tasks = []
        for result in previous_results:
            if 'tasks' in result:
                all_tasks.extend([task.get('description', '') for task in result['tasks']])
        
        if all_tasks:
            return f"Previously Identified Tasks:\n" + '\n'.join(f"- {task}" for task in all_tasks[:8])
        
        return "Previous analysis results available for refinement."
    
    def _build_refinement_criteria(self, context: Dict[str, Any]) -> str:
        """Build refinement criteria for contextual analysis"""
        criteria = [
            "Remove tasks that are too vague or unclear",
            "Combine similar tasks into single, comprehensive actions",
            "Prioritize tasks based on visual impact and effort required",
            "Ensure task descriptions are actionable and specific"
        ]
        
        if context.get('personality_mode') == PersonalityMode.CONCISE:
            criteria.append("Keep descriptions brief and direct")
        elif context.get('personality_mode') == PersonalityMode.ENCOURAGING:
            criteria.append("Frame tasks positively and motivationally")
        
        return '\n'.join(f"- {criterion}" for criterion in criteria)
    
    def _build_analysis_strategy(self, context: Dict[str, Any]) -> str:
        """Build analysis strategy for single-pass analysis"""
        strategies = [
            "Systematic visual scanning of the entire space",
            "Priority-based task identification (high impact first)",
            "Confidence-based filtering of uncertain observations",
            "Location-aware task positioning for visual overlay"
        ]
        
        return '\n'.join(f"- {strategy}" for strategy in strategies)
    
    def _add_chain_of_thought(self, prompt: str, complexity: PromptComplexity) -> str:
        """Add chain-of-thought reasoning to prompt"""
        if complexity in [PromptComplexity.SIMPLE, PromptComplexity.MODERATE]:
            return prompt
        
        cot_instruction = """
        
        Think through this step-by-step:
        1. First, observe the overall state of the room
        2. Identify the most obvious issues or tasks
        3. Consider the functional use of the space
        4. Prioritize tasks based on impact and effort
        5. Provide your final analysis
        """
        
        return prompt + cot_instruction
    
    def _add_examples(self, prompt: str, prompt_type: PromptType, personality: PersonalityMode) -> str:
        """Add relevant examples to the prompt"""
        if not self.optimization_config['include_examples']:
            return prompt
        
        personality_info = self.personality_modifiers.get(personality, {})
        examples = personality_info.get('examples', '')
        
        if examples:
            example_section = f"\n\nStyle Examples:\n{examples}"
            return prompt + example_section
        
        return prompt
    
    def optimize_prompt_for_model(self, prompt: str, model_type: str) -> str:
        """Optimize prompt for specific AI model"""
        # Model-specific optimizations
        if 'gemini' in model_type.lower():
            # Gemini works well with structured prompts
            return prompt
        elif 'gpt' in model_type.lower():
            # GPT models prefer more conversational tone
            prompt = prompt.replace("You are an expert", "As an expert")
            prompt = prompt.replace("Analyze this image", "Please analyze this image")
        
        return prompt
