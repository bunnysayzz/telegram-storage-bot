import json
import os
import shutil
import logging
import time
from typing import Dict, List, Optional, Any, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database structure
# {
#   "users": {
#     "user_id": {
#       "categories": {
#         "category_name": [
#           {"message_id": 123, "file_type": "photo", "file_name": "example.jpg"},
#         ]
#       }
#     }
#   }
# }

# Use the persistent data directory when in Docker/Render
if os.environ.get('IS_DOCKER') == 'true' or os.environ.get('RENDER') == 'true':
    DATA_DIR = "data"
    # Create data directory if it doesn't exist
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
        logger.info(f"Created data directory at {os.path.abspath(DATA_DIR)}")
    
    DB_FILE = os.path.join(DATA_DIR, "store_bot_db.json")
    logger.info(f"Using database at {os.path.abspath(DB_FILE)}")
else:
    DB_FILE = "store_bot_db.json"
    logger.info(f"Using local database at {os.path.abspath(DB_FILE)}")

def init_db() -> None:
    """Initialize the database if it doesn't exist."""
    try:
        if not os.path.exists(DB_FILE):
            # Ensure directory exists
            dir_path = os.path.dirname(DB_FILE)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                logger.info(f"Created directory {dir_path} for database")
            
            # Create new DB file
            with open(DB_FILE, 'w') as f:
                json.dump({"users": {}}, f)
            logger.info(f"Initialized new database at {DB_FILE}")
        else:
            # Verify the file is valid JSON
            try:
                with open(DB_FILE, 'r') as f:
                    json.load(f)
                logger.info(f"Existing database found at {DB_FILE}")
            except json.JSONDecodeError:
                logger.error(f"Database file {DB_FILE} exists but contains invalid JSON")
                # Backup the broken file
                backup_file = f"{DB_FILE}.broken.{int(time.time())}"
                shutil.copy2(DB_FILE, backup_file)
                logger.info(f"Created backup of broken database at {backup_file}")
                
                # Create new DB file
                with open(DB_FILE, 'w') as f:
                    json.dump({"users": {}}, f)
                logger.info(f"Recreated database at {DB_FILE}")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

def get_db() -> Dict[str, Any]:
    """Get the current database."""
    try:
        init_db()
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading database: {e}")
        # Return empty database structure as fallback
        return {"users": {}}

def save_db(db: Dict[str, Any]) -> None:
    """Save the database."""
    try:
        # First create a temporary file
        temp_file = f"{DB_FILE}.temp"
        with open(temp_file, 'w') as f:
            json.dump(db, f, indent=2)
        
        # Then rename it to the actual file (atomic operation)
        os.replace(temp_file, DB_FILE)
        
        # Log the operation for debugging
        logger.debug(f"Database saved successfully to {DB_FILE}")
    except Exception as e:
        logger.error(f"Error saving database: {e}")
        raise

def get_user_data(user_id: int) -> Dict[str, Any]:
    """Get data for a specific user."""
    db = get_db()
    user_id_str = str(user_id)
    
    if user_id_str not in db["users"]:
        db["users"][user_id_str] = {"categories": {}}
        save_db(db)
    
    return db["users"][user_id_str]

def get_user_categories(user_id: int) -> List[str]:
    """Get all categories for a user."""
    user_data = get_user_data(user_id)
    return list(user_data["categories"].keys())

def add_file_to_category(user_id: int, category: str, message_id: int, file_type: str, file_name: Optional[str] = None) -> None:
    """Add a file to a category."""
    db = get_db()
    user_id_str = str(user_id)
    
    if user_id_str not in db["users"]:
        db["users"][user_id_str] = {"categories": {}}
    
    if category not in db["users"][user_id_str]["categories"]:
        db["users"][user_id_str]["categories"][category] = []
    
    file_info = {
        "message_id": message_id,
        "file_type": file_type,
    }
    
    if file_name:
        file_info["file_name"] = file_name
    
    db["users"][user_id_str]["categories"][category].append(file_info)
    save_db(db)
    logger.info(f"Added file to category '{category}' for user {user_id}")

def get_files_in_category(user_id: int, category: str) -> List[Dict[str, Any]]:
    """Get all files in a category."""
    user_data = get_user_data(user_id)
    
    if category not in user_data["categories"]:
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
    db = get_db()
    user_id_str = str(user_id)
    
    if user_id_str not in db["users"]:
        db["users"][user_id_str] = {"categories": {}}
    
    if category not in db["users"][user_id_str]["categories"]:
        db["users"][user_id_str]["categories"][category] = []
        save_db(db)

def delete_category(user_id: int, category: str) -> bool:
    """Delete a category for a user."""
    db = get_db()
    user_id_str = str(user_id)
    
    if (user_id_str in db["users"] and 
        category in db["users"][user_id_str]["categories"]):
        del db["users"][user_id_str]["categories"][category]
        save_db(db)
        return True
    
    return False

def backup_database() -> str:
    """Create a backup of the database file.
    
    Returns:
        The path to the backup file.
    """
    if not os.path.exists(DB_FILE):
        logger.warning(f"Cannot backup - database file {DB_FILE} does not exist")
        return ""
    
    timestamp = int(time.time())
    backup_file = f"{DB_FILE}.backup.{timestamp}"
    
    try:
        shutil.copy2(DB_FILE, backup_file)
        logger.info(f"Created database backup at {backup_file}")
        return backup_file
    except Exception as e:
        logger.error(f"Failed to create database backup: {e}")
        return "" 