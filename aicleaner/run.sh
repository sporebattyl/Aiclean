#!/usr/bin/with-contenv bashio

bashio::log.info "Starting Roo AI Cleaning Assistant v2.0 in LIVE RELOAD mode..."

# Execute from the mapped directory for live reloading
# This allows changes to the Python source code to be reflected immediately
python3 /addons/aiclean/aicleaner/aicleaner.py