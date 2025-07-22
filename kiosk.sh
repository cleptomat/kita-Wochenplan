#!/bin/bash

# Wait for the desktop to load
sleep 10

# Start the Flask application
/home/admin/Desktop/terminplan/start_app.sh

# Wait for Flask to start up
sleep 5

# Hide cursor and start Chromium in kiosk mode
unclutter -idle 0.5 -root &

# Start Chromium in kiosk mode
chromium-browser \
  --noerrdialogs \
  --disable-infobars \
  --kiosk \
  --disable-session-crashed-bubble \
  --disable-background-timer-throttling \
  --disable-backgrounding-occluded-windows \
  --disable-renderer-backgrounding \
  --disable-features=TranslateUI \
  --disable-ipc-flooding-protection \
  --disable-popup-blocking \
  --disable-prompt-on-repost \
  --no-first-run \
  --fast \
  --fast-start \
  --disable-default-apps \
  --no-default-browser-check \
  --disable-translate \
  --disable-features=VizDisplayCompositor \
  --disable-dev-shm-usage \
  --disable-gpu-sandbox \
  --enable-features=OverlayScrollbar \
  --start-fullscreen \
  http://localhost:5000
