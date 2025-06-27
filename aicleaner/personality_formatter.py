"""
PersonalityFormatter - Handles different notification personalities
Component-based design following TDD principles
"""

import logging
import random
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class PersonalityFormatter:
    """
    Formats messages according to different personality styles.
    
    This component is responsible for applying personality-specific formatting
    to notification messages, making them more engaging and personalized.
    """
    
    AVAILABLE_PERSONALITIES = [
        'default', 'snarky', 'jarvis', 'roaster', 'butler', 'coach', 'zen'
    ]
    
    def __init__(self, personality: str = 'default'):
        """
        Initialize the personality formatter.
        
        Args:
            personality: The personality style to use for formatting
        """
        self.personality = personality if personality in self.AVAILABLE_PERSONALITIES else 'default'
        logger.info(f"PersonalityFormatter initialized with personality: {self.personality}")
    
    def get_available_personalities(self) -> List[str]:
        """Get list of available personalities."""
        return self.AVAILABLE_PERSONALITIES.copy()
    
    def format_task_message(self, task_data: Dict[str, Any], base_message: str = None) -> str:
        """
        Format a task notification message with personality.
        
        Args:
            task_data: Dictionary containing task information
            base_message: Optional base message to enhance
            
        Returns:
            str: Formatted message with personality applied
        """
        if base_message is None:
            base_message = f"New task in {task_data.get('zone', 'unknown zone')}: {task_data.get('description', 'Unknown task')}"
        
        if self.personality == 'default':
            return self._format_default(base_message, task_data)
        elif self.personality == 'snarky':
            return self._format_snarky(base_message, task_data)
        elif self.personality == 'jarvis':
            return self._format_jarvis(base_message, task_data)
        elif self.personality == 'roaster':
            return self._format_roaster(base_message, task_data)
        elif self.personality == 'butler':
            return self._format_butler(base_message, task_data)
        elif self.personality == 'coach':
            return self._format_coach(base_message, task_data)
        elif self.personality == 'zen':
            return self._format_zen(base_message, task_data)
        else:
            return self._format_default(base_message, task_data)
    
    def format_analysis_message(self, analysis_data: Dict[str, Any], base_message: str) -> str:
        """
        Format an analysis complete message with personality.
        
        Args:
            analysis_data: Dictionary containing analysis results
            base_message: Base message to enhance
            
        Returns:
            str: Formatted message with personality applied
        """
        if self.personality == 'snarky':
            return f"Well, well... {base_message} Surprise, surprise! 🙄"
        elif self.personality == 'jarvis':
            return f"Analysis complete, sir. {base_message} Shall I proceed with the recommendations?"
        elif self.personality == 'roaster':
            return f"Yikes! {base_message} That's... quite the situation you've got there! 😬"
        elif self.personality == 'butler':
            return f"If I may report, {base_message} I do hope this information proves useful."
        elif self.personality == 'coach':
            return f"Alright team! {base_message} Time to crush these tasks! 💪"
        elif self.personality == 'zen':
            return f"In peaceful observation, {base_message} May this bring harmony to your space. 🧘"
        else:
            return f"📊 {base_message}"
    
    def format_system_message(self, status_data: Dict[str, Any], base_message: str) -> str:
        """
        Format a system status message with personality.
        
        Args:
            status_data: Dictionary containing system status
            base_message: Base message to enhance
            
        Returns:
            str: Formatted message with personality applied
        """
        if self.personality == 'snarky':
            return f"Oh look, a system update! {base_message} How thrilling... 🎉"
        elif self.personality == 'jarvis':
            return f"System status report: {base_message} All systems operational, sir."
        elif self.personality == 'roaster':
            return f"System check time! {base_message} Let's see how messy things have gotten! 😅"
        elif self.personality == 'butler':
            return f"Your humble system reports: {base_message} At your service as always."
        elif self.personality == 'coach':
            return f"System update! {base_message} Keep pushing forward, champion! 🏆"
        elif self.personality == 'zen':
            return f"System flows in balance: {base_message} All is as it should be. ☯️"
        else:
            return f"🏠 {base_message}"
    
    def format_test_message(self, message: str) -> str:
        """
        Format a test message with personality.
        
        Args:
            message: Test message to format
            
        Returns:
            str: Formatted test message
        """
        if self.personality == 'snarky':
            return f"Oh great, another test... {message} Hope you're happy! 😏"
        elif self.personality == 'jarvis':
            return f"Test protocol initiated. {message} Systems are functioning optimally, sir."
        elif self.personality == 'roaster':
            return f"Testing, testing... {message} Don't break anything! 😂"
        elif self.personality == 'butler':
            return f"Testing at your request: {message} I do hope everything is satisfactory."
        elif self.personality == 'coach':
            return f"Test time! {message} You've got this! 💪"
        elif self.personality == 'zen':
            return f"In mindful testing: {message} May all systems flow in harmony. 🕯️"
        else:
            return f"🧪 {message}"
    
    def _format_default(self, message: str, data: Dict[str, Any]) -> str:
        """Format message with default personality (professional)."""
        priority = data.get('priority', 'normal')
        priority_emoji = {'high': '🔴', 'normal': '🟡', 'low': '🟢'}.get(priority, '🟡')
        return f"{priority_emoji} {message}"
    
    def _format_snarky(self, message: str, data: Dict[str, Any]) -> str:
        """Format message with snarky personality."""
        snarky_prefixes = [
            "Oh look, another mess...",
            "Surprise, surprise!",
            "Well, well, well...",
            "Here we go again...",
            "Obviously someone needs to..."
        ]
        prefix = random.choice(snarky_prefixes)
        return f"{prefix} {message} 🙄"
    
    def _format_jarvis(self, message: str, data: Dict[str, Any]) -> str:
        """Format message with Jarvis personality (formal assistant)."""
        jarvis_prefixes = [
            "Sir, I must inform you that",
            "If I may suggest,",
            "Your attention is required for",
            "I recommend addressing",
            "Might I advise that"
        ]
        prefix = random.choice(jarvis_prefixes)
        return f"{prefix} {message.lower()}. Shall I assist further?"
    
    def _format_roaster(self, message: str, data: Dict[str, Any]) -> str:
        """Format message with roaster personality (playfully critical)."""
        roast_prefixes = [
            "Yikes! Looks like",
            "Oh no, not again!",
            "This is a disaster zone:",
            "Houston, we have a problem:",
            "Well this is embarrassing..."
        ]
        prefix = random.choice(roast_prefixes)
        return f"{prefix} {message} 😬"
    
    def _format_butler(self, message: str, data: Dict[str, Any]) -> str:
        """Format message with butler personality (polite and formal)."""
        butler_prefixes = [
            "If I may humbly suggest,",
            "Begging your pardon, but",
            "With the utmost respect,",
            "At your convenience, please",
            "I do hope you'll consider"
        ]
        prefix = random.choice(butler_prefixes)
        return f"{prefix} {message.lower()}. Thank you kindly."
    
    def _format_coach(self, message: str, data: Dict[str, Any]) -> str:
        """Format message with coach personality (motivational)."""
        coach_prefixes = [
            "Alright team, let's tackle this:",
            "You've got this!",
            "Time to crush it:",
            "Let's power through:",
            "Champion, it's time to"
        ]
        prefix = random.choice(coach_prefixes)
        return f"{prefix} {message} 💪 You're unstoppable!"
    
    def _format_zen(self, message: str, data: Dict[str, Any]) -> str:
        """Format message with zen personality (calm and mindful)."""
        zen_prefixes = [
            "In mindful awareness,",
            "With peaceful intention,",
            "In harmony with your space,",
            "Breathing deeply, consider",
            "In the spirit of balance,"
        ]
        prefix = random.choice(zen_prefixes)
        return f"{prefix} {message.lower()}. May this bring serenity to your home. 🧘"
