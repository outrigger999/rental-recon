"""
Backup service for database management
"""
import os
import shutil
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import json
from pathlib import Path

class BackupService:
    def __init__(self, db_path: str = "data/rentals.db", backup_dir: str = "backups"):
        self.db_path = db_path
        self.backup_dir = backup_dir
        self.config_file = os.path.join(backup_dir, "backup_config.json")
        self.ensure_backup_directory()
        
    def ensure_backup_directory(self):
        """Ensure backup directory exists"""
        os.makedirs(self.backup_dir, exist_ok=True)
        
    def get_backup_config(self) -> Dict:
        """Get backup configuration"""
        default_config = {
            "max_backups": 7,
            "auto_backup": True,
            "backup_interval": 86400,  # 24 hours in seconds
            "last_backup_time": None
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    return {**default_config, **config}
            except (json.JSONDecodeError, IOError):
                pass
                
        return default_config
    
    def save_backup_config(self, config: Dict):
        """Save backup configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def update_max_backups(self, max_backups: int) -> bool:
        """Update maximum number of backups to keep"""
        if not (1 <= max_backups <= 50):
            return False
            
        config = self.get_backup_config()
        config["max_backups"] = max_backups
        self.save_backup_config(config)
        
        # Clean up excess backups if needed
        self.cleanup_old_backups(max_backups)
        return True
    
    def create_backup(self) -> Dict:
        """Create a database backup"""
        if not os.path.exists(self.db_path):
            return {"success": False, "message": "Database file not found"}
        
        try:
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"rentals_backup_{timestamp}.db"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Copy the database file
            shutil.copy2(self.db_path, backup_path)
            
            # Update last backup time in config
            config = self.get_backup_config()
            config["last_backup_time"] = datetime.now().isoformat()
            self.save_backup_config(config)
            
            # Clean up old backups
            self.cleanup_old_backups()
            
            return {
                "success": True, 
                "message": f"Backup created successfully: {backup_filename}",
                "filename": backup_filename
            }
            
        except Exception as e:
            return {"success": False, "message": f"Backup failed: {str(e)}"}
    
    def get_backup_files(self) -> List[Dict]:
        """Get list of backup files with metadata"""
        backups = []
        
        if not os.path.exists(self.backup_dir):
            return backups
            
        for filename in os.listdir(self.backup_dir):
            if filename.startswith("rentals_backup_") and filename.endswith(".db"):
                filepath = os.path.join(self.backup_dir, filename)
                try:
                    stat = os.stat(filepath)
                    backups.append({
                        "filename": filename,
                        "size": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_mtime),
                        "size_mb": round(stat.st_size / (1024 * 1024), 2)
                    })
                except OSError:
                    continue
        
        # Sort by creation time, newest first
        backups.sort(key=lambda x: x["created"], reverse=True)
        return backups
    
    def cleanup_old_backups(self, max_backups: Optional[int] = None):
        """Remove old backup files beyond the maximum limit"""
        if max_backups is None:
            config = self.get_backup_config()
            max_backups = config["max_backups"]
        
        backups = self.get_backup_files()
        
        # Remove excess backups
        if len(backups) > max_backups:
            for backup in backups[max_backups:]:
                try:
                    filepath = os.path.join(self.backup_dir, backup["filename"])
                    os.remove(filepath)
                except OSError:
                    continue
    
    def delete_backup_files(self, filenames: List[str]) -> Dict:
        """Delete specific backup files"""
        deleted = []
        failed = []
        
        for filename in filenames:
            # Security check - ensure filename is a valid backup file
            if not (filename.startswith("rentals_backup_") and filename.endswith(".db")):
                failed.append(f"{filename}: Invalid backup filename")
                continue
                
            filepath = os.path.join(self.backup_dir, filename)
            
            if not os.path.exists(filepath):
                failed.append(f"{filename}: File not found")
                continue
                
            try:
                os.remove(filepath)
                deleted.append(filename)
            except OSError as e:
                failed.append(f"{filename}: {str(e)}")
        
        return {
            "deleted": deleted,
            "failed": failed,
            "success": len(failed) == 0
        }
    
    def get_backup_file_path(self, filename: str) -> Optional[str]:
        """Get full path to backup file if it exists and is valid"""
        # Security check
        if not (filename.startswith("rentals_backup_") and filename.endswith(".db")):
            return None
            
        filepath = os.path.join(self.backup_dir, filename)
        
        if os.path.exists(filepath):
            return filepath
            
        return None
    
    def get_last_backup_time(self) -> Optional[datetime]:
        """Get the last backup time from config"""
        config = self.get_backup_config()
        last_backup = config.get("last_backup_time")
        
        if last_backup:
            try:
                return datetime.fromisoformat(last_backup)
            except ValueError:
                pass
                
        return None
