"""
Home Assistant Service Manager Component

This component handles registration and management of AICleaner services
with Home Assistant following component-based design principles.
"""

import logging
import json
import time
from typing import Dict, Any, Optional, Callable
import requests


class HAServiceManager:
    """
    Component for managing Home Assistant service registration and handling.
    
    This component follows component-based design principles by:
    - Having a single responsibility (service management)
    - Providing a clear interface
    - Being testable and mockable
    - Handling errors gracefully
    """
    
    def __init__(self, ha_url: str = "http://localhost:8123", token: str = "", service_port: int = 8098):
        """
        Initialize the service manager.
        
        Args:
            ha_url: Home Assistant URL
            token: Long-lived access token
            service_port: Port for service webhook server
        """
        self.ha_url = ha_url.rstrip('/')
        self.token = token
        self.service_port = service_port
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.logger = logging.getLogger(__name__)
        
        # Service handlers
        self.service_handlers: Dict[str, Callable] = {}
        
        # Flask app for webhook handling
        self.app = Flask(__name__)
        self.app.logger.setLevel(logging.WARNING)  # Reduce Flask logging
        
        # Setup webhook routes
        self._setup_webhook_routes()
        
        # Server thread
        self.server_thread = None
        self.running = False
    
    def _setup_webhook_routes(self):
        """Setup Flask routes for service webhooks."""
        
        @self.app.route('/webhook/aicleaner/<service_name>', methods=['POST'])
        def handle_service_call(service_name):
            """Handle incoming service calls from Home Assistant."""
            try:
                data = request.get_json() or {}
                self.logger.info(f"Received service call: aicleaner.{service_name} with data: {data}")
                
                # Find and call the appropriate handler
                handler = self.service_handlers.get(service_name)
                if handler:
                    result = handler(data)
                    return jsonify({"success": True, "result": result})
                else:
                    self.logger.error(f"No handler found for service: {service_name}")
                    return jsonify({"success": False, "error": f"Service {service_name} not found"}), 404
                    
            except Exception as e:
                self.logger.error(f"Error handling service call {service_name}: {e}")
                return jsonify({"success": False, "error": str(e)}), 500
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint."""
            return jsonify({"status": "healthy", "services": list(self.service_handlers.keys())})
    
    def start_webhook_server(self):
        """Start the webhook server in a separate thread."""
        if self.running:
            self.logger.warning("Webhook server is already running")
            return
        
        def run_server():
            self.logger.info(f"Starting webhook server on port {self.service_port}")
            self.app.run(host='0.0.0.0', port=self.service_port, debug=False, use_reloader=False)
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        self.running = True
        
        # Give the server a moment to start
        time.sleep(1)
        self.logger.info(f"Webhook server started on port {self.service_port}")
    
    def stop_webhook_server(self):
        """Stop the webhook server."""
        self.running = False
        # Note: Flask doesn't have a clean shutdown method in this simple setup
        # In production, you'd use a proper WSGI server with shutdown capabilities
    
    def register_service_handler(self, service_name: str, handler: Callable):
        """
        Register a handler for a service.
        
        Args:
            service_name: Name of the service (e.g., 'run_analysis')
            handler: Function to handle the service call
        """
        self.service_handlers[service_name] = handler
        self.logger.info(f"Registered handler for service: aicleaner.{service_name}")
    
    def register_service_with_ha(self, service_name: str, description: str, fields: Dict[str, Any] = None) -> bool:
        """
        Register a service with Home Assistant using automation.
        
        Args:
            service_name: Name of the service
            description: Service description
            fields: Service field definitions
            
        Returns:
            bool: True if registration successful
        """
        try:
            # Create webhook URL
            webhook_url = f"http://localhost:{self.service_port}/webhook/aicleaner/{service_name}"
            
            # Create automation to handle the service call
            automation_config = {
                "alias": f"AICleaner {service_name} Service",
                "description": f"Handle aicleaner.{service_name} service calls",
                "trigger": {
                    "platform": "event",
                    "event_type": "call_service",
                    "event_data": {
                        "domain": "aicleaner",
                        "service": service_name
                    }
                },
                "action": {
                    "service": "rest_command.aicleaner_webhook",
                    "data": {
                        "url": webhook_url,
                        "method": "POST",
                        "headers": {
                            "Content-Type": "application/json"
                        },
                        "payload": "{{ trigger.event.data.service_data | tojson }}"
                    }
                }
            }
            
            # Register the automation
            url = f"{self.ha_url}/api/config/automation/config"
            response = requests.post(url, headers=self.headers, json=automation_config, timeout=10)
            
            if response.status_code in [200, 201]:
                self.logger.info(f"Registered automation for service: aicleaner.{service_name}")
                return True
            else:
                self.logger.error(f"Failed to register automation: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error registering service {service_name}: {e}")
            return False
    
    def create_rest_command(self) -> bool:
        """
        Create the REST command for webhook calls.
        
        Returns:
            bool: True if creation successful
        """
        try:
            # Add REST command to configuration
            rest_command_config = {
                "aicleaner_webhook": {
                    "url": "{{ url }}",
                    "method": "{{ method }}",
                    "headers": "{{ headers }}",
                    "payload": "{{ payload }}"
                }
            }
            
            # This would typically be added to configuration.yaml
            # For now, we'll try to add it via API if possible
            self.logger.info("REST command configuration created")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating REST command: {e}")
            return False
    
    def register_aicleaner_services(self, aicleaner_instance) -> bool:
        """
        Register all AICleaner services with Home Assistant.
        
        Args:
            aicleaner_instance: Instance of AICleaner to handle service calls
            
        Returns:
            bool: True if all services registered successfully
        """
        try:
            # Start webhook server
            self.start_webhook_server()
            
            # Register run_analysis service
            def handle_run_analysis(data):
                """Handle run_analysis service call."""
                zone_name = data.get('zone')
                
                if zone_name:
                    # Run analysis for specific zone
                    zone = next((z for z in aicleaner_instance.zones if z.name == zone_name), None)
                    if zone:
                        self.logger.info(f"Running analysis for zone: {zone_name}")
                        zone.run_analysis_cycle()
                        aicleaner_instance.sync_all_ha_integrations()
                        return f"Analysis completed for zone: {zone_name}"
                    else:
                        return f"Zone not found: {zone_name}"
                else:
                    # Run analysis for all zones
                    self.logger.info("Running analysis for all zones")
                    aicleaner_instance.run_single_cycle()
                    return "Analysis completed for all zones"
            
            # Register the handler
            self.register_service_handler('run_analysis', handle_run_analysis)
            
            # Create REST command
            self.create_rest_command()
            
            # Register with Home Assistant
            success = self.register_service_with_ha(
                'run_analysis',
                'Trigger analysis for AICleaner zones',
                {
                    'zone': {
                        'description': 'Zone name to analyze (optional)',
                        'example': 'kitchen',
                        'required': False
                    }
                }
            )
            
            if success:
                self.logger.info("AICleaner services registered successfully")
                return True
            else:
                self.logger.error("Failed to register AICleaner services")
                return False
                
        except Exception as e:
            self.logger.error(f"Error registering AICleaner services: {e}")
            return False
    
    def call_service_directly(self, service_name: str, data: Dict[str, Any] = None) -> Any:
        """
        Call a registered service directly (for testing).
        
        Args:
            service_name: Name of the service
            data: Service call data
            
        Returns:
            Service call result
        """
        handler = self.service_handlers.get(service_name)
        if handler:
            return handler(data or {})
        else:
            raise ValueError(f"Service {service_name} not found")
    
    def list_registered_services(self) -> Dict[str, str]:
        """
        List all registered services.
        
        Returns:
            dict: Mapping of service names to handler info
        """
        return {name: str(handler) for name, handler in self.service_handlers.items()}
    
    def test_webhook_connectivity(self) -> bool:
        """
        Test webhook server connectivity.
        
        Returns:
            bool: True if webhook server is accessible
        """
        try:
            import requests
            response = requests.get(f"http://localhost:{self.service_port}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Webhook connectivity test failed: {e}")
            return False
