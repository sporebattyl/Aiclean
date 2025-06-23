#!/usr/bin/with-contenv bashio

bashio::log.info "Starting Roo AI Cleaning Assistant..."

# Read configuration into variables
CAMERA_ENTITY=$(bashio::config 'camera_entity')
API_KEY=$(bashio::config 'gemini_api_key')
TODO_LIST=$(bashio::config 'todo_list_entity')
# Default to 24 hours if not set, convert hours to seconds
FREQUENCY=$(bashio::config.get 'update_frequency' 24)
SLEEP_TIME=$((FREQUENCY * 3600))

# Main execution loop
while true; do
  bashio::log.info "Running cleanliness analysis..."

  # Export variables for the Python script to access
  export CAMERA_ENTITY API_KEY TODO_LIST

  # Execute the main Python application
  python3 /app/aicleaner.py

  bashio::log.info "Analysis complete. Sleeping for ${FREQUENCY} hour(s)."
  sleep "${SLEEP_TIME}"
done