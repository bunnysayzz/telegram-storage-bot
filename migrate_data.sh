#!/bin/bash

# Script to migrate data from JSON to MongoDB
# Usage: ./migrate_data.sh [json_file_path]

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
fi

# Check if MONGO_URI is set
if [ -z "$MONGO_URI" ]; then
    echo "ERROR: MONGO_URI environment variable is not set!"
    echo "Please set it in your .env file or export it directly:"
    echo "export MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/database"
    exit 1
fi

# Determine JSON file path
JSON_FILE=""
if [ -n "$1" ]; then
    JSON_FILE="$1"
elif [ -f "store_bot_db.json" ]; then
    JSON_FILE="store_bot_db.json"
elif [ -f "data/store_bot_db.json" ]; then
    JSON_FILE="data/store_bot_db.json"
else
    echo "ERROR: Cannot find JSON database file."
    echo "Please specify the path to your store_bot_db.json file:"
    echo "./migrate_data.sh path/to/store_bot_db.json"
    exit 1
fi

echo "Will migrate data from: $JSON_FILE to MongoDB"
echo "Using MongoDB URI: ${MONGO_URI:0:30}..."

# Check if the JSON file exists and is readable
if [ ! -f "$JSON_FILE" ]; then
    echo "ERROR: File $JSON_FILE does not exist!"
    exit 1
fi

if [ ! -r "$JSON_FILE" ]; then
    echo "ERROR: Cannot read file $JSON_FILE!"
    exit 1
fi

# Run the migration script
echo "Starting migration..."
python migrate_to_mongodb.py "$JSON_FILE"

# Check if migration was successful
if [ $? -eq 0 ]; then
    echo "✅ Migration completed successfully!"
    echo ""
    echo "Your data has been migrated to MongoDB. You can now use the bot with MongoDB storage."
    echo "If you want to backup your old JSON file, run:"
    echo "mv $JSON_FILE ${JSON_FILE}.bak"
else
    echo "❌ Migration failed!"
    echo "Please check the error messages above and try again."
    exit 1
fi 