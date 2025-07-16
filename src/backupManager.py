import os
import shutil
import logging
from datetime import datetime
from typing import List

class BackupManager:
    def __init__(self, data_file: str, backup_interval: int = 3600, max_backups: int = 24, backup_dir: str = "backups"):
        self.data_file = data_file
        self.backup_interval = backup_interval
        self.max_backups = max_backups
        self.backup_dir = backup_dir
        self.last_backup_time = 0

    def _create_backup_directory(self) -> str:
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
        return self.backup_dir

    def _get_backup_filename(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"recent_players_backup_{timestamp}.json"

    def should_create_backup(self) -> bool:
        import time
        current_time = time.time()
        return (current_time - self.last_backup_time) >= self.backup_interval

    def create_backup(self):
        try:
            if not os.path.exists(self.data_file):
                logging.info("No player data file to backup")
                return
            backup_dir = self._create_backup_directory()
            backup_filename = self._get_backup_filename()
            backup_path = os.path.join(backup_dir, backup_filename)
            shutil.copy2(self.data_file, backup_path)
            import time
            self.last_backup_time = time.time()
            logging.info(f"Created backup: {backup_path}")
            self.cleanup_old_backups()
        except Exception as e:
            logging.error(f"Error creating backup: {e}")

    def cleanup_old_backups(self):
        try:
            backup_files = []
            for filename in os.listdir(self.backup_dir):
                if filename.startswith("recent_players_backup_") and filename.endswith(".json"):
                    file_path = os.path.join(self.backup_dir, filename)
                    backup_files.append((file_path, os.path.getmtime(file_path)))
            backup_files.sort(key=lambda x: x[1])
            if len(backup_files) > self.max_backups:
                files_to_remove = len(backup_files) - self.max_backups
                for i in range(files_to_remove):
                    try:
                        os.remove(backup_files[i][0])
                        logging.info(f"Removed old backup: {backup_files[i][0]}")
                    except Exception as e:
                        logging.error(f"Error removing old backup {backup_files[i][0]}: {e}")
        except Exception as e:
            logging.error(f"Error cleaning up old backups: {e}")

    def restore_from_backup(self, backup_filename: str) -> bool:
        try:
            backup_path = os.path.join(self.backup_dir, backup_filename)
            if not os.path.exists(backup_path):
                logging.error(f"Backup file not found: {backup_path}")
                return False
            # Create a backup of current file before restoring
            if os.path.exists(self.data_file):
                current_backup = f"recent_players_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                current_backup_path = os.path.join(self.backup_dir, current_backup)
                shutil.copy2(self.data_file, current_backup_path)
                logging.info(f"Created backup of current file before restore: {current_backup_path}")
            shutil.copy2(backup_path, self.data_file)
            logging.info(f"Successfully restored from backup: {backup_path}")
            return True
        except Exception as e:
            logging.error(f"Error restoring from backup: {e}")
            return False

    def get_available_backups(self) -> List[str]:
        try:
            if not os.path.exists(self.backup_dir):
                return []
            backup_files = []
            for filename in os.listdir(self.backup_dir):
                if filename.startswith("recent_players_backup_") and filename.endswith(".json"):
                    backup_files.append(filename)
            backup_files.sort(reverse=True)
            return backup_files
        except Exception as e:
            logging.error(f"Error getting available backups: {e}")
            return [] 