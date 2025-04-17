#!/usr/bin/env python3
import json
import os
import shutil
import datetime
import argparse
import glob
import sys

def backup_database(source_file, backup_dir=None, max_backups=10):
    """Create a backup of the database file.
    
    Args:
        source_file (str): Path to the database file
        backup_dir (str): Directory to store backups (default: same as source)
        max_backups (int): Maximum number of backups to keep
    
    Returns:
        str: Path to the backup file or empty string on failure
    """
    if not os.path.exists(source_file):
        print(f"ERROR: Source file {source_file} does not exist")
        return ""
    
    # Set backup directory
    if not backup_dir:
        backup_dir = os.path.dirname(source_file) or "."
    
    # Create backup directory if it doesn't exist
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir, exist_ok=True)
    
    # Generate backup filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.basename(source_file)
    backup_file = os.path.join(backup_dir, f"{filename}.backup.{timestamp}")
    
    try:
        # Validate JSON before backing up
        with open(source_file, 'r') as f:
            data = json.load(f)
        
        # Create backup
        shutil.copy2(source_file, backup_file)
        print(f"Created backup: {backup_file}")
        
        # Clean up old backups if needed
        if max_backups > 0:
            pattern = os.path.join(backup_dir, f"{filename}.backup.*")
            backup_files = sorted(glob.glob(pattern))
            
            if len(backup_files) > max_backups:
                files_to_delete = backup_files[:-max_backups]
                for old_file in files_to_delete:
                    os.remove(old_file)
                    print(f"Removed old backup: {old_file}")
        
        return backup_file
    except json.JSONDecodeError:
        print(f"ERROR: Source file {source_file} is not valid JSON")
        return ""
    except Exception as e:
        print(f"ERROR: Failed to create backup: {str(e)}")
        return ""

def restore_database(backup_file, target_file):
    """Restore database from a backup file.
    
    Args:
        backup_file (str): Path to the backup file
        target_file (str): Path to restore to
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not os.path.exists(backup_file):
        print(f"ERROR: Backup file {backup_file} does not exist")
        return False
    
    try:
        # Validate JSON before restoring
        with open(backup_file, 'r') as f:
            data = json.load(f)
        
        # Create backup of current file if it exists
        if os.path.exists(target_file):
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            current_backup = f"{target_file}.before_restore.{timestamp}"
            shutil.copy2(target_file, current_backup)
            print(f"Backed up current file to: {current_backup}")
        
        # Restore from backup
        shutil.copy2(backup_file, target_file)
        print(f"Restored database from: {backup_file}")
        return True
    except json.JSONDecodeError:
        print(f"ERROR: Backup file {backup_file} is not valid JSON")
        return False
    except Exception as e:
        print(f"ERROR: Failed to restore database: {str(e)}")
        return False

def find_latest_backup(source_file, backup_dir=None):
    """Find the latest backup file.
    
    Args:
        source_file (str): Original database file path
        backup_dir (str): Directory containing backups
    
    Returns:
        str: Path to the latest backup file
    """
    if not backup_dir:
        backup_dir = os.path.dirname(source_file) or "."
    
    filename = os.path.basename(source_file)
    pattern = os.path.join(backup_dir, f"{filename}.backup.*")
    
    backup_files = sorted(glob.glob(pattern))
    
    if not backup_files:
        print("No backup files found")
        return ""
    
    latest = backup_files[-1]
    print(f"Latest backup: {latest}")
    return latest

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Database backup and restore utility")
    parser.add_argument("action", choices=["backup", "restore", "list"], help="Action to perform")
    parser.add_argument("--file", default="data/store_bot_db.json", help="Database file path")
    parser.add_argument("--backup-dir", help="Directory to store backups")
    parser.add_argument("--max-backups", type=int, default=10, help="Maximum number of backups to keep")
    parser.add_argument("--backup-file", help="Specific backup file to restore from")
    
    args = parser.parse_args()
    
    if args.action == "backup":
        result = backup_database(args.file, args.backup_dir, args.max_backups)
        if not result:
            sys.exit(1)
    
    elif args.action == "restore":
        if args.backup_file:
            backup_file = args.backup_file
        else:
            backup_file = find_latest_backup(args.file, args.backup_dir)
            if not backup_file:
                sys.exit(1)
        
        result = restore_database(backup_file, args.file)
        if not result:
            sys.exit(1)
    
    elif args.action == "list":
        if not args.backup_dir:
            args.backup_dir = os.path.dirname(args.file) or "."
        
        filename = os.path.basename(args.file)
        pattern = os.path.join(args.backup_dir, f"{filename}.backup.*")
        
        backup_files = sorted(glob.glob(pattern))
        
        if not backup_files:
            print("No backup files found")
        else:
            print(f"Found {len(backup_files)} backup(s):")
            for backup in backup_files:
                size = os.path.getsize(backup) / 1024  # KB
                modified = datetime.datetime.fromtimestamp(os.path.getmtime(backup))
                print(f"{backup} ({size:.1f} KB, {modified})") 