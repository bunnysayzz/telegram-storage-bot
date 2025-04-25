#!/usr/bin/env python3
import json
import os
import shutil
import datetime
import argparse
import glob
import sys
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection settings
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://azharsayzz:Azhar@70@cluster0.0encvzq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
DB_NAME = "telegram_storage_bot"
USERS_COLLECTION = "users"

def get_mongo_client():
    """Get a MongoDB client connection."""
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Test connection
        client.admin.command('ping')
        print("Connected successfully to MongoDB")
        return client
    except Exception as e:
        print(f"ERROR: MongoDB connection failed: {e}")
        return None

def backup_mongodb(backup_dir=None, max_backups=10):
    """Create a backup of the MongoDB database.
    
    Args:
        backup_dir (str): Directory to store backups (default: ./data)
        max_backups (int): Maximum number of backups to keep
    
    Returns:
        str: Path to the backup file or empty string on failure
    """
    # Connect to MongoDB
    client = get_mongo_client()
    if client is None:
        return ""
    
    # Set backup directory
    if not backup_dir:
        backup_dir = "data"
    
    # Create backup directory if it doesn't exist
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir, exist_ok=True)
    
    # Generate backup filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f"mongodb_backup_{timestamp}.json")
    
    try:
        # Export all data from users collection
        db = client[DB_NAME]
        users_collection = db[USERS_COLLECTION]
        
        users_data = list(users_collection.find({}, {"_id": 0}))  # Exclude MongoDB _id field
        
        # Save to file
        with open(backup_file, 'w') as f:
            json.dump({"users": users_data}, f, indent=2)
            
        print(f"Created MongoDB backup: {backup_file}")
        
        # Clean up old backups if needed
        if max_backups > 0:
            pattern = os.path.join(backup_dir, "mongodb_backup_*.json")
            backup_files = sorted(glob.glob(pattern))
            
            if len(backup_files) > max_backups:
                files_to_delete = backup_files[:-max_backups]
                for old_file in files_to_delete:
                    os.remove(old_file)
                    print(f"Removed old backup: {old_file}")
        
        return backup_file
    except Exception as e:
        print(f"ERROR: Failed to create MongoDB backup: {str(e)}")
        return ""
    finally:
        client.close()

def restore_mongodb(backup_file):
    """Restore MongoDB database from a backup file.
    
    Args:
        backup_file (str): Path to the backup file
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not os.path.exists(backup_file):
        print(f"ERROR: Backup file {backup_file} does not exist")
        return False
    
    # Connect to MongoDB
    client = get_mongo_client()
    if client is None:
        return False
    
    try:
        # Load backup data
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
        
        if "users" not in backup_data:
            print(f"ERROR: Invalid backup format in {backup_file}")
            return False
        
        # Get database and collection
        db = client[DB_NAME]
        users_collection = db[USERS_COLLECTION]
        
        # Create a backup of current data
        current_backup = backup_mongodb(max_backups=5)
        if current_backup:
            print(f"Created backup of current data before restore: {current_backup}")
        
        # Clear current collection data
        users_collection.delete_many({})
        
        # Insert backup data
        users = backup_data["users"]
        if users:
            users_collection.insert_many(users)
            print(f"Restored {len(users)} user records from backup")
        else:
            print("Backup contained no user records")
        
        return True
    except json.JSONDecodeError:
        print(f"ERROR: Backup file {backup_file} is not valid JSON")
        return False
    except Exception as e:
        print(f"ERROR: Failed to restore MongoDB database: {str(e)}")
        return False
    finally:
        client.close()

def backup_database(source_file, backup_dir=None, max_backups=10):
    """Legacy function for file-based backups, redirects to MongoDB backup."""
    print("NOTE: Using MongoDB backup instead of file-based backup")
    return backup_mongodb(backup_dir, max_backups)

def restore_database(backup_file, target_file):
    """Legacy function for file-based restores, redirects to MongoDB restore."""
    print("NOTE: Using MongoDB restore instead of file-based restore")
    return restore_mongodb(backup_file)

def find_latest_backup(source_file=None, backup_dir=None):
    """Find the latest backup file.
    
    Args:
        source_file (str): Ignored, maintained for compatibility
        backup_dir (str): Directory containing backups
    
    Returns:
        str: Path to the latest backup file
    """
    if not backup_dir:
        backup_dir = "data"
    
    pattern = os.path.join(backup_dir, "mongodb_backup_*.json")
    
    backup_files = sorted(glob.glob(pattern))
    
    if not backup_files:
        print("No MongoDB backup files found")
        return ""
    
    latest = backup_files[-1]
    print(f"Latest MongoDB backup: {latest}")
    return latest

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MongoDB backup and restore utility for Telegram Storage Bot")
    parser.add_argument("action", choices=["backup", "restore", "list"], help="Action to perform")
    parser.add_argument("--backup-dir", default="data", help="Directory to store backups")
    parser.add_argument("--max-backups", type=int, default=10, help="Maximum number of backups to keep")
    parser.add_argument("--backup-file", help="Specific backup file to restore from")
    parser.add_argument("--file", help="Legacy parameter, ignored", default=None)
    
    args = parser.parse_args()
    
    if args.action == "backup":
        result = backup_mongodb(args.backup_dir, args.max_backups)
        if not result:
            sys.exit(1)
    
    elif args.action == "restore":
        if args.backup_file:
            backup_file = args.backup_file
        else:
            backup_file = find_latest_backup(None, args.backup_dir)
            if not backup_file:
                sys.exit(1)
        
        result = restore_mongodb(backup_file)
        if not result:
            sys.exit(1)
    
    elif args.action == "list":
        if not args.backup_dir:
            args.backup_dir = "data"
        
        pattern = os.path.join(args.backup_dir, "mongodb_backup_*.json")
        
        backup_files = sorted(glob.glob(pattern))
        
        if not backup_files:
            print("No MongoDB backup files found")
        else:
            print(f"Found {len(backup_files)} MongoDB backup(s):")
            for backup in backup_files:
                size = os.path.getsize(backup) / 1024  # KB
                modified = datetime.datetime.fromtimestamp(os.path.getmtime(backup))
                print(f"{backup} ({size:.1f} KB, {modified})") 