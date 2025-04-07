import json
import os
from typing import Dict, List, Optional, Any, Tuple

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

DB_FILE = "store_bot_db.json"

def init_db() -> None:
    """Initialize the database if it doesn't exist."""
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f:
            json.dump({"users": {}}, f)

def get_db() -> Dict[str, Any]:
    """Get the current database."""
    init_db()
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_db(db: Dict[str, Any]) -> None:
    """Save the database."""
    with open(DB_FILE, 'w') as f:
        json.dump(db, f, indent=2)

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