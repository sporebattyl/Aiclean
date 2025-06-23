#!/usr/bin/with-contenv bashio

bashio::log.info "Starting Roo AI Cleaning Assistant..."

# Read configuration into variables
# Read configuration using bashio, respecting defaults from config.yaml
CAMERA_ENTITY=$(bashio::config 'camera_entity')
API_KEY=$(bashio::config 'gemini_api_key')
TODO_LIST=$(bashio::config 'todo_list_entity')
SENSOR_ENTITY=$(bashio::config 'sensor_entity_id')
# The frequency is now in minutes, convert to seconds for sleep
FREQUENCY_MINUTES=$(bashio::config 'update_frequency')
SLEEP_TIME=$((FREQUENCY_MINUTES * 60))

# Main execution loop
while true; do
  bashio::log.info "Running cleanliness analysis..."

  # Export variables for the Python script to access
  export CAMERA_ENTITY API_KEY TODO_LIST SENSOR_ENTITY

  # Execute the main Python application
  python3 /app/aicleaner/aicleaner.py

  bashio::log.info "Analysis complete. Sleeping for ${FREQUENCY_MINUTES} minute(s)."
  sleep "${SLEEP_TIME}"
done