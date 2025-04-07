#!/bin/bash

# Create data directory if it doesn't exist
mkdir -p /app/data

# Set environment variable to indicate we're in Render
export RENDER=true

# Print debugging info
echo "Starting bot in Render environment"
echo "Using PORT: ${PORT:-10000}"
echo "Render URL: ${RENDER_EXTERNAL_URL:-unknown}"

# Delete any existing webhooks before starting
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/deleteWebhook"
echo "Deleted any existing webhook"

# Start the bot
python bot.py 