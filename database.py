import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MongoDB connection variables
MONGO_URI = os.environ.get('MONGO_URI')
DB_NAME = 'telegram_storage_bot'
USERS_COLLECTION = 'users'

# Global connection objects
mongo_client = None
db = None
users_collection = None

# Database structure in MongoDB will be similar to the JSON structure:
# {
#   "_id": "user_id",
#   "categories": {
#     "category_name": [
#       {"message_id": 123, "file_type": "photo", "file_name": "example.jpg"},
#     ]
#   }
# }

def init_db() -> None:
    """Initialize the MongoDB connection if it's not already initialized."""
    global mongo_client, db, users_collection
    
    if not MONGO_URI:
        logger.error("MONGO_URI environment variable is not set!")
        raise ValueError("MONGO_URI environment variable must be set")
        
    try:
        if mongo_client is None:
            # Create a MongoDB client
            mongo_client = MongoClient(MONGO_URI)
            
            # Access the database
            db = mongo_client[DB_NAME]
            
            # Access the users collection
            users_collection = db[USERS_COLLECTION]
            
            # Create an index on user_id for faster lookups
            users_collection.create_index("_id")
            
            logger.info(f"Successfully connected to MongoDB database '{DB_NAME}'")
            
            # Test the connection
            mongo_client.admin.command('ping')
            logger.info("MongoDB connection verified with ping")
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {e}")
        raise

def get_user_data(user_id: int) -> Dict[str, Any]:
    """Get data for a specific user."""
    init_db()
    
    user_id_str = str(user_id)
    user_data = users_collection.find_one({"_id": user_id_str})
    
    if not user_data:
        # Create new user document if it doesn't exist
        user_data = {"_id": user_id_str, "categories": {}}
        users_collection.insert_one(user_data)
        logger.info(f"Created new user document for user {user_id}")
    
    return user_data

def get_user_categories(user_id: int) -> List[str]:
    """Get all categories for a user."""
    user_data = get_user_data(user_id)
    
    # Check if categories field exists
    if "categories" not in user_data:
        return []
    
    return list(user_data["categories"].keys())

def add_file_to_category(user_id: int, category: str, message_id: int, file_type: str, file_name: Optional[str] = None) -> None:
    """Add a file to a category."""
    init_db()
    user_id_str = str(user_id)
    
    # Prepare the file info
    file_info = {
        "message_id": message_id,
        "file_type": file_type,
    }
    
    if file_name:
        file_info["file_name"] = file_name
    
    # Update the user document - push the new file to the category array
    result = users_collection.update_one(
        {"_id": user_id_str},
        {
            "$push": {f"categories.{category}": file_info},
        },
        upsert=True
    )
    
    if result.modified_count > 0 or result.upserted_id:
        logger.info(f"Added file to category '{category}' for user {user_id}")
    else:
        logger.warning(f"Failed to add file to category '{category}' for user {user_id}")

def get_files_in_category(user_id: int, category: str) -> List[Dict[str, Any]]:
    """Get all files in a category."""
    user_data = get_user_data(user_id)
    
    if "categories" not in user_data or category not in user_data["categories"]:
        return []
    
    return user_data["categories"][category]

def get_files_in_category_paginated(user_id: int, category: str, page: int = 1, page_size: int = 5) -> Tuple[List[Dict[str, Any]], int, int]:
    """Get files in a category with pagination.
    
    Returns:
        Tuple containing (files_list, total_pages, total_files)
    """
    all_files = get_files_in_category(user_id, category)
    total_files = len(all_files)
    
    # Calculate total pages
    total_pages = (total_files + page_size - 1) // page_size if total_files > 0 else 1
    
    # Ensure page is within valid range
    page = max(1, min(page, total_pages))
    
    # Get files for the requested page
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total_files)
    
    return all_files[start_idx:end_idx], total_pages, total_files

def create_category(user_id: int, category: str) -> None:
    """Create a new category for a user."""
    init_db()
    user_id_str = str(user_id)
    
    # Check if the category already exists
    user_data = get_user_data(user_id)
    categories = user_data.get("categories", {})
    
    if category not in categories:
        # Update the user document to include the new empty category
        result = users_collection.update_one(
            {"_id": user_id_str},
            {"$set": {f"categories.{category}": []}},
            upsert=True
        )
        
        if result.modified_count > 0 or result.upserted_id:
            logger.info(f"Created category '{category}' for user {user_id}")
        else:
            logger.warning(f"Failed to create category '{category}' for user {user_id}")

def delete_category(user_id: int, category: str) -> bool:
    """Delete a category for a user."""
    init_db()
    user_id_str = str(user_id)
    
    # Check if the category exists
    user_data = get_user_data(user_id)
    if "categories" not in user_data or category not in user_data["categories"]:
        return False
    
    # Remove the category field
    result = users_collection.update_one(
        {"_id": user_id_str},
        {"$unset": {f"categories.{category}": ""}}
    )
    
    if result.modified_count > 0:
        logger.info(f"Deleted category '{category}' for user {user_id}")
        return True
    else:
        logger.warning(f"Failed to delete category '{category}' for user {user_id}")
        return False

def import_from_json(json_file_path: str) -> bool:
    """Import data from a JSON file into MongoDB.
    
    This is useful for migrating existing data from the old JSON format.
    
    Returns:
        bool: True if successful, False otherwise
    """
    import json
    
    try:
        # Read the JSON file
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        init_db()
        
        # Process each user in the JSON
        for user_id, user_data in data.get("users", {}).items():
            # Create a MongoDB document for this user
            mongo_user = {
                "_id": user_id,
                "categories": user_data.get("categories", {})
            }
            
            # Insert or update the user document
            users_collection.replace_one(
                {"_id": user_id},
                mongo_user,
                upsert=True
            )
        
        logger.info(f"Successfully imported data from {json_file_path}")
        return True
    except Exception as e:
        logger.error(f"Error importing data from JSON: {e}")
        return False

def export_to_json(json_file_path: str) -> bool:
    """Export data from MongoDB to a JSON file.
    
    This is useful for creating backups or migrating to another system.
    
    Returns:
        bool: True if successful, False otherwise
    """
    import json
    
    try:
        init_db()
        
        # Fetch all users
        all_users = list(users_collection.find({}))
        
        # Format into the expected structure
        export_data = {"users": {}}
        for user in all_users:
            user_id = user["_id"]
            export_data["users"][user_id] = {
                "categories": user.get("categories", {})
            }
        
        # Write to JSON file
        with open(json_file_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Successfully exported data to {json_file_path}")
        return True
    except Exception as e:
        logger.error(f"Error exporting data to JSON: {e}")
        return False

def close_connection():
    """Close the MongoDB connection."""
    global mongo_client
    if mongo_client:
        mongo_client.close()
        logger.info("MongoDB connection closed")
        mongo_client = None 