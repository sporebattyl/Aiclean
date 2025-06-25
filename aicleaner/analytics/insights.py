"""
Insights Generator - Generates actionable insights and recommendations
"""
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

try:
    from ..data import PerformanceMetricsRepository, TaskHistoryRepository, DatabaseManager
    from .trend_analyzer import TrendAnalyzer
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from data import PerformanceMetricsRepository, TaskHistoryRepository, DatabaseManager
    from analytics.trend_analyzer import TrendAnalyzer


@dataclass
class Insight:
    """Represents a generated insight"""
    type: str  # 'recommendation', 'alert', 'observation', 'achievement'
    priority: str  # 'high', 'medium', 'low'
    title: str
    description: str
    action_items: List[str]
    confidence: float
    data_source: str


class InsightsGenerator:
    """Generates actionable insights from analytics data"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.logger = logging.getLogger(__name__)
        self.db = db_manager
        self.metrics_repo = PerformanceMetricsRepository(db_manager)
        self.history_repo = TaskHistoryRepository(db_manager)
        self.trend_analyzer = TrendAnalyzer(db_manager)
        
        # Insight thresholds
        self.thresholds = {
            'low_cleanliness': 60,
            'high_cleanliness': 85,
            'low_completion_rate': 70,
            'high_completion_rate': 90,
            'high_task_volume': 20,
            'long_analysis_time': 5.0,
            'streak_achievement': 7
        }
        
        self.logger.info("Insights generator initialized")
    
    def generate_zone_insights(self, zone_id: int, days: int = 30) -> List[Insight]:
        """
        Generate comprehensive insights for a zone
        
        Args:
            zone_id: Zone to analyze
            days: Number of days to analyze
            
        Returns:
            List of generated insights
        """
        insights = []
        
        try:
            self.logger.info(f"Generating insights for zone {zone_id}")
            
            # Get recent metrics and trends
            metrics = self.metrics_repo.get_recent_metrics(zone_id, days)
            if not metrics:
                return [Insight(
                    type='observation',
                    priority='low',
                    title='No Data Available',
                    description=f'No performance data available for zone {zone_id}',
                    action_items=['Start using the system to collect data'],
                    confidence=1.0,
                    data_source='metrics'
                )]
            
            # Get trend analysis
            trend_analysis = self.trend_analyzer.analyze_zone_trends(zone_id, days)
            
            # Generate different types of insights
            insights.extend(self._generate_performance_insights(metrics, trend_analysis))
            insights.extend(self._generate_pattern_insights(metrics))
            insights.extend(self._generate_achievement_insights(metrics))
            insights.extend(self._generate_recommendation_insights(metrics, trend_analysis))
            insights.extend(self._generate_alert_insights(metrics))
            
            # Sort by priority and confidence
            insights.sort(key=lambda x: (
                {'high': 3, 'medium': 2, 'low': 1}[x.priority],
                x.confidence
            ), reverse=True)
            
            self.logger.info(f"Generated {len(insights)} insights for zone {zone_id}")
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating insights for zone {zone_id}: {e}")
            return [Insight(
                type='alert',
                priority='high',
                title='Analysis Error',
                description=f'Error generating insights: {str(e)}',
                action_items=['Check system logs', 'Verify data integrity'],
                confidence=1.0,
                data_source='system'
            )]
    
    def _generate_performance_insights(self, metrics: List, trend_analysis: Dict) -> List[Insight]:
        """Generate insights about overall performance"""
        insights = []
        
        if not metrics:
            return insights
        
        latest = metrics[0]  # Most recent metrics
        
        # Cleanliness performance
        if latest.avg_cleanliness_score < self.thresholds['low_cleanliness']:
            insights.append(Insight(
                type='alert',
                priority='high',
                title='Low Cleanliness Score',
                description=f'Current cleanliness score is {latest.avg_cleanliness_score:.1f}%, '
                           f'below the recommended {self.thresholds["low_cleanliness"]}%',
                action_items=[
                    'Review recent cleaning tasks',
                    'Check if ignore rules are too aggressive',
                    'Consider increasing cleaning frequency'
                ],
                confidence=0.9,
                data_source='performance_metrics'
            ))
        elif latest.avg_cleanliness_score > self.thresholds['high_cleanliness']:
            insights.append(Insight(
                type='achievement',
                priority='medium',
                title='Excellent Cleanliness',
                description=f'Outstanding cleanliness score of {latest.avg_cleanliness_score:.1f}%!',
                action_items=['Keep up the great work!'],
                confidence=0.9,
                data_source='performance_metrics'
            ))
        
        # Task completion performance
        if latest.completion_rate < self.thresholds['low_completion_rate']:
            insights.append(Insight(
                type='recommendation',
                priority='medium',
                title='Low Task Completion Rate',
                description=f'Only {latest.completion_rate:.1f}% of detected tasks are being completed',
                action_items=[
                    'Review task difficulty and feasibility',
                    'Consider adjusting AI sensitivity',
                    'Check if tasks are too numerous or complex'
                ],
                confidence=0.8,
                data_source='performance_metrics'
            ))
        
        # High task volume
        if latest.tasks_created > self.thresholds['high_task_volume']:
            insights.append(Insight(
                type='observation',
                priority='medium',
                title='High Task Volume',
                description=f'{latest.tasks_created} tasks detected in one day',
                action_items=[
                    'Consider if this is normal for your space',
                    'Review AI sensitivity settings',
                    'Check for recurring issues'
                ],
                confidence=0.7,
                data_source='performance_metrics'
            ))
        
        return insights
    
    def _generate_pattern_insights(self, metrics: List) -> List[Insight]:
        """Generate insights about detected patterns"""
        insights = []
        
        if len(metrics) < 7:
            return insights
        
        # Weekly pattern analysis
        weekly_scores = {}
        for metric in metrics[-14:]:  # Last 2 weeks
            metric_date = date.fromisoformat(metric.metric_date)
            day_name = metric_date.strftime('%A')
            if day_name not in weekly_scores:
                weekly_scores[day_name] = []
            weekly_scores[day_name].append(metric.avg_cleanliness_score)
        
        if len(weekly_scores) >= 5:  # Have data for most days
            day_averages = {day: sum(scores)/len(scores) for day, scores in weekly_scores.items()}
            best_day = max(day_averages, key=day_averages.get)
            worst_day = min(day_averages, key=day_averages.get)
            
            if day_averages[best_day] - day_averages[worst_day] > 10:
                insights.append(Insight(
                    type='observation',
                    priority='low',
                    title='Weekly Pattern Detected',
                    description=f'{best_day} tends to be your cleanest day '
                               f'({day_averages[best_day]:.1f}%), while {worst_day} '
                               f'tends to be messier ({day_averages[worst_day]:.1f}%)',
                    action_items=[
                        f'Consider extra attention on {worst_day}',
                        f'Maintain good habits from {best_day}'
                    ],
                    confidence=0.7,
                    data_source='pattern_analysis'
                ))
        
        return insights
    
    def _generate_achievement_insights(self, metrics: List) -> List[Insight]:
        """Generate insights about achievements and milestones"""
        insights = []
        
        if not metrics:
            return insights
        
        latest = metrics[0]
        
        # Streak achievements
        if latest.streak_days >= self.thresholds['streak_achievement']:
            insights.append(Insight(
                type='achievement',
                priority='medium',
                title=f'{latest.streak_days}-Day Clean Streak!',
                description=f'Congratulations on maintaining good cleanliness for {latest.streak_days} consecutive days!',
                action_items=['Keep the momentum going!'],
                confidence=1.0,
                data_source='streak_tracking'
            ))
        
        # Perfect completion rate
        if latest.completion_rate >= 100:
            insights.append(Insight(
                type='achievement',
                priority='low',
                title='Perfect Task Completion',
                description='All detected tasks were completed - excellent work!',
                action_items=['Maintain this level of attention to detail'],
                confidence=1.0,
                data_source='task_completion'
            ))
        
        # High auto-completion rate (good AI accuracy)
        if latest.auto_completion_rate > 80 and latest.tasks_completed > 5:
            insights.append(Insight(
                type='observation',
                priority='low',
                title='High AI Accuracy',
                description=f'{latest.auto_completion_rate:.1f}% of completed tasks were auto-detected as done',
                action_items=['AI is working well for your space'],
                confidence=0.8,
                data_source='ai_accuracy'
            ))
        
        return insights
    
    def _generate_recommendation_insights(self, metrics: List, trend_analysis: Dict) -> List[Insight]:
        """Generate actionable recommendations"""
        insights = []
        
        if not metrics or 'trends' not in trend_analysis:
            return insights
        
        trends = trend_analysis['trends']
        
        # Declining cleanliness trend
        cleanliness_trend = trends.get('cleanliness_score')
        if (cleanliness_trend and cleanliness_trend.direction == 'declining' 
            and cleanliness_trend.confidence > 0.6):
            insights.append(Insight(
                type='recommendation',
                priority='high',
                title='Address Declining Cleanliness',
                description=f'Cleanliness has been declining by {abs(cleanliness_trend.change_rate):.1f}% recently',
                action_items=[
                    'Review and increase cleaning frequency',
                    'Check if new mess sources have appeared',
                    'Consider adjusting cleaning routines'
                ],
                confidence=cleanliness_trend.confidence,
                data_source='trend_analysis'
            ))
        
        # Declining completion rate
        completion_trend = trends.get('completion_rate')
        if (completion_trend and completion_trend.direction == 'declining' 
            and completion_trend.confidence > 0.6):
            insights.append(Insight(
                type='recommendation',
                priority='medium',
                title='Improve Task Completion',
                description=f'Task completion rate has declined by {abs(completion_trend.change_rate):.1f}%',
                action_items=[
                    'Review task difficulty and feasibility',
                    'Consider breaking large tasks into smaller ones',
                    'Check if AI is detecting too many minor issues'
                ],
                confidence=completion_trend.confidence,
                data_source='trend_analysis'
            ))
        
        return insights
    
    def _generate_alert_insights(self, metrics: List) -> List[Insight]:
        """Generate alerts for issues requiring attention"""
        insights = []
        
        if not metrics:
            return insights
        
        latest = metrics[0]
        
        # Performance alerts
        if latest.avg_analysis_duration > self.thresholds['long_analysis_time']:
            insights.append(Insight(
                type='alert',
                priority='medium',
                title='Slow Analysis Performance',
                description=f'AI analysis is taking {latest.avg_analysis_duration:.1f} seconds on average',
                action_items=[
                    'Check system resources',
                    'Consider image quality optimization',
                    'Review AI model performance'
                ],
                confidence=0.8,
                data_source='performance_monitoring'
            ))
        
        # No recent activity
        if len(metrics) == 1 and metrics[0].analyses_performed == 0:
            insights.append(Insight(
                type='alert',
                priority='low',
                title='No Recent Activity',
                description='No analysis has been performed recently',
                action_items=[
                    'Check camera connectivity',
                    'Verify automation schedules',
                    'Ensure system is running properly'
                ],
                confidence=0.9,
                data_source='activity_monitoring'
            ))
        
        return insights
