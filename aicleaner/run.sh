#!/usr/bin/with-contenv bashio

bashio::log.info "Starting Roo AI Cleaning Assistant v2.0..."

# Read configuration into variables
API_KEY=$(bashio::config 'gemini_api_key')
DEFAULT_PERSONALITY=$(bashio::config 'default_personality')
GLOBAL_NOTIFICATIONS=$(bashio::config 'global_notifications')
DATABASE_PATH=$(bashio::config 'database_path')
LOG_LEVEL=$(bashio::config 'log_level')

# Export variables for the Python application to access
export API_KEY DEFAULT_PERSONALITY GLOBAL_NOTIFICATIONS DATABASE_PATH LOG_LEVEL

# Set Python path
export PYTHONPATH="/app:$PYTHONPATH"

bashio::log.info "Starting Roo v2.0 Flask application..."

# Execute the main Python application (Flask server)
cd /app
python3 -m aicleaner.app