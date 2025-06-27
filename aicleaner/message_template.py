"""
MessageTemplate - Handles message template formatting
Component-based design following TDD principles
"""

import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class MessageTemplate:
    """
    Handles the base template formatting for different types of notifications.
    
    This component is responsible for creating structured, consistent message
    templates that can then be enhanced with personality formatting.
    """
    
    def __init__(self):
        """Initialize the message template formatter."""
        logger.info("MessageTemplate initialized")
    
    def format_task_notification(self, task_data: Dict[str, Any]) -> str:
        """
        Format a base task notification message.
        
        Args:
            task_data: Dictionary containing task information
            
        Returns:
            str: Formatted base message
        """
        zone = task_data.get('zone', 'Unknown Zone')
        description = task_data.get('description', 'Unknown Task')
        priority = task_data.get('priority', 'normal')
        
        # Format zone name for display
        zone_display = zone.replace('_', ' ').title()
        
        # Create priority indicator
        priority_text = f"({priority.upper()} priority)" if priority != 'normal' else ""
        
        message = f"New task in {zone_display}: {description} {priority_text}".strip()
        
        logger.debug(f"Formatted task notification: {message}")
        return message
    
    def format_analysis_complete(self, analysis_data: Dict[str, Any]) -> str:
        """
        Format a base analysis complete message.
        
        Args:
            analysis_data: Dictionary containing analysis results
            
        Returns:
            str: Formatted base message
        """
        zone = analysis_data.get('zone', 'Unknown Zone')
        tasks_found = analysis_data.get('tasks_found', 0)
        tasks_completed = analysis_data.get('tasks_completed', 0)
        completion_rate = analysis_data.get('completion_rate', 0)
        
        # Format zone name for display
        zone_display = zone.replace('_', ' ').title()
        
        # Calculate completion percentage
        completion_percent = int(completion_rate * 100) if completion_rate else 0
        
        # Create message based on results
        if tasks_found == 0:
            message = f"Analysis complete for {zone_display}: No tasks found - zone looks great!"
        elif tasks_completed == tasks_found:
            message = f"Analysis complete for {zone_display}: All {tasks_found} tasks completed! 🎉"
        else:
            remaining = tasks_found - tasks_completed
            message = f"Analysis complete for {zone_display}: {tasks_found} tasks found, {tasks_completed} completed, {remaining} remaining ({completion_percent}% complete)"
        
        logger.debug(f"Formatted analysis complete: {message}")
        return message
    
    def format_system_status(self, status_data: Dict[str, Any]) -> str:
        """
        Format a base system status message.
        
        Args:
            status_data: Dictionary containing system status information
            
        Returns:
            str: Formatted base message
        """
        total_zones = status_data.get('total_zones', 0)
        active_tasks = status_data.get('active_tasks', 0)
        completed_tasks = status_data.get('completed_tasks', 0)
        completion_rate = status_data.get('completion_rate', 0)
        
        # Calculate completion percentage
        completion_percent = int(completion_rate * 100) if completion_rate else 0
        
        # Create status message
        if active_tasks == 0:
            message = f"System Status: All zones clean! {total_zones} zones monitored, {completed_tasks} tasks completed"
        else:
            total_tasks = active_tasks + completed_tasks
            message = f"System Status: {total_zones} zones monitored, {active_tasks} active tasks, {completed_tasks} completed ({completion_percent}% overall completion)"
        
        logger.debug(f"Formatted system status: {message}")
        return message
    
    def format_zone_summary(self, zone_data: Dict[str, Any]) -> str:
        """
        Format a zone summary message.
        
        Args:
            zone_data: Dictionary containing zone information
            
        Returns:
            str: Formatted zone summary
        """
        zone_name = zone_data.get('name', 'Unknown Zone')
        active_tasks = zone_data.get('active_tasks', 0)
        completed_tasks = zone_data.get('completed_tasks', 0)
        last_analysis = zone_data.get('last_analysis')
        
        # Format zone name for display
        zone_display = zone_name.replace('_', ' ').title()
        
        # Format last analysis time
        if last_analysis:
            try:
                last_analysis_dt = datetime.fromisoformat(last_analysis.replace('Z', '+00:00'))
                time_diff = datetime.now() - last_analysis_dt.replace(tzinfo=None)
                if time_diff.days > 0:
                    time_str = f"{time_diff.days} days ago"
                elif time_diff.seconds > 3600:
                    hours = time_diff.seconds // 3600
                    time_str = f"{hours} hours ago"
                else:
                    minutes = time_diff.seconds // 60
                    time_str = f"{minutes} minutes ago"
            except:
                time_str = "recently"
        else:
            time_str = "never"
        
        # Create summary message
        if active_tasks == 0:
            message = f"{zone_display}: Clean! {completed_tasks} tasks completed (last checked {time_str})"
        else:
            message = f"{zone_display}: {active_tasks} active tasks, {completed_tasks} completed (last checked {time_str})"
        
        logger.debug(f"Formatted zone summary: {message}")
        return message
    
    def format_task_completion(self, task_data: Dict[str, Any]) -> str:
        """
        Format a task completion message.
        
        Args:
            task_data: Dictionary containing completed task information
            
        Returns:
            str: Formatted completion message
        """
        zone = task_data.get('zone', 'Unknown Zone')
        description = task_data.get('description', 'Unknown Task')
        completion_method = task_data.get('completion_method', 'manual')
        
        # Format zone name for display
        zone_display = zone.replace('_', ' ').title()
        
        # Create completion message
        if completion_method == 'auto':
            message = f"Task auto-completed in {zone_display}: {description} ✅"
        else:
            message = f"Task completed in {zone_display}: {description} ✅"
        
        logger.debug(f"Formatted task completion: {message}")
        return message
    
    def format_error_message(self, error_data: Dict[str, Any]) -> str:
        """
        Format an error message.
        
        Args:
            error_data: Dictionary containing error information
            
        Returns:
            str: Formatted error message
        """
        error_type = error_data.get('type', 'Unknown Error')
        zone = error_data.get('zone', 'Unknown Zone')
        details = error_data.get('details', 'No details available')
        
        # Format zone name for display
        zone_display = zone.replace('_', ' ').title()
        
        message = f"⚠️ {error_type} in {zone_display}: {details}"
        
        logger.debug(f"Formatted error message: {message}")
        return message
    
    def format_welcome_message(self, config_data: Dict[str, Any]) -> str:
        """
        Format a welcome/startup message.
        
        Args:
            config_data: Dictionary containing configuration information
            
        Returns:
            str: Formatted welcome message
        """
        personality = config_data.get('personality', 'default')
        zones_count = config_data.get('zones_count', 0)
        version = config_data.get('version', '2.0')
        
        message = f"🏠 AICleaner v{version} is now active! Monitoring {zones_count} zones with {personality} personality."
        
        logger.debug(f"Formatted welcome message: {message}")
        return message
