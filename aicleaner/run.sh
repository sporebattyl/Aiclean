#!/usr/bin/with-contenv bashio

bashio::log.info "Starting AICleaner v2.0 in LIVE RELOAD mode..."

# Start a simple HTTP server for static files in the background
bashio::log.info "Starting static file server for Lovelace cards..."
cd /addons/Aiclean/aicleaner/www && python3 -m http.server 8099 &

# Execute from the mapped directory for live reloading
# This allows changes to the Python source code to be reflected immediately
bashio::log.info "Starting main AICleaner application..."
cd /addons/Aiclean/aicleaner && python3 aicleaner.py