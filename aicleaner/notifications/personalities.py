"""
Personality Engine - Generates messages in different personality modes
"""
import random
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from ..data.models import PersonalityMode, Zone


class PersonalityEngine:
    """Generates personality-based messages for different notification types"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._initialize_templates()
    
    def _initialize_templates(self):
        """Initialize message templates for each personality mode"""
        self.templates = {
            PersonalityMode.CONCISE: {
                'task_reminder': [
                    "{zone_name}: {task_count} tasks remaining (Score: {score}/100)",
                    "{zone_name}: {task_count} items need attention",
                    "{task_count} tasks pending in {zone_name}",
                    "{zone_name} cleanliness: {score}/100 - {task_count} tasks"
                ],
                'completion_celebration': [
                    "{zone_name}: All tasks completed! Score: {score}/100",
                    "{zone_name} is now clean (Score: {score}/100)",
                    "All {zone_name} tasks completed",
                    "{zone_name}: Clean and organized"
                ],
                'streak_milestone': [
                    "{zone_name}: {streak_days} day clean streak!",
                    "{streak_days} consecutive clean days in {zone_name}",
                    "{zone_name} streak: {streak_days} days",
                    "Clean streak milestone: {streak_days} days ({zone_name})"
                ],
                'analysis_error': [
                    "{zone_name}: Analysis failed - check camera",
                    "Unable to analyze {zone_name}",
                    "{zone_name} camera issue detected",
                    "Analysis error in {zone_name}"
                ],
                'auto_completion': [
                    "{zone_name}: {task_count} tasks auto-completed",
                    "Auto-completed {task_count} tasks in {zone_name}",
                    "{task_count} tasks marked complete in {zone_name}",
                    "{zone_name}: {task_count} items resolved"
                ]
            },
            
            PersonalityMode.SNARKY: {
                'task_reminder': [
                    "The {zone_name} is staging a rebellion with {task_count} tasks plotting against your relaxation time.",
                    "Your {zone_name} called - it wants to know when you're coming to rescue it from {task_count} tasks.",
                    "Breaking news: {task_count} items in the {zone_name} are having an unauthorized party.",
                    "The {zone_name} scored {score}/100. Even my algorithms are embarrassed.",
                    "I've seen cleaner crime scenes than your {zone_name} (Score: {score}/100, {task_count} tasks).",
                    "Your {zone_name} is so messy, Marie Kondo would need therapy. {task_count} tasks await.",
                    "The {zone_name} chaos level is at {task_count} tasks. Even I need a digital aspirin."
                ],
                'completion_celebration': [
                    "Miracles do happen! The {zone_name} is actually clean (Score: {score}/100).",
                    "Alert the media: {zone_name} has achieved cleanliness! Score: {score}/100",
                    "I'm genuinely shocked. The {zone_name} is clean. Did you hire a cleaning fairy?",
                    "The {zone_name} transformation is complete. I barely recognize it!",
                    "Well, well, well... look who finally cleaned the {zone_name}. Score: {score}/100",
                    "The {zone_name} is so clean, I'm updating my definition of 'impossible'."
                ],
                'streak_milestone': [
                    "Hold the phone! {zone_name} has been clean for {streak_days} whole days. I'm impressed.",
                    "Day {streak_days} of the {zone_name} cleanliness miracle. Still can't believe it.",
                    "The {zone_name} clean streak hits {streak_days} days. Are you feeling okay?",
                    "Breaking: {zone_name} maintains cleanliness for {streak_days} days straight. Unprecedented!",
                    "{streak_days} days of {zone_name} cleanliness. I'm starting to believe in magic."
                ],
                'analysis_error': [
                    "Your {zone_name} camera is having an existential crisis. Can't analyze what it can't see.",
                    "The {zone_name} camera decided to take a sick day. How convenient.",
                    "Camera error in {zone_name}. Even technology doesn't want to look at the mess.",
                    "The {zone_name} analysis failed. Maybe the camera is protecting my circuits.",
                    "I can't analyze the {zone_name} right now. The camera might be in shock."
                ],
                'auto_completion': [
                    "Plot twist: {task_count} tasks in {zone_name} vanished! Either you cleaned or hired ninjas.",
                    "The {zone_name} mystery: {task_count} tasks disappeared. I'm calling it magic.",
                    "Somehow {task_count} tasks in {zone_name} completed themselves. Suspicious...",
                    "The {zone_name} cleaning fairy struck again! {task_count} tasks mysteriously done.",
                    "Either you're getting faster or {task_count} tasks in {zone_name} got tired of waiting."
                ]
            },
            
            PersonalityMode.ENCOURAGING: {
                'task_reminder': [
                    "You're doing amazing! Just {task_count} more tasks and your {zone_name} will be perfect for relaxing!",
                    "Great progress in {zone_name}! Only {task_count} small tasks left to make it shine.",
                    "You've got this! {task_count} quick tasks in {zone_name} and you'll feel so accomplished.",
                    "Almost there! Your {zone_name} is looking better - just {task_count} more tasks to go.",
                    "You're on a roll! {task_count} tasks in {zone_name} and you'll have the perfect space.",
                    "Small steps, big results! {task_count} tasks in {zone_name} will make such a difference.",
                    "You're creating such a wonderful space! {task_count} tasks left in {zone_name}."
                ],
                'completion_celebration': [
                    "🎉 Incredible work! Your {zone_name} is absolutely beautiful now (Score: {score}/100)!",
                    "You did it! The {zone_name} looks amazing - you should be so proud! Score: {score}/100",
                    "Fantastic job! Your {zone_name} is now a peaceful, organized space. Well done!",
                    "Bravo! The {zone_name} transformation is complete. You've created something wonderful!",
                    "Outstanding! Your {zone_name} is spotless and inviting. Time to enjoy your hard work!",
                    "You're a cleaning superstar! The {zone_name} looks absolutely perfect now."
                ],
                'streak_milestone': [
                    "🌟 Incredible! {streak_days} days of keeping {zone_name} beautiful - you're building amazing habits!",
                    "Wow! {streak_days} consecutive days of {zone_name} cleanliness. You're absolutely crushing it!",
                    "Amazing dedication! {streak_days} days of maintaining your beautiful {zone_name}.",
                    "You're on fire! {streak_days} days of {zone_name} perfection. Keep up the fantastic work!",
                    "Inspiring! {streak_days} days of consistent {zone_name} care. You're setting a great example!"
                ],
                'analysis_error': [
                    "No worries! There's a small camera issue with {zone_name}. These things happen!",
                    "Just a quick hiccup with the {zone_name} camera. We'll get back on track soon!",
                    "The {zone_name} analysis hit a small snag, but don't worry - we'll sort it out!",
                    "Technical difficulties with {zone_name} camera. Nothing you did wrong!",
                    "Brief camera issue in {zone_name}. Your cleaning efforts are still amazing!"
                ],
                'auto_completion': [
                    "Wonderful! {task_count} tasks in {zone_name} are now complete. You're making great progress!",
                    "Excellent! I noticed {task_count} tasks in {zone_name} are finished. Keep up the great work!",
                    "Fantastic! {task_count} items in {zone_name} are all sorted. You're doing brilliantly!",
                    "Great job! {task_count} tasks in {zone_name} are complete. Your efforts are paying off!",
                    "Amazing progress! {task_count} tasks in {zone_name} are done. You're creating such a lovely space!"
                ]
            }
        }
    
    def generate_message(self, personality: PersonalityMode, message_type: str, 
                        context: Dict[str, Any]) -> str:
        """
        Generate a personality-based message
        
        Args:
            personality: The personality mode to use
            message_type: Type of message (task_reminder, completion_celebration, etc.)
            context: Context data for message formatting
            
        Returns:
            Formatted message string
        """
        try:
            if personality not in self.templates:
                personality = PersonalityMode.CONCISE
            
            if message_type not in self.templates[personality]:
                self.logger.warning(f"Unknown message type: {message_type}")
                return f"Notification for {context.get('zone_name', 'zone')}"
            
            templates = self.templates[personality][message_type]
            template = random.choice(templates)
            
            # Format the message with context
            formatted_message = template.format(**context)
            
            self.logger.debug(f"Generated {personality.value} {message_type}: {formatted_message}")
            return formatted_message
            
        except Exception as e:
            self.logger.error(f"Failed to generate message: {e}")
            return f"Notification for {context.get('zone_name', 'zone')}"
    
    def generate_task_reminder(self, zone: Zone, task_count: int, score: int) -> str:
        """Generate a task reminder message"""
        context = {
            'zone_name': zone.display_name,
            'task_count': task_count,
            'score': score
        }
        return self.generate_message(zone.personality_mode, 'task_reminder', context)
    
    def generate_completion_celebration(self, zone: Zone, score: int) -> str:
        """Generate a completion celebration message"""
        context = {
            'zone_name': zone.display_name,
            'score': score
        }
        return self.generate_message(zone.personality_mode, 'completion_celebration', context)
    
    def generate_streak_milestone(self, zone: Zone, streak_days: int) -> str:
        """Generate a streak milestone message"""
        context = {
            'zone_name': zone.display_name,
            'streak_days': streak_days
        }
        return self.generate_message(zone.personality_mode, 'streak_milestone', context)
    
    def generate_analysis_error(self, zone: Zone, error_message: str = None) -> str:
        """Generate an analysis error message"""
        context = {
            'zone_name': zone.display_name,
            'error': error_message or 'Unknown error'
        }
        return self.generate_message(zone.personality_mode, 'analysis_error', context)
    
    def generate_auto_completion(self, zone: Zone, task_count: int, completed_tasks: List[str] = None) -> str:
        """Generate an auto-completion message"""
        context = {
            'zone_name': zone.display_name,
            'task_count': task_count,
            'tasks': completed_tasks or []
        }
        return self.generate_message(zone.personality_mode, 'auto_completion', context)
    
    def get_personality_description(self, personality: PersonalityMode) -> str:
        """Get a description of the personality mode"""
        descriptions = {
            PersonalityMode.CONCISE: "Direct and factual notifications with essential information only.",
            PersonalityMode.SNARKY: "Humorous and slightly sarcastic messages that add personality to your cleaning routine.",
            PersonalityMode.ENCOURAGING: "Positive and motivational messages that celebrate your progress and efforts."
        }
        return descriptions.get(personality, "Unknown personality mode")
    
    def preview_personality(self, personality: PersonalityMode, zone_name: str = "Living Room") -> Dict[str, str]:
        """Generate preview messages for each message type in a personality"""
        preview_context = {
            'zone_name': zone_name,
            'task_count': 3,
            'score': 65,
            'streak_days': 5
        }
        
        preview = {}
        for message_type in ['task_reminder', 'completion_celebration', 'streak_milestone', 'analysis_error', 'auto_completion']:
            try:
                preview[message_type] = self.generate_message(personality, message_type, preview_context)
            except Exception as e:
                preview[message_type] = f"Error generating preview: {e}"
        
        return preview
