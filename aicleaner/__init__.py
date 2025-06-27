"""
AICleaner Package - Intelligent Multi-Zone Cleanliness Management
Component-based design following TDD principles
"""

from .aicleaner import AICleaner, Zone
from .configuration_manager import ConfigurationManager
from .notification_engine import NotificationEngine
from .ignore_rules_manager import IgnoreRulesManager

__version__ = "2.0.0"
__all__ = [
    'AICleaner',
    'Zone', 
    'ConfigurationManager',
    'NotificationEngine',
    'IgnoreRulesManager'
]
