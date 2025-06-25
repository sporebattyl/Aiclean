"""
AI Model Manager - Manages multiple AI models and provides fallback mechanisms
"""
import logging
import asyncio
import time
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from datetime import datetime, timedelta
from PIL import Image

from .gemini_client import GeminiClient


class ModelType(Enum):
    """Available AI model types"""
    GEMINI_FLASH = "gemini-1.5-flash"
    GEMINI_PRO = "gemini-1.5-pro"
    GEMINI_VISION = "gemini-pro-vision"
    LOCAL_VISION = "local-vision"  # Placeholder for future local models


class ModelStatus(Enum):
    """Model availability status"""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"
    UNKNOWN = "unknown"


class AIModelManager:
    """Manages multiple AI models with intelligent fallback and load balancing"""
    
    def __init__(self, gemini_api_key: str = None):
        self.logger = logging.getLogger(__name__)
        
        # Initialize model clients
        self.models = {}
        self.model_status = {}
        self.model_performance = {}
        self.rate_limits = {}
        
        # Configuration
        self.config = {
            'primary_model': ModelType.GEMINI_FLASH,
            'fallback_models': [ModelType.GEMINI_PRO, ModelType.GEMINI_VISION],
            'max_retries_per_model': 3,
            'rate_limit_window_minutes': 60,
            'performance_tracking_enabled': True,
            'auto_model_selection': True
        }
        
        # Initialize Gemini models
        if gemini_api_key:
            self._initialize_gemini_models(gemini_api_key)
        
        self.logger.info("AI Model Manager initialized")
    
    def _initialize_gemini_models(self, api_key: str):
        """Initialize Gemini model clients"""
        gemini_models = [ModelType.GEMINI_FLASH, ModelType.GEMINI_PRO, ModelType.GEMINI_VISION]
        
        for model_type in gemini_models:
            try:
                client = GeminiClient(api_key, model_name=model_type.value)
                self.models[model_type] = client
                self.model_status[model_type] = ModelStatus.UNKNOWN
                self.model_performance[model_type] = {
                    'total_requests': 0,
                    'successful_requests': 0,
                    'failed_requests': 0,
                    'average_response_time': 0.0,
                    'last_success': None,
                    'last_failure': None
                }
                self.rate_limits[model_type] = {
                    'requests_in_window': 0,
                    'window_start': datetime.now(),
                    'max_requests_per_window': 60  # Default limit
                }
                
                self.logger.info(f"Initialized {model_type.value} model")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize {model_type.value}: {e}")
    
    async def analyze_with_best_model(self, image: Image.Image, prompt: str, 
                                    preferred_model: ModelType = None) -> Dict[str, Any]:
        """Analyze image using the best available model"""
        start_time = time.time()
        
        # Determine model selection order
        if preferred_model and preferred_model in self.models:
            model_order = [preferred_model] + [m for m in self._get_available_models() if m != preferred_model]
        elif self.config['auto_model_selection']:
            model_order = self._get_optimal_model_order()
        else:
            model_order = [self.config['primary_model']] + self.config['fallback_models']
        
        last_error = None
        
        for model_type in model_order:
            if model_type not in self.models:
                continue
            
            # Check if model is available
            if not await self._is_model_available(model_type):
                continue
            
            try:
                # Attempt analysis with this model
                result = await self._analyze_with_model(model_type, image, prompt)
                
                # Record success
                self._record_model_performance(model_type, True, time.time() - start_time)
                
                result['model_used'] = model_type.value
                result['analysis_duration'] = time.time() - start_time
                
                return result
                
            except Exception as e:
                last_error = e
                self._record_model_performance(model_type, False, time.time() - start_time)
                self.logger.warning(f"Model {model_type.value} failed: {e}")
                continue
        
        # All models failed
        return {
            'success': False,
            'error': f"All models failed. Last error: {last_error}",
            'model_used': None,
            'analysis_duration': time.time() - start_time
        }
    
    async def _analyze_with_model(self, model_type: ModelType, image: Image.Image, 
                                prompt: str) -> Dict[str, Any]:
        """Analyze image with a specific model"""
        if model_type not in self.models:
            raise ValueError(f"Model {model_type.value} not available")
        
        # Check rate limits
        if not self._check_rate_limit(model_type):
            raise Exception(f"Rate limit exceeded for {model_type.value}")
        
        # Update rate limit counter
        self._update_rate_limit(model_type)
        
        # Perform analysis
        client = self.models[model_type]
        
        if hasattr(client, 'analyze_image_with_prompt'):
            response = await client.analyze_image_with_prompt(image, prompt)
        else:
            # Fallback for different client interfaces
            response = await client.analyze_image(image, prompt)
        
        return {
            'success': True,
            'response': response,
            'model_type': model_type.value
        }
    
    async def _is_model_available(self, model_type: ModelType) -> bool:
        """Check if a model is currently available"""
        if model_type not in self.models:
            return False
        
        status = self.model_status.get(model_type, ModelStatus.UNKNOWN)
        
        # If status is unknown, test the model
        if status == ModelStatus.UNKNOWN:
            status = await self._test_model_availability(model_type)
            self.model_status[model_type] = status
        
        # Check if enough time has passed since last failure
        if status in [ModelStatus.UNAVAILABLE, ModelStatus.ERROR]:
            performance = self.model_performance.get(model_type, {})
            last_failure = performance.get('last_failure')
            
            if last_failure:
                time_since_failure = datetime.now() - last_failure
                if time_since_failure > timedelta(minutes=5):  # Retry after 5 minutes
                    status = await self._test_model_availability(model_type)
                    self.model_status[model_type] = status
        
        return status == ModelStatus.AVAILABLE
    
    async def _test_model_availability(self, model_type: ModelType) -> ModelStatus:
        """Test if a model is available by making a simple request"""
        try:
            if model_type not in self.models:
                return ModelStatus.UNAVAILABLE
            
            # Create a simple test image
            test_image = Image.new('RGB', (100, 100), color='white')
            test_prompt = "What do you see in this image? Respond with just 'test image'."
            
            # Set a short timeout for availability test
            client = self.models[model_type]
            
            # Make test request
            response = await asyncio.wait_for(
                client.analyze_image_with_prompt(test_image, test_prompt),
                timeout=10.0
            )
            
            if response and len(response) > 0:
                return ModelStatus.AVAILABLE
            else:
                return ModelStatus.ERROR
                
        except asyncio.TimeoutError:
            return ModelStatus.UNAVAILABLE
        except Exception as e:
            if "rate limit" in str(e).lower() or "quota" in str(e).lower():
                return ModelStatus.RATE_LIMITED
            else:
                return ModelStatus.ERROR
    
    def _get_available_models(self) -> List[ModelType]:
        """Get list of currently available models"""
        available = []
        for model_type in self.models.keys():
            if self.model_status.get(model_type) == ModelStatus.AVAILABLE:
                available.append(model_type)
        return available
    
    def _get_optimal_model_order(self) -> List[ModelType]:
        """Get optimal model order based on performance metrics"""
        models_with_scores = []
        
        for model_type in self.models.keys():
            score = self._calculate_model_score(model_type)
            models_with_scores.append((model_type, score))
        
        # Sort by score (higher is better)
        models_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        return [model_type for model_type, _ in models_with_scores]
    
    def _calculate_model_score(self, model_type: ModelType) -> float:
        """Calculate a performance score for a model"""
        performance = self.model_performance.get(model_type, {})
        
        # Base score from success rate
        total_requests = performance.get('total_requests', 0)
        successful_requests = performance.get('successful_requests', 0)
        
        if total_requests == 0:
            success_rate = 0.5  # Neutral score for untested models
        else:
            success_rate = successful_requests / total_requests
        
        # Factor in response time (lower is better)
        avg_response_time = performance.get('average_response_time', 5.0)
        time_score = max(0, 1.0 - (avg_response_time / 10.0))  # Normalize to 0-1
        
        # Factor in recency of last success
        last_success = performance.get('last_success')
        recency_score = 1.0
        if last_success:
            hours_since_success = (datetime.now() - last_success).total_seconds() / 3600
            recency_score = max(0.1, 1.0 - (hours_since_success / 24.0))  # Decay over 24 hours
        
        # Combine scores
        total_score = (success_rate * 0.5) + (time_score * 0.3) + (recency_score * 0.2)
        
        return total_score
    
    def _check_rate_limit(self, model_type: ModelType) -> bool:
        """Check if model is within rate limits"""
        rate_limit_info = self.rate_limits.get(model_type, {})
        
        window_start = rate_limit_info.get('window_start', datetime.now())
        requests_in_window = rate_limit_info.get('requests_in_window', 0)
        max_requests = rate_limit_info.get('max_requests_per_window', 60)
        
        # Reset window if needed
        if datetime.now() - window_start > timedelta(minutes=self.config['rate_limit_window_minutes']):
            self.rate_limits[model_type]['window_start'] = datetime.now()
            self.rate_limits[model_type]['requests_in_window'] = 0
            return True
        
        return requests_in_window < max_requests
    
    def _update_rate_limit(self, model_type: ModelType):
        """Update rate limit counter for a model"""
        if model_type in self.rate_limits:
            self.rate_limits[model_type]['requests_in_window'] += 1
    
    def _record_model_performance(self, model_type: ModelType, success: bool, response_time: float):
        """Record performance metrics for a model"""
        if model_type not in self.model_performance:
            return
        
        performance = self.model_performance[model_type]
        
        # Update counters
        performance['total_requests'] += 1
        if success:
            performance['successful_requests'] += 1
            performance['last_success'] = datetime.now()
        else:
            performance['failed_requests'] += 1
            performance['last_failure'] = datetime.now()
        
        # Update average response time
        current_avg = performance['average_response_time']
        total_requests = performance['total_requests']
        
        if total_requests == 1:
            performance['average_response_time'] = response_time
        else:
            # Exponential moving average
            alpha = 0.1  # Smoothing factor
            performance['average_response_time'] = (alpha * response_time) + ((1 - alpha) * current_avg)
    
    def get_model_status_report(self) -> Dict[str, Any]:
        """Get comprehensive status report for all models"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'models': {},
            'configuration': self.config,
            'summary': {
                'total_models': len(self.models),
                'available_models': len(self._get_available_models()),
                'optimal_model': None
            }
        }
        
        # Get optimal model
        optimal_order = self._get_optimal_model_order()
        if optimal_order:
            report['summary']['optimal_model'] = optimal_order[0].value
        
        # Model details
        for model_type in self.models.keys():
            report['models'][model_type.value] = {
                'status': self.model_status.get(model_type, ModelStatus.UNKNOWN).value,
                'performance': self.model_performance.get(model_type, {}),
                'rate_limit': self.rate_limits.get(model_type, {}),
                'score': self._calculate_model_score(model_type)
            }
        
        return report
    
    def update_model_configuration(self, config_updates: Dict[str, Any]):
        """Update model manager configuration"""
        self.config.update(config_updates)
        self.logger.info(f"Model configuration updated: {config_updates}")
    
    def set_model_rate_limit(self, model_type: ModelType, max_requests_per_window: int):
        """Set rate limit for a specific model"""
        if model_type in self.rate_limits:
            self.rate_limits[model_type]['max_requests_per_window'] = max_requests_per_window
            self.logger.info(f"Rate limit updated for {model_type.value}: {max_requests_per_window}")
    
    async def health_check_all_models(self) -> Dict[str, Any]:
        """Perform health check on all models"""
        health_results = {}
        
        for model_type in self.models.keys():
            try:
                status = await self._test_model_availability(model_type)
                self.model_status[model_type] = status
                health_results[model_type.value] = {
                    'status': status.value,
                    'healthy': status == ModelStatus.AVAILABLE
                }
            except Exception as e:
                health_results[model_type.value] = {
                    'status': 'error',
                    'healthy': False,
                    'error': str(e)
                }
        
        return {
            'timestamp': datetime.now().isoformat(),
            'results': health_results,
            'overall_health': any(result['healthy'] for result in health_results.values())
        }
