"""
Trend Analysis Engine - Advanced pattern detection and trend analysis
"""
import logging
import statistics
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import math

try:
    from ..data import PerformanceMetricsRepository, PerformanceMetrics, DatabaseManager
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from data import PerformanceMetricsRepository, PerformanceMetrics, DatabaseManager


@dataclass
class TrendData:
    """Represents trend analysis results"""
    metric_name: str
    direction: str  # 'improving', 'declining', 'stable'
    strength: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    change_rate: float  # percentage change
    description: str


@dataclass
class PatternData:
    """Represents detected patterns"""
    pattern_type: str  # 'weekly', 'daily', 'seasonal'
    description: str
    confidence: float
    data_points: List[Dict[str, Any]]


class TrendAnalyzer:
    """Analyzes trends and patterns in performance metrics"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.logger = logging.getLogger(__name__)
        self.db = db_manager
        self.metrics_repo = PerformanceMetricsRepository(db_manager)
        
        # Analysis configuration
        self.config = {
            'min_data_points': 7,  # Minimum days of data for trend analysis
            'trend_window': 30,    # Days to analyze for trends
            'pattern_window': 90,  # Days to analyze for patterns
            'significance_threshold': 0.05,  # Statistical significance threshold
            'trend_strength_threshold': 0.3   # Minimum strength for trend detection
        }
        
        self.logger.info("Trend analyzer initialized")
    
    def analyze_zone_trends(self, zone_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Comprehensive trend analysis for a zone
        
        Args:
            zone_id: Zone to analyze
            days: Number of days to analyze
            
        Returns:
            Dictionary containing trend analysis results
        """
        try:
            self.logger.info(f"Analyzing trends for zone {zone_id} over {days} days")
            
            # Get metrics data
            metrics = self.metrics_repo.get_recent_metrics(zone_id, days)
            
            if len(metrics) < self.config['min_data_points']:
                return {
                    'error': f'Insufficient data: {len(metrics)} days (minimum {self.config["min_data_points"]})',
                    'zone_id': zone_id,
                    'data_points': len(metrics)
                }
            
            # Analyze different metrics
            trends = {}
            trends['cleanliness_score'] = self._analyze_metric_trend(
                metrics, 'avg_cleanliness_score', 'Cleanliness Score'
            )
            trends['completion_rate'] = self._analyze_metric_trend(
                metrics, 'completion_rate', 'Task Completion Rate'
            )
            trends['task_volume'] = self._analyze_metric_trend(
                metrics, 'tasks_created', 'Task Volume'
            )
            trends['analysis_performance'] = self._analyze_metric_trend(
                metrics, 'avg_analysis_duration', 'Analysis Performance', inverse=True
            )
            
            # Detect patterns
            patterns = self._detect_patterns(metrics)
            
            # Generate insights
            insights = self._generate_trend_insights(trends, patterns)
            
            # Calculate overall health score
            health_score = self._calculate_health_score(trends)
            
            return {
                'zone_id': zone_id,
                'analysis_period': f'{days} days',
                'data_points': len(metrics),
                'trends': trends,
                'patterns': patterns,
                'insights': insights,
                'health_score': health_score,
                'analyzed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing trends for zone {zone_id}: {e}")
            return {'error': str(e), 'zone_id': zone_id}
    
    def _analyze_metric_trend(self, metrics: List[PerformanceMetrics], 
                             metric_field: str, metric_name: str, 
                             inverse: bool = False) -> TrendData:
        """Analyze trend for a specific metric"""
        
        # Extract values and dates
        values = []
        dates = []
        
        for metric in reversed(metrics):  # Reverse to get chronological order
            value = getattr(metric, metric_field)
            if value is not None:
                values.append(float(value))
                dates.append(date.fromisoformat(metric.metric_date))
        
        if len(values) < 2:
            return TrendData(
                metric_name=metric_name,
                direction='unknown',
                strength=0.0,
                confidence=0.0,
                change_rate=0.0,
                description=f'Insufficient data for {metric_name} trend analysis'
            )
        
        # Calculate linear regression
        slope, confidence = self._calculate_linear_trend(values)
        
        # Adjust for inverse metrics (lower is better)
        if inverse:
            slope = -slope
        
        # Determine trend direction and strength
        if abs(slope) < self.config['trend_strength_threshold']:
            direction = 'stable'
            strength = 0.0
        elif slope > 0:
            direction = 'improving'
            strength = min(abs(slope), 1.0)
        else:
            direction = 'declining'
            strength = min(abs(slope), 1.0)
        
        # Calculate percentage change
        if len(values) >= 2:
            start_value = statistics.mean(values[:3]) if len(values) >= 3 else values[0]
            end_value = statistics.mean(values[-3:]) if len(values) >= 3 else values[-1]
            change_rate = ((end_value - start_value) / start_value * 100) if start_value != 0 else 0.0
            
            if inverse:
                change_rate = -change_rate
        else:
            change_rate = 0.0
        
        # Generate description
        description = self._generate_trend_description(
            metric_name, direction, strength, change_rate
        )
        
        return TrendData(
            metric_name=metric_name,
            direction=direction,
            strength=strength,
            confidence=confidence,
            change_rate=change_rate,
            description=description
        )
    
    def _calculate_linear_trend(self, values: List[float]) -> Tuple[float, float]:
        """Calculate linear regression slope and confidence"""
        n = len(values)
        x = list(range(n))
        
        # Calculate means
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(values)
        
        # Calculate slope
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0, 0.0
        
        slope = numerator / denominator
        
        # Calculate R-squared for confidence
        y_pred = [slope * (i - x_mean) + y_mean for i in x]
        ss_res = sum((values[i] - y_pred[i]) ** 2 for i in range(n))
        ss_tot = sum((values[i] - y_mean) ** 2 for i in range(n))
        
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
        confidence = max(0.0, min(1.0, r_squared))
        
        # Normalize slope to 0-1 range
        normalized_slope = slope / (statistics.stdev(values) if len(values) > 1 else 1.0)
        
        return normalized_slope, confidence
    
    def _detect_patterns(self, metrics: List[PerformanceMetrics]) -> List[PatternData]:
        """Detect recurring patterns in the data"""
        patterns = []
        
        if len(metrics) < 14:  # Need at least 2 weeks for pattern detection
            return patterns
        
        # Weekly patterns
        weekly_pattern = self._detect_weekly_pattern(metrics)
        if weekly_pattern:
            patterns.append(weekly_pattern)
        
        # Performance degradation patterns
        degradation_pattern = self._detect_degradation_pattern(metrics)
        if degradation_pattern:
            patterns.append(degradation_pattern)
        
        # Improvement patterns
        improvement_pattern = self._detect_improvement_pattern(metrics)
        if improvement_pattern:
            patterns.append(improvement_pattern)
        
        return patterns
    
    def _detect_weekly_pattern(self, metrics: List[PerformanceMetrics]) -> Optional[PatternData]:
        """Detect weekly patterns in cleanliness scores"""
        try:
            # Group by day of week
            day_scores = {i: [] for i in range(7)}  # 0=Monday, 6=Sunday
            
            for metric in metrics:
                metric_date = date.fromisoformat(metric.metric_date)
                day_of_week = metric_date.weekday()
                if metric.avg_cleanliness_score > 0:
                    day_scores[day_of_week].append(metric.avg_cleanliness_score)
            
            # Calculate average scores per day
            day_averages = {}
            for day, scores in day_scores.items():
                if scores:
                    day_averages[day] = statistics.mean(scores)
            
            if len(day_averages) < 5:  # Need data for most days
                return None
            
            # Check for significant variation
            avg_values = list(day_averages.values())
            if statistics.stdev(avg_values) < 5:  # Not enough variation
                return None
            
            # Find best and worst days
            best_day = max(day_averages, key=day_averages.get)
            worst_day = min(day_averages, key=day_averages.get)
            
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            return PatternData(
                pattern_type='weekly',
                description=f'Weekly pattern detected: Best day is {day_names[best_day]} '
                           f'({day_averages[best_day]:.1f}), worst is {day_names[worst_day]} '
                           f'({day_averages[worst_day]:.1f})',
                confidence=min(len(day_averages) / 7.0, 1.0),
                data_points=[
                    {'day': day_names[day], 'average_score': avg}
                    for day, avg in day_averages.items()
                ]
            )
            
        except Exception as e:
            self.logger.error(f"Error detecting weekly pattern: {e}")
            return None
    
    def _detect_degradation_pattern(self, metrics: List[PerformanceMetrics]) -> Optional[PatternData]:
        """Detect performance degradation patterns"""
        if len(metrics) < 7:
            return None
        
        # Look for consecutive days of declining performance
        declining_streaks = []
        current_streak = 0
        
        for i in range(1, len(metrics)):
            current = metrics[i].avg_cleanliness_score
            previous = metrics[i-1].avg_cleanliness_score
            
            if current < previous and current > 0 and previous > 0:
                current_streak += 1
            else:
                if current_streak >= 3:  # 3+ consecutive declining days
                    declining_streaks.append(current_streak)
                current_streak = 0
        
        if current_streak >= 3:
            declining_streaks.append(current_streak)
        
        if declining_streaks:
            max_streak = max(declining_streaks)
            return PatternData(
                pattern_type='degradation',
                description=f'Performance degradation detected: {max_streak} consecutive days of decline',
                confidence=min(max_streak / 7.0, 1.0),
                data_points=[{'max_declining_streak': max_streak, 'total_streaks': len(declining_streaks)}]
            )
        
        return None

    def _detect_improvement_pattern(self, metrics: List[PerformanceMetrics]) -> Optional[PatternData]:
        """Detect performance improvement patterns"""
        if len(metrics) < 7:
            return None

        # Look for consecutive days of improving performance
        improving_streaks = []
        current_streak = 0

        for i in range(1, len(metrics)):
            current = metrics[i].avg_cleanliness_score
            previous = metrics[i-1].avg_cleanliness_score

            if current > previous and current > 0 and previous > 0:
                current_streak += 1
            else:
                if current_streak >= 3:  # 3+ consecutive improving days
                    improving_streaks.append(current_streak)
                current_streak = 0

        if current_streak >= 3:
            improving_streaks.append(current_streak)

        if improving_streaks:
            max_streak = max(improving_streaks)
            return PatternData(
                pattern_type='improvement',
                description=f'Performance improvement detected: {max_streak} consecutive days of improvement',
                confidence=min(max_streak / 7.0, 1.0),
                data_points=[{'max_improving_streak': max_streak, 'total_streaks': len(improving_streaks)}]
            )

        return None

    def _generate_trend_insights(self, trends: Dict[str, TrendData],
                                patterns: List[PatternData]) -> List[str]:
        """Generate human-readable insights from trends and patterns"""
        insights = []

        # Analyze overall performance
        cleanliness_trend = trends.get('cleanliness_score')
        if cleanliness_trend and cleanliness_trend.confidence > 0.5:
            if cleanliness_trend.direction == 'improving':
                insights.append(f"✅ Cleanliness is improving with {cleanliness_trend.change_rate:+.1f}% change")
            elif cleanliness_trend.direction == 'declining':
                insights.append(f"⚠️ Cleanliness is declining with {cleanliness_trend.change_rate:+.1f}% change")
            else:
                insights.append("📊 Cleanliness scores are stable")

        # Analyze task completion
        completion_trend = trends.get('completion_rate')
        if completion_trend and completion_trend.confidence > 0.5:
            if completion_trend.direction == 'improving':
                insights.append(f"🎯 Task completion is improving ({completion_trend.change_rate:+.1f}%)")
            elif completion_trend.direction == 'declining':
                insights.append(f"📉 Task completion is declining ({completion_trend.change_rate:+.1f}%)")

        # Analyze patterns
        for pattern in patterns:
            if pattern.confidence > 0.6:
                insights.append(f"🔍 {pattern.description}")

        # Performance insights
        performance_trend = trends.get('analysis_performance')
        if performance_trend and performance_trend.confidence > 0.5:
            if performance_trend.direction == 'improving':
                insights.append("⚡ Analysis performance is improving (faster processing)")
            elif performance_trend.direction == 'declining':
                insights.append("🐌 Analysis performance is declining (slower processing)")

        return insights if insights else ["📊 No significant trends detected in the current period"]

    def _calculate_health_score(self, trends: Dict[str, TrendData]) -> float:
        """Calculate overall health score based on trends"""
        score = 50.0  # Start with neutral score

        # Weight different metrics
        weights = {
            'cleanliness_score': 0.4,
            'completion_rate': 0.3,
            'task_volume': 0.2,
            'analysis_performance': 0.1
        }

        for metric_name, trend in trends.items():
            if metric_name in weights and trend.confidence > 0.3:
                weight = weights[metric_name]

                if trend.direction == 'improving':
                    score += weight * 30 * trend.strength
                elif trend.direction == 'declining':
                    score -= weight * 30 * trend.strength

        return max(0.0, min(100.0, score))

    def _generate_trend_description(self, metric_name: str, direction: str,
                                   strength: float, change_rate: float) -> str:
        """Generate human-readable trend description"""
        strength_words = {
            (0.0, 0.3): 'slightly',
            (0.3, 0.6): 'moderately',
            (0.6, 1.0): 'significantly'
        }

        strength_word = 'slightly'
        for (min_val, max_val), word in strength_words.items():
            if min_val <= strength < max_val:
                strength_word = word
                break

        if direction == 'stable':
            return f"{metric_name} is remaining stable with minimal variation"
        elif direction == 'improving':
            return f"{metric_name} is {strength_word} improving ({change_rate:+.1f}%)"
        else:
            return f"{metric_name} is {strength_word} declining ({change_rate:+.1f}%)"
