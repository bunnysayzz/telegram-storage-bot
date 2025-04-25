import os
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MongoDB connection string
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://azharsayzz:Azhar@70@cluster0.0encvzq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')

# Database and collection names
DB_NAME = "telegram_storage_bot"
USERS_COLLECTION = "users"

# Global client variable
mongo_client = None
db = None

def get_mongo_client():
    """Get or create MongoDB client."""
    global mongo_client, db
    
    if mongo_client is None:
        try:
            # Create a new client and connect to the server
            mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            
            # Verify the connection
            mongo_client.admin.command('ping')
            logger.info("Connected successfully to MongoDB")
            
            # Get database
            db = mongo_client[DB_NAME]
            return mongo_client
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"MongoDB Connection error: {e}")
            raise
    
    return mongo_client

def get_db():
    """Get the MongoDB database object."""
    global db
    if db is None:
        get_mongo_client()
    return db

def init_db() -> None:
    """Initialize the database connection."""
    try:
        # Get the MongoDB client
        client = get_mongo_client()
        
        # Create indexes if needed
        db = get_db()
        users_collection = db[USERS_COLLECTION]
        
        # Create index on user_id for faster lookups
        users_collection.create_index("user_id")
        
        logger.info(f"Database initialized: {DB_NAME}")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

def get_user_data(user_id: int) -> Dict[str, Any]:
    """Get data for a specific user."""
    users_collection = get_db()[USERS_COLLECTION]
    
    user_id_str = str(user_id)
    user_data = users_collection.find_one({"user_id": user_id_str})
    
    if not user_data:
        # Create new user entry if it doesn't exist
        user_data = {
            "user_id": user_id_str,
            "categories": {}
        }
        users_collection.insert_one(user_data)
        logger.info(f"Created new user record for user_id: {user_id_str}")
    
    return user_data

def get_user_categories(user_id: int) -> List[str]:
    """Get all categories for a user."""
    user_data = get_user_data(user_id)
    
    if "categories" not in user_data:
        return []
    
    return list(user_data["categories"].keys())

def add_file_to_category(user_id: int, category: str, message_id: int, file_type: str, file_name: Optional[str] = None) -> None:
    """Add a file to a category."""
    users_collection = get_db()[USERS_COLLECTION]
    user_id_str = str(user_id)
    
    # Prepare file info
    file_info = {
        "message_id": message_id,
        "file_type": file_type,
    }
    
    if file_name:
        file_info["file_name"] = file_name
    
    # Update the user record
    users_collection.update_one(
        {"user_id": user_id_str},
        {
            "$push": {f"categories.{category}": file_info},
            "$setOnInsert": {"user_id": user_id_str}
        },
        upsert=True
    )
    
    logger.info(f"Added file to category '{category}' for user {user_id}")

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
    users_collection = get_db()[USERS_COLLECTION]
    user_id_str = str(user_id)
    
    # Check if category already exists
    user_data = get_user_data(user_id)
    if "categories" in user_data and category in user_data["categories"]:
        # Category already exists, no need to create it again
        return
    
    # Create the category with an empty array
    users_collection.update_one(
        {"user_id": user_id_str},
        {
            "$set": {f"categories.{category}": []},
            "$setOnInsert": {"user_id": user_id_str}
        },
        upsert=True
    )
    
    logger.info(f"Created new category '{category}' for user {user_id}")

def delete_category(user_id: int, category: str) -> bool:
    """Delete a category for a user."""
    users_collection = get_db()[USERS_COLLECTION]
    user_id_str = str(user_id)
    
    # Check if category exists before deleting
    user_data = get_user_data(user_id)
    if "categories" not in user_data or category not in user_data["categories"]:
        return False
    
    # Remove the category
    result = users_collection.update_one(
        {"user_id": user_id_str},
        {"$unset": {f"categories.{category}": ""}}
    )
    
    return result.modified_count > 0

def backup_database() -> str:
    """Create a backup of the database by exporting MongoDB data to a JSON file.
    
    Returns:
        The path to the backup file.
    """
    try:
        # Create data directory if it doesn't exist
        backup_dir = "data"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir, exist_ok=True)
        
        # Generate timestamp for the backup file
        timestamp = int(time.time())
        backup_file = os.path.join(backup_dir, f"mongodb_backup_{timestamp}.json")
        
        # Get all user data from MongoDB
        users_collection = get_db()[USERS_COLLECTION]
        users_data = list(users_collection.find({}, {"_id": 0}))  # Exclude MongoDB _id field
        
        # Save to file
        with open(backup_file, 'w') as f:
            import json
            json.dump({"users": users_data}, f, indent=2)
        
        logger.info(f"Created MongoDB database backup at {backup_file}")
        return backup_file
    except Exception as e:
        logger.error(f"Failed to create database backup: {e}")
        return "" 