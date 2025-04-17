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

# Check if channel ID is set
if [ -z "$CHANNEL_ID" ]; then
    echo "WARNING: CHANNEL_ID environment variable is not set!"
fi

# Check database directory permissions
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

# Check if database exists
DB_FILE="/app/data/store_bot_db.json"
if [ -f "$DB_FILE" ]; then
    echo "Database file found: $DB_FILE"
    # Backup existing database
    BACKUP_FILE="${DB_FILE}.backup.$(date +%s)"
    cp "$DB_FILE" "$BACKUP_FILE"
    echo "Created database backup: $BACKUP_FILE"
    # Verify database is valid JSON
    python -c "import json; json.load(open('$DB_FILE'))" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "WARNING: Database file is not valid JSON!"
        echo "Attempting to restore from backup..."
        find /app/data -name "store_bot_db.json.backup.*" -type f | sort -r | head -n 1 | xargs -I {} cp {} "$DB_FILE"
        python -c "import json; json.load(open('$DB_FILE'))" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "Successfully restored database from backup"
        else
            echo "ERROR: Could not restore database from backup!"
            echo "Creating new empty database..."
            echo '{"users":{}}' > "$DB_FILE"
        fi
    fi
else
    echo "No database file found. Will create a new one."
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