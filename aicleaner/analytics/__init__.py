"""
Analytics Package for Roo AI Cleaning Assistant v2.0
Provides comprehensive performance analytics, trend analysis, and insights
"""

from .collector import AnalyticsCollector
from .trend_analyzer import TrendAnalyzer
from .insights import InsightsGenerator
from .api import AnalyticsAPI

__all__ = [
    'AnalyticsCollector',
    'TrendAnalyzer', 
    'InsightsGenerator',
    'AnalyticsAPI'
]
