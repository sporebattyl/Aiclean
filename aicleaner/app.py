"""
Roo AI Cleaning Assistant v2.0 - Main Flask Application
Serves the analytics API and manages the overall system
"""
import os
import logging
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

try:
    from .core import StateManager
    from .data import initialize_database, get_database
    from .analytics import AnalyticsAPI
    from .config import ConfigManager
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from core import StateManager
    from data import initialize_database, get_database
    from analytics import AnalyticsAPI
    from config import ConfigManager


class RooApplication:
    """Main application class for Roo AI Cleaning Assistant v2.0"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize Flask app
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for frontend
        
        # Load configuration
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config()
        
        # Initialize database
        initialize_database()
        
        # Initialize core components
        gemini_api_key = self.config.get('google_gemini', {}).get('api_key')
        if not gemini_api_key:
            raise ValueError("Google Gemini API key is required")
        
        self.state_manager = StateManager(gemini_api_key)
        
        # Initialize analytics API
        self.analytics_api = AnalyticsAPI(self.app)
        
        # Setup routes
        self._setup_routes()
        
        # Analysis scheduler
        self.analysis_thread = None
        self.running = False
        
        self.logger.info("Roo Application v2.0 initialized")
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/api/health')
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'version': '2.0.0',
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/system/status')
        def system_status():
            """Get system status"""
            try:
                status = self.state_manager.get_system_status()
                return jsonify(status)
            except Exception as e:
                self.logger.error(f"Error getting system status: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/analysis/trigger', methods=['POST'])
        def trigger_analysis():
            """Manually trigger analysis cycle"""
            try:
                data = request.get_json() or {}
                zone_id = data.get('zone_id')
                
                result = self.state_manager.run_analysis_cycle(zone_id)
                return jsonify(result)
                
            except Exception as e:
                self.logger.error(f"Error triggering analysis: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/analytics/trigger', methods=['POST'])
        def trigger_analytics_collection():
            """Manually trigger analytics collection"""
            try:
                data = request.get_json() or {}
                zone_id = data.get('zone_id')
                target_date = data.get('date')
                
                if target_date:
                    from datetime import date
                    target_date = date.fromisoformat(target_date)
                
                result = self.state_manager.trigger_analytics_collection(zone_id, target_date)
                return jsonify(result)
                
            except Exception as e:
                self.logger.error(f"Error triggering analytics collection: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/analytics/status')
        def analytics_status():
            """Get analytics collection status"""
            try:
                status = self.state_manager.get_analytics_status()
                return jsonify(status)
            except Exception as e:
                self.logger.error(f"Error getting analytics status: {e}")
                return jsonify({'error': str(e)}), 500
        
        # Serve frontend files
        @self.app.route('/')
        def index():
            """Serve the main frontend page"""
            return send_from_directory('frontend/www', 'index.html')
        
        @self.app.route('/static/<path:filename>')
        def static_files(filename):
            """Serve static frontend files"""
            return send_from_directory('frontend/www/static', filename)
        
        @self.app.route('/card/<path:filename>')
        def card_files(filename):
            """Serve Lovelace card files"""
            return send_from_directory('frontend/card', filename)
    
    def start_analysis_scheduler(self):
        """Start the background analysis scheduler"""
        if self.analysis_thread and self.analysis_thread.is_alive():
            self.logger.warning("Analysis scheduler already running")
            return
        
        self.running = True
        self.analysis_thread = threading.Thread(target=self._analysis_loop, daemon=True)
        self.analysis_thread.start()
        self.logger.info("Analysis scheduler started")
    
    def stop_analysis_scheduler(self):
        """Stop the background analysis scheduler"""
        self.running = False
        if self.analysis_thread:
            self.analysis_thread.join(timeout=5)
        self.logger.info("Analysis scheduler stopped")
    
    def _analysis_loop(self):
        """Background analysis loop"""
        last_analysis = {}
        last_daily_collection = None
        
        while self.running:
            try:
                current_time = datetime.now()
                
                # Check if we need to run daily analytics collection
                if (last_daily_collection is None or 
                    current_time.date() > last_daily_collection.date()):
                    
                    self.logger.info("Running daily analytics collection")
                    self.state_manager.trigger_analytics_collection()
                    last_daily_collection = current_time
                
                # Check zones for scheduled analysis
                zones = self.state_manager.zone_manager.get_enabled_zones()
                
                for zone in zones:
                    if not zone.enabled or zone.analysis_frequency_minutes <= 0:
                        continue
                    
                    last_run = last_analysis.get(zone.id)
                    if (last_run is None or 
                        (current_time - last_run).total_seconds() >= zone.analysis_frequency_minutes * 60):
                        
                        self.logger.info(f"Running scheduled analysis for zone {zone.name}")
                        try:
                            self.state_manager.run_analysis_cycle(zone.id)
                            last_analysis[zone.id] = current_time
                        except Exception as e:
                            self.logger.error(f"Error in scheduled analysis for zone {zone.name}: {e}")
                
                # Sleep for 1 minute before next check
                time.sleep(60)
                
            except Exception as e:
                self.logger.error(f"Error in analysis loop: {e}")
                time.sleep(60)  # Continue after error
    
    def run(self, host='0.0.0.0', port=8099, debug=False):
        """Run the Flask application"""
        try:
            # Start the analysis scheduler
            self.start_analysis_scheduler()
            
            self.logger.info(f"Starting Roo Application v2.0 on {host}:{port}")
            self.app.run(host=host, port=port, debug=debug, threaded=True)
            
        except KeyboardInterrupt:
            self.logger.info("Shutting down...")
        finally:
            self.stop_analysis_scheduler()


def create_app():
    """Factory function to create Flask app"""
    roo_app = RooApplication()
    return roo_app.app


def main():
    """Main entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        app = RooApplication()
        app.run()
    except Exception as e:
        logging.critical(f"Failed to start Roo Application: {e}")
        raise


if __name__ == '__main__':
    main()
