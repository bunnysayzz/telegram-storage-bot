#!/usr/bin/env python3
"""
MongoDB Migration Script

This script migrates data from the JSON file database to MongoDB.
Run this once to transfer existing data to MongoDB.
"""

import os
import sys
import json
import logging
from dotenv import load_dotenv
from pymongo import MongoClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def migrate_json_to_mongodb(json_file_path, mongo_uri=None):
    """Migrate data from JSON file to MongoDB.
    
    Args:
        json_file_path (str): Path to the JSON database file
        mongo_uri (str, optional): MongoDB connection URI. If not provided, uses MONGO_URI env variable.
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Get MongoDB URI
    mongo_uri = mongo_uri or os.environ.get('MONGO_URI')
    if not mongo_uri:
        logger.error("No MongoDB URI provided. Set MONGO_URI environment variable or pass as parameter.")
        return False
    
    # Check if JSON file exists
    if not os.path.exists(json_file_path):
        logger.error(f"JSON file not found: {json_file_path}")
        return False
    
    try:
        # Read JSON data
        logger.info(f"Reading data from {json_file_path}")
        with open(json_file_path, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in {json_file_path}")
                return False
        
        # Connect to MongoDB
        logger.info(f"Connecting to MongoDB...")
        client = MongoClient(mongo_uri)
        
        # Test connection
        client.admin.command('ping')
        logger.info("MongoDB connection successful")
        
        # Set up database and collection
        db = client['telegram_storage_bot']
        users_collection = db['users']
        
        # Count users in JSON
        user_count = len(data.get('users', {}))
        logger.info(f"Found {user_count} users in JSON data")
        
        # Count categories and files
        category_count = 0
        file_count = 0
        for user_id, user_data in data.get('users', {}).items():
            categories = user_data.get('categories', {})
            category_count += len(categories)
            for category, files in categories.items():
                file_count += len(files)
        
        logger.info(f"Found {category_count} categories and {file_count} files in JSON data")
        
        # Process each user in the JSON
        migrated_users = 0
        for user_id, user_data in data.get('users', {}).items():
            # Create document for MongoDB
            mongo_user = {
                '_id': user_id,
                'categories': user_data.get('categories', {})
            }
            
            # Insert or update the user document
            result = users_collection.replace_one(
                {'_id': user_id},
                mongo_user,
                upsert=True
            )
            
            if result.modified_count > 0 or result.upserted_id:
                migrated_users += 1
        
        logger.info(f"Migration complete: {migrated_users} users migrated to MongoDB")
        
        # Create index for faster lookups
        users_collection.create_index('_id')
        logger.info("Created index on _id field")
        
        return True
    
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        return False

if __name__ == "__main__":
    # Determine the JSON file path
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
    else:
        # Use default paths
        if os.path.exists('data/store_bot_db.json'):
            json_path = 'data/store_bot_db.json'
        elif os.path.exists('store_bot_db.json'):
            json_path = 'store_bot_db.json'
        else:
            logger.error("No JSON database file found. Please specify the path as an argument.")
            sys.exit(1)
    
    # Run the migration
    logger.info(f"Starting migration from {json_path} to MongoDB")
    if migrate_json_to_mongodb(json_path):
        logger.info("Migration completed successfully!")
        sys.exit(0)
    else:
        logger.error("Migration failed!")
        sys.exit(1) 