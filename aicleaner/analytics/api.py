"""
Analytics API - REST endpoints for serving analytics data
"""
import logging
import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify, Blueprint
from dataclasses import asdict

try:
    from ..data import DatabaseManager, get_database
    from .collector import AnalyticsCollector
    from .trend_analyzer import TrendAnalyzer
    from .insights import InsightsGenerator
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from data import DatabaseManager, get_database
    from analytics.collector import AnalyticsCollector
    from analytics.trend_analyzer import TrendAnalyzer
    from analytics.insights import InsightsGenerator


class AnalyticsAPI:
    """REST API for analytics data"""
    
    def __init__(self, app: Optional[Flask] = None):
        self.logger = logging.getLogger(__name__)
        self.db = get_database()
        
        # Initialize analytics components
        self.collector = AnalyticsCollector(self.db)
        self.trend_analyzer = TrendAnalyzer(self.db)
        self.insights_generator = InsightsGenerator(self.db)
        
        # Create blueprint
        self.blueprint = Blueprint('analytics', __name__, url_prefix='/api/analytics')
        self._register_routes()
        
        if app:
            self.register_with_app(app)
        
        self.logger.info("Analytics API initialized")
    
    def register_with_app(self, app: Flask):
        """Register the analytics blueprint with a Flask app"""
        app.register_blueprint(self.blueprint)
        self.logger.info("Analytics API registered with Flask app")
    
    def _register_routes(self):
        """Register all API routes"""
        
        @self.blueprint.route('/metrics/<int:zone_id>')
        def get_zone_metrics(zone_id: int):
            """Get performance metrics for a zone"""
            try:
                days = request.args.get('days', 30, type=int)
                days = min(max(days, 1), 365)  # Limit to 1-365 days
                
                metrics = self.collector.metrics_repo.get_recent_metrics(zone_id, days)
                summary = self.collector.metrics_repo.get_metrics_summary(zone_id, days)
                
                return jsonify({
                    'zone_id': zone_id,
                    'period_days': days,
                    'metrics': [self._serialize_metrics(m) for m in metrics],
                    'summary': summary,
                    'retrieved_at': datetime.now().isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"Error getting metrics for zone {zone_id}: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.blueprint.route('/trends/<int:zone_id>')
        def get_zone_trends(zone_id: int):
            """Get trend analysis for a zone"""
            try:
                days = request.args.get('days', 30, type=int)
                days = min(max(days, 7), 365)  # Minimum 7 days for trends
                
                trends = self.trend_analyzer.analyze_zone_trends(zone_id, days)
                
                return jsonify(trends)
                
            except Exception as e:
                self.logger.error(f"Error getting trends for zone {zone_id}: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.blueprint.route('/insights/<int:zone_id>')
        def get_zone_insights(zone_id: int):
            """Get insights and recommendations for a zone"""
            try:
                days = request.args.get('days', 30, type=int)
                days = min(max(days, 7), 365)
                
                insights = self.insights_generator.generate_zone_insights(zone_id, days)
                
                return jsonify({
                    'zone_id': zone_id,
                    'period_days': days,
                    'insights': [self._serialize_insight(i) for i in insights],
                    'total_insights': len(insights),
                    'generated_at': datetime.now().isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"Error getting insights for zone {zone_id}: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.blueprint.route('/dashboard/<int:zone_id>')
        def get_dashboard_data(zone_id: int):
            """Get comprehensive dashboard data for a zone"""
            try:
                days = request.args.get('days', 30, type=int)
                days = min(max(days, 7), 365)
                
                # Get all data in parallel
                metrics = self.collector.metrics_repo.get_recent_metrics(zone_id, days)
                summary = self.collector.metrics_repo.get_metrics_summary(zone_id, days)
                trends = self.trend_analyzer.analyze_zone_trends(zone_id, days)
                insights = self.insights_generator.generate_zone_insights(zone_id, days)
                
                return jsonify({
                    'zone_id': zone_id,
                    'period_days': days,
                    'metrics': {
                        'recent': [self._serialize_metrics(m) for m in metrics[:7]],  # Last 7 days
                        'summary': summary
                    },
                    'trends': trends,
                    'insights': [self._serialize_insight(i) for i in insights[:5]],  # Top 5 insights
                    'dashboard_generated_at': datetime.now().isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"Error getting dashboard data for zone {zone_id}: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.blueprint.route('/collection/status')
        def get_collection_status():
            """Get analytics collection status"""
            try:
                status = self.collector.get_collection_status()
                return jsonify(status)
                
            except Exception as e:
                self.logger.error(f"Error getting collection status: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.blueprint.route('/collection/trigger', methods=['POST'])
        def trigger_collection():
            """Manually trigger metrics collection"""
            try:
                data = request.get_json() or {}
                zone_id = data.get('zone_id')
                target_date = data.get('date')
                
                if target_date:
                    target_date = date.fromisoformat(target_date)
                
                if zone_id:
                    # Collect for specific zone
                    success = self.collector.collect_daily_metrics(zone_id, target_date)
                    return jsonify({
                        'success': success,
                        'zone_id': zone_id,
                        'date': target_date.isoformat() if target_date else 'yesterday'
                    })
                else:
                    # Collect for all zones
                    results = self.collector.collect_all_zones_metrics(target_date)
                    return jsonify({
                        'results': results,
                        'total_zones': len(results),
                        'successful_zones': sum(1 for success in results.values() if success),
                        'date': target_date.isoformat() if target_date else 'yesterday'
                    })
                
            except Exception as e:
                self.logger.error(f"Error triggering collection: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.blueprint.route('/export/<int:zone_id>')
        def export_zone_data(zone_id: int):
            """Export zone analytics data"""
            try:
                days = request.args.get('days', 90, type=int)
                format_type = request.args.get('format', 'json')
                
                metrics = self.collector.metrics_repo.get_recent_metrics(zone_id, days)
                trends = self.trend_analyzer.analyze_zone_trends(zone_id, days)
                insights = self.insights_generator.generate_zone_insights(zone_id, days)
                
                export_data = {
                    'zone_id': zone_id,
                    'export_period_days': days,
                    'metrics': [self._serialize_metrics(m) for m in metrics],
                    'trends': trends,
                    'insights': [self._serialize_insight(i) for i in insights],
                    'exported_at': datetime.now().isoformat()
                }
                
                if format_type == 'csv':
                    # Convert to CSV format for metrics
                    import csv
                    import io
                    
                    output = io.StringIO()
                    if metrics:
                        writer = csv.DictWriter(output, fieldnames=self._serialize_metrics(metrics[0]).keys())
                        writer.writeheader()
                        for metric in metrics:
                            writer.writerow(self._serialize_metrics(metric))
                    
                    response = Flask.response_class(
                        output.getvalue(),
                        mimetype='text/csv',
                        headers={'Content-Disposition': f'attachment; filename=zone_{zone_id}_metrics.csv'}
                    )
                    return response
                else:
                    return jsonify(export_data)
                
            except Exception as e:
                self.logger.error(f"Error exporting data for zone {zone_id}: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.blueprint.route('/health')
        def health_check():
            """Health check endpoint"""
            try:
                # Test database connection
                status = self.collector.get_collection_status()
                
                return jsonify({
                    'status': 'healthy',
                    'timestamp': datetime.now().isoformat(),
                    'database_connected': True,
                    'zones_tracked': status.get('zones_tracked', 0)
                })
                
            except Exception as e:
                self.logger.error(f"Health check failed: {e}")
                return jsonify({
                    'status': 'unhealthy',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
    
    def _serialize_metrics(self, metrics) -> Dict[str, Any]:
        """Serialize PerformanceMetrics to dictionary"""
        return {
            'id': metrics.id,
            'zone_id': metrics.zone_id,
            'metric_date': metrics.metric_date,
            'analyses_performed': metrics.analyses_performed,
            'tasks_created': metrics.tasks_created,
            'tasks_completed': metrics.tasks_completed,
            'tasks_auto_completed': metrics.tasks_auto_completed,
            'tasks_ignored': metrics.tasks_ignored,
            'avg_cleanliness_score': metrics.avg_cleanliness_score,
            'min_cleanliness_score': metrics.min_cleanliness_score,
            'max_cleanliness_score': metrics.max_cleanliness_score,
            'completion_rate': metrics.completion_rate,
            'auto_completion_rate': metrics.auto_completion_rate,
            'avg_analysis_duration': metrics.avg_analysis_duration,
            'total_gemini_tokens': metrics.total_gemini_tokens,
            'streak_days': metrics.streak_days,
            'created_at': metrics.created_at.isoformat() if metrics.created_at else None,
            'updated_at': metrics.updated_at.isoformat() if metrics.updated_at else None
        }
    
    def _serialize_insight(self, insight) -> Dict[str, Any]:
        """Serialize Insight to dictionary"""
        return {
            'type': insight.type,
            'priority': insight.priority,
            'title': insight.title,
            'description': insight.description,
            'action_items': insight.action_items,
            'confidence': insight.confidence,
            'data_source': insight.data_source
        }
