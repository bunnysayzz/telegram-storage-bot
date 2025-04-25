#!/bin/bash

# Script to help set up environment variables for the Telegram Storage Bot
# Usage: ./setup_env.sh

echo "Telegram Storage Bot Environment Setup"
echo "======================================"
echo

# Check if .env file already exists
if [ -f .env ]; then
    echo "An .env file already exists. Do you want to create a new one? (y/n):"
    read answer
    if [ "$answer" != "y" ] && [ "$answer" != "Y" ]; then
        echo "Setup canceled. Your existing .env file was not modified."
        exit 0
    fi
    # Backup existing .env file
    cp .env .env.backup
    echo "Backed up existing .env file to .env.backup"
fi

echo "Please provide the following information:"
echo

# Ask for required environment variables
echo "Required Environment Variables:"
echo "------------------------------"

echo -n "Telegram Bot Token (from BotFather): "
read BOT_TOKEN

echo -n "Channel ID (where files will be stored): "
read CHANNEL_ID

echo -n "MongoDB URI: "
read MONGO_URI

# Ask for optional environment variables
echo
echo "Optional Environment Variables (press Enter to skip):"
echo "------------------------------"

echo -n "Telegram API ID: "
read TELEGRAM_API_ID

echo -n "API Hash: "
read API_HASH

echo -n "Channel First Message ID (default is 2): "
read CHANNEL_FIRST_MESSAGE_ID
CHANNEL_FIRST_MESSAGE_ID=${CHANNEL_FIRST_MESSAGE_ID:-2}

echo -n "Webhook server PORT (default is 10000): "
read PORT
PORT=${PORT:-10000}

echo -n "Health check server PORT (default is 8080): "
read HEALTH_PORT
HEALTH_PORT=${HEALTH_PORT:-8080}

# Create .env file
cat > .env << EOF
# Required Environment Variables
BOT_TOKEN=$BOT_TOKEN
CHANNEL_ID=$CHANNEL_ID
MONGO_URI=$MONGO_URI

EOF

# Add optional variables if provided
if [ -n "$TELEGRAM_API_ID" ]; then
    echo "TELEGRAM_API_ID=$TELEGRAM_API_ID" >> .env
fi

if [ -n "$API_HASH" ]; then
    echo "API_HASH=$API_HASH" >> .env
fi

echo "CHANNEL_FIRST_MESSAGE_ID=$CHANNEL_FIRST_MESSAGE_ID" >> .env
echo "PORT=$PORT" >> .env
echo "HEALTH_PORT=$HEALTH_PORT" >> .env

echo
echo "Environment variables have been saved to .env file."
echo "You can now run the bot using Docker or directly with Python."
echo

if [ -f migrate_data.sh ]; then
    echo "Do you want to migrate existing JSON data to MongoDB? (y/n):"
    read migrate_answer
    if [ "$migrate_answer" = "y" ] || [ "$migrate_answer" = "Y" ]; then
        echo "Running migration script..."
        chmod +x migrate_data.sh
        ./migrate_data.sh
    fi
fi

echo "Setup complete!" 