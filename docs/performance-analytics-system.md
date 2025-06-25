# 📊 Performance Analytics System - Roo AI Cleaning Assistant v2.0

## Overview

The Performance Analytics System provides comprehensive insights into your home's cleanliness patterns, task completion rates, and overall system performance. It automatically collects, analyzes, and presents actionable insights to help you optimize your cleaning routines.

## 🏗️ Architecture

### Core Components

1. **Analytics Collector** (`analytics/collector.py`)
   - Automated daily metrics aggregation
   - Historical data processing
   - Backfill capabilities for missing data

2. **Trend Analyzer** (`analytics/trend_analyzer.py`)
   - Advanced pattern detection algorithms
   - Statistical trend analysis
   - Performance degradation detection

3. **Insights Generator** (`analytics/insights.py`)
   - AI-powered recommendations
   - Actionable insights generation
   - Priority-based alert system

4. **Analytics API** (`analytics/api.py`)
   - RESTful endpoints for data access
   - Real-time analytics serving
   - Export capabilities

5. **Enhanced Frontend** (`frontend/card/components/roo-performance.js`)
   - Interactive dashboard
   - Real-time data visualization
   - Mobile-responsive design

## 📈 Features

### Automated Data Collection
- **Daily Metrics Aggregation**: Automatically processes TaskHistory data into PerformanceMetrics
- **Real-time Updates**: Metrics updated after each analysis cycle
- **Historical Processing**: Backfill capabilities for retroactive analysis

### Advanced Analytics
- **Trend Detection**: Identifies improving, declining, or stable performance patterns
- **Pattern Recognition**: Detects weekly patterns, degradation cycles, and improvement streaks
- **Statistical Analysis**: Uses linear regression and confidence scoring

### Intelligent Insights
- **AI Recommendations**: Generates actionable suggestions based on data patterns
- **Priority Alerts**: High/medium/low priority insights with confidence scores
- **Achievement Tracking**: Celebrates milestones and streaks

### Comprehensive Dashboard
- **Performance Metrics**: Cleanliness scores, task completion rates, analysis performance
- **Trend Visualization**: Interactive charts showing performance over time
- **Health Score**: Overall system health indicator (0-100)
- **Export Capabilities**: CSV and JSON data export

## 🔧 API Endpoints

### Analytics Data
```
GET /api/analytics/metrics/{zone_id}?days=30
GET /api/analytics/trends/{zone_id}?days=30
GET /api/analytics/insights/{zone_id}?days=30
GET /api/analytics/dashboard/{zone_id}?days=30
```

### Collection Management
```
GET /api/analytics/collection/status
POST /api/analytics/collection/trigger
```

### Data Export
```
GET /api/analytics/export/{zone_id}?days=90&format=json|csv
```

### System Health
```
GET /api/analytics/health
```

## 📊 Data Models

### PerformanceMetrics
```python
@dataclass
class PerformanceMetrics:
    zone_id: int
    metric_date: str  # YYYY-MM-DD
    analyses_performed: int
    tasks_created: int
    tasks_completed: int
    tasks_auto_completed: int
    tasks_ignored: int
    avg_cleanliness_score: float
    min_cleanliness_score: int
    max_cleanliness_score: int
    completion_rate: float
    auto_completion_rate: float
    avg_analysis_duration: float
    total_gemini_tokens: int
    streak_days: int
```

### TrendData
```python
@dataclass
class TrendData:
    metric_name: str
    direction: str  # 'improving', 'declining', 'stable'
    strength: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    change_rate: float  # percentage change
    description: str
```

### Insight
```python
@dataclass
class Insight:
    type: str  # 'recommendation', 'alert', 'observation', 'achievement'
    priority: str  # 'high', 'medium', 'low'
    title: str
    description: str
    action_items: List[str]
    confidence: float
    data_source: str
```

## 🚀 Usage Examples

### Triggering Manual Collection
```python
# Collect metrics for specific zone
result = state_manager.trigger_analytics_collection(zone_id=1)

# Collect metrics for all zones
result = state_manager.trigger_analytics_collection()

# Backfill historical data
collector.backfill_metrics(zone_id=1, start_date=date(2024, 1, 1), end_date=date.today())
```

### Getting Analytics Data
```python
# Get trend analysis
trends = trend_analyzer.analyze_zone_trends(zone_id=1, days=30)

# Generate insights
insights = insights_generator.generate_zone_insights(zone_id=1, days=30)

# Get performance metrics
metrics = metrics_repo.get_recent_metrics(zone_id=1, days=30)
```

### Frontend Integration
```javascript
// Load analytics data
const response = await fetch(`/api/analytics/dashboard/${zoneId}?days=30`);
const data = await response.json();

// Trigger collection
await fetch('/api/analytics/collection/trigger', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ zone_id: zoneId })
});
```

## 🔍 Insights Types

### Recommendations
- **Low Completion Rate**: Suggests reviewing task difficulty
- **Declining Trends**: Recommends increasing cleaning frequency
- **Performance Issues**: Suggests system optimization

### Alerts
- **Low Cleanliness Scores**: Immediate attention required
- **System Performance**: Slow analysis or high resource usage
- **Data Issues**: Missing or inconsistent data

### Observations
- **Weekly Patterns**: Identifies best/worst days
- **High Task Volume**: Notes unusual activity levels
- **AI Accuracy**: Reports auto-completion rates

### Achievements
- **Clean Streaks**: Celebrates consecutive good days
- **Perfect Completion**: Acknowledges 100% task completion
- **Improvement Milestones**: Recognizes positive trends

## 📱 Frontend Features

### Performance Dashboard
- **Summary Cards**: Key metrics with trend indicators
- **Interactive Charts**: Cleanliness scores and task completion over time
- **Time Range Selection**: 7, 30, 90, or 365 days
- **Real-time Updates**: Automatic data refresh

### Trend Analysis
- **Trend Cards**: Visual representation of performance trends
- **Health Score**: Overall system health indicator
- **Confidence Indicators**: Statistical confidence in trends

### Enhanced Insights
- **Priority-based Display**: High priority insights shown first
- **Action Items**: Specific recommendations for improvement
- **Confidence Scores**: Reliability indicators for insights

## 🔧 Configuration

### Analytics Collection
```python
# Configure collection thresholds
collector.config = {
    'min_data_points': 7,
    'trend_window': 30,
    'pattern_window': 90,
    'significance_threshold': 0.05
}
```

### Insight Generation
```python
# Configure insight thresholds
insights_generator.thresholds = {
    'low_cleanliness': 60,
    'high_cleanliness': 85,
    'low_completion_rate': 70,
    'high_completion_rate': 90,
    'streak_achievement': 7
}
```

## 🚀 Performance Optimizations

### Database Indexing
- Indexed on `zone_id` and `metric_date` for fast queries
- Composite indexes for common query patterns

### Caching Strategy
- Frontend caches analytics data for 5 minutes
- API responses include cache headers

### Background Processing
- Daily collection runs automatically at midnight
- Non-blocking analytics processing

## 🔮 Future Enhancements

### Planned Features
- **Predictive Analytics**: Forecast future cleanliness trends
- **Comparative Analysis**: Compare zones and time periods
- **Custom Metrics**: User-defined performance indicators
- **Advanced Visualizations**: Heat maps and correlation charts
- **Machine Learning**: Automated pattern recognition improvements

### Integration Opportunities
- **Home Assistant Sensors**: Expose analytics as HA sensors
- **Notification Integration**: Analytics-driven notifications
- **Automation Triggers**: Use insights to trigger automations
- **Mobile App**: Dedicated mobile analytics interface

## 📚 Related Documentation

- [Core Architecture](./v2.0-architecture.md)
- [Database Schema](./database-schema.md)
- [API Reference](./api-reference.md)
- [Frontend Components](./frontend-components.md)
- [Configuration Guide](./configuration-guide.md)
