#!/bin/bash

# Create data directory if it doesn't exist
mkdir -p /app/data

# Set environment variable to indicate we're in Render
export RENDER=true

# Print debugging info
echo "Starting bot in Render environment"
echo "Using PORT: ${PORT:-10000}"
echo "Render URL: ${RENDER_EXTERNAL_URL:-unknown}"

# Check if BOT_TOKEN is set
if [ -z "$BOT_TOKEN" ]; then
    echo "ERROR: BOT_TOKEN environment variable is not set!"
    exit 1
fi

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