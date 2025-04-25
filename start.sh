#!/bin/bash

# Create data directory if it doesn't exist
mkdir -p /app/data
chmod 777 /app/data

# Set environment variable to indicate we're in Render
export RENDER=true

# Print debugging info
echo "Starting bot in Render environment"
echo "Using PORT: ${PORT:-10000}"
echo "Using HEALTH_PORT: ${HEALTH_PORT:-8080}"
echo "Render URL: ${RENDER_EXTERNAL_URL:-unknown}"

# Check if BOT_TOKEN is set
if [ -z "$BOT_TOKEN" ]; then
    echo "ERROR: BOT_TOKEN environment variable is not set!"
    exit 1
fi

# Check if MONGO_URI is set
if [ -z "$MONGO_URI" ]; then
    echo "ERROR: MONGO_URI environment variable is not set!"
    exit 1
fi

# Check if channel ID is set
if [ -z "$CHANNEL_ID" ]; then
    echo "WARNING: CHANNEL_ID environment variable is not set!"
fi

# Check data directory permissions (for exporting data if needed)
echo "Checking data directory permissions..."
ls -la /app/data
touch /app/data/permission_test && rm /app/data/permission_test
if [ $? -eq 0 ]; then
    echo "Data directory permissions OK"
else
    echo "WARNING: Cannot write to data directory!"
    echo "Attempting to fix permissions..."
    chmod -R 777 /app/data
fi

# Check MongoDB connection
echo "Checking MongoDB connection..."
python -c "
import os
from pymongo import MongoClient
try:
    client = MongoClient(os.environ.get('MONGO_URI'), serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print('MongoDB connection successful!')
except Exception as e:
    print(f'ERROR: MongoDB connection failed: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "MongoDB connection check failed. Please check your MONGO_URI."
    exit 1
fi

# Test health check server directly
echo "Testing health check server..."
python -c "
import os
import http.server
import socketserver
import threading
import time

HEALTH_PORT = int(os.environ.get('HEALTH_PORT', 8080))

class TestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'test_ok')
    
    def log_message(self, format, *args):
        return

try:
    print(f'Starting test server on port {HEALTH_PORT}')
    with socketserver.TCPServer(('', HEALTH_PORT), TestHandler) as httpd:
        print('Test server is running')
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        print('Test server started in thread')
        # Test if we can connect to our own server
        time.sleep(1)
        import urllib.request
        response = urllib.request.urlopen(f'http://localhost:{HEALTH_PORT}')
        print(f'Test response: {response.read().decode()}')
except Exception as e:
    print(f'Error in test health server: {e}')
"

# Delete any existing webhooks before starting
echo "Attempting to delete webhook..."
WEBHOOK_RESPONSE=$(curl -s "https://api.telegram.org/bot${BOT_TOKEN}/deleteWebhook")
if [ $? -eq 0 ]; then
    echo "Webhook deletion response: $WEBHOOK_RESPONSE"
else
    echo "Warning: Failed to delete webhook using curl. Will try again in the Python code."
fi

# Test bot token validity
echo "Testing bot token validity..."
BOT_INFO=$(curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getMe")
echo "Bot info: $BOT_INFO"

# For render, check if external URL is set
if [ -n "$RENDER_EXTERNAL_URL" ]; then
    echo "Render external URL is set to: $RENDER_EXTERNAL_URL"
    echo "Webhook path will be: $RENDER_EXTERNAL_URL/telegram"
else
    echo "Warning: RENDER_EXTERNAL_URL is not set. Webhook setup may fail."
fi

# Start the bot
echo "Starting the bot now..."
python bot.py 