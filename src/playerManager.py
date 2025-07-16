import json
import os
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from settings import Settings
from backupManager import BackupManager


class PlayerManager:
    """Manages player data persistence and online status tracking."""
    
    def __init__(self, data_file="recent_players.json"):
        self.data_file = data_file
        self.players_data = self._load_players_data()
        self.backup_manager = BackupManager(
            data_file=self.data_file,
            backup_interval=getattr(Settings, 'playerDataBackupInterval', 3600),
            max_backups=getattr(Settings, 'playerDataMaxBackups', 24)
        )

    # Data Management Methods
    def _get_default_data(self) -> Dict[str, Any]:
        """Return default data structure."""
        return {"players": [], "last_updated": ""}

    def _validate_data_structure(self, data: Any) -> Dict[str, Any]:
        """Validate and fix data structure."""
        if not isinstance(data, dict):
            return self._get_default_data()
        
        if "players" not in data:
            data["players"] = []
        if "last_updated" not in data:
            data["last_updated"] = ""
        
        return data

    def _load_players_data(self, restoration_attempted=False) -> Dict[str, Any]:
        """Load player data from file with error handling."""
        try:
            if not os.path.exists(self.data_file):
                return self._get_default_data()
            
            # Check if file is corrupted before attempting to load
            if self._is_file_corrupted():
                logging.warning("Player data file appears to be corrupted, attempting automatic restoration")
                if not restoration_attempted and self._auto_restore_from_latest_backup():
                    # Try loading again after restoration (recursive call with flag)
                    logging.info("Backup restoration successful, reloading data...")
                    return self._load_players_data(restoration_attempted=True)
                else:
                    if restoration_attempted:
                        logging.error("Failed to restore from backup after 1 attempt, using default data")
                    else:
                        logging.error("Failed to restore from backup, using default data")
                    return self._get_default_data()
            
            # File is not corrupted, load normally
            with open(self.data_file, 'r', encoding='utf-8') as file:
                data = json.load(file)
            return self._validate_data_structure(data)
            
        except Exception as e:
            logging.error(f"Error loading player data: {e}")
            # Try to automatically restore from latest backup (only if not already attempted)
            if not restoration_attempted and self._auto_restore_from_latest_backup():
                try:
                    # Try loading again after restoration (recursive call with flag)
                    logging.info("Backup restoration successful, reloading data...")
                    return self._load_players_data(restoration_attempted=True)
                except Exception as restore_error:
                    logging.error(f"Error loading player data after backup restoration: {restore_error}")
                    return self._get_default_data()
            return self._get_default_data()

    def _auto_restore_from_latest_backup(self) -> bool:
        """Automatically restore from the latest available backup if the current file is damaged."""
        # Check if automatic backup restoration is enabled
        if not getattr(Settings, 'enableAutoBackupRestoration', True):
            logging.info("Automatic backup restoration is disabled in settings")
            return False
            
        try:
            available_backups = self.backup_manager.get_available_backups()
            if not available_backups:
                logging.warning("No backup files available for automatic restoration")
                return False
            
            latest_backup = available_backups[0]  # Backups are sorted in reverse order (newest first)
            logging.info(f"Attempting automatic restoration from latest backup: {latest_backup}")
            
            success = self.backup_manager.restore_from_backup(latest_backup)
            if success:
                logging.info(f"Successfully restored player data from backup: {latest_backup}")
                return True
            else:
                logging.error(f"Failed to restore from backup: {latest_backup}")
                return False
                
        except Exception as e:
            logging.error(f"Error during automatic backup restoration: {e}")
            return False

    def _is_file_corrupted(self) -> bool:
        """Check if the current players file is corrupted."""
        try:
            if not os.path.exists(self.data_file):
                return False  # File doesn't exist, not corrupted
            
            with open(self.data_file, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
            # Basic validation
            if not isinstance(data, dict):
                return True
            if "players" not in data:
                return True
            if not isinstance(data["players"], list):
                return True
                
            return False
        except (json.JSONDecodeError, UnicodeDecodeError, IOError):
            return True
        except Exception:
            return True

    def _save_players_data(self):
        """Save player data to file with error handling."""
        try:
            # Use BackupManager for backup
            if self.backup_manager.should_create_backup():
                self.backup_manager.create_backup()

            self.players_data["last_updated"] = datetime.now().isoformat()
            
            with open(self.data_file, 'w', encoding='utf-8') as file:
                json.dump(self.players_data, file, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Error saving player data: {e}")

    # Expose backup/restore methods for external use
    def restore_from_backup(self, backup_filename: str) -> bool:
        return self.backup_manager.restore_from_backup(backup_filename)

    def get_available_backups(self) -> List[str]:
        return self.backup_manager.get_available_backups()

    def restore_from_latest_backup(self) -> bool:
        """Manually restore from the latest available backup."""
        return self._auto_restore_from_latest_backup()

    def reload_players_data(self) -> bool:
        """Reload player data from file, with automatic backup restoration if needed."""
        try:
            self.players_data = self._load_players_data(restoration_attempted=False)
            return True
        except Exception as e:
            logging.error(f"Error reloading player data: {e}")
            return False

    def force_reload_players_data(self) -> bool:
        """Force reload player data from file, allowing another restoration attempt."""
        try:
            self.players_data = self._load_players_data(restoration_attempted=False)
            return True
        except Exception as e:
            logging.error(f"Error force reloading player data: {e}")
            return False

    # Time Conversion Methods
    def _timestamp_to_iso(self, timestamp: float) -> str:
        """Convert timestamp to ISO format string."""
        return datetime.fromtimestamp(timestamp).isoformat()

    def _iso_to_timestamp(self, iso_string: str, fallback: float) -> float:
        """Convert ISO string to timestamp with fallback."""
        if not iso_string:
            return fallback
        
        try:
            return datetime.fromisoformat(iso_string).timestamp()
        except (ValueError, TypeError):
            return fallback

    # Data Extraction Methods
    def _extract_player_info(self, player_info: List[str]) -> Optional[Dict[str, str]]:
        """Extract player information from server data."""
        if len(player_info) < 4:
            return None
        
        return {
            "name": player_info[0],
            "uid": player_info[1] if len(player_info) > 1 else "Unknown",
            "steam_id": player_info[2] if len(player_info) > 2 else "Unknown",
            "level": player_info[3] if len(player_info) > 3 else "Unknown"
        }

    def _extract_current_player_names(self, current_players: List[List[str]]) -> List[str]:
        """Extract list of currently online player names."""
        return [
            player_info[0] for player_info in current_players 
            if len(player_info) >= 4
        ]

    # Player Search Methods
    def _find_player_by_id(self, steam_id: str, uid: str) -> Optional[Dict[str, Any]]:
        """Find player by steam_id or uid."""
        for player in self.players_data["players"]:
            # First try to match by steam_id
            if steam_id != "Unknown" and player.get("steam_id") == steam_id:
                return player
            # Fallback to uid if steam_id is not available
            if uid != "Unknown" and player.get("uid") == uid:
                return player
        return None

    def _find_player_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find player by name (legacy method for backward compatibility)."""
        for player in self.players_data["players"]:
            if player["name"] == name:
                return player
        return None

    # Player State Management Methods
    def _is_player_offline(self, player: Dict[str, Any]) -> bool:
        """Check if player is currently offline."""
        return not player.get("currently_online", False)

    def _mark_player_offline(self, player: Dict[str, Any]):
        """Mark player as offline."""
        player["currently_online"] = False

    def _mark_player_online(self, player: Dict[str, Any]):
        """Mark player as online."""
        player["currently_online"] = True

    def _update_player_session(self, player: Dict[str, Any], current_time: float):
        """Update player's session timestamp."""
        player["last_seen"] = self._timestamp_to_iso(current_time)

    # Time Tracking Methods
    def _calculate_session_time(self, player: Dict[str, Any], current_time: float) -> int:
        """Calculate time since last check for a player."""
        last_check = self._iso_to_timestamp(player.get("last_seen", ""), current_time)
        return int(current_time - last_check)

    def _update_player_online_time(self, player: Dict[str, Any], current_time: float):
        """Update player's online time tracking."""
        session_time = self._calculate_session_time(player, current_time)
        current_total = int(player.get("total_online_seconds", 0))
        player["total_online_seconds"] = current_total + max(0, session_time)

    def _update_session_time_for_online_players(self, current_time: float, current_player_names: List[str]):
        """Update session time for all currently online players."""
        for player in self.players_data["players"]:
            if not player.get("currently_online"):
                continue
            
            self._update_player_online_time(player, current_time)
            
            if player["name"] not in current_player_names:
                self._mark_player_offline(player)
            else:
                self._update_player_session(player, current_time)

    # Player Creation and Update Methods
    def _create_player_base_data(self, player_info: Dict[str, str], current_time: float) -> Dict[str, Any]:
        """Create base player data structure."""
        return {
            "name": player_info["name"],
            "uid": player_info["uid"],
            "steam_id": player_info["steam_id"],
            "level": player_info["level"],
            "first_seen": self._timestamp_to_iso(current_time),
            "last_seen": self._timestamp_to_iso(current_time),
            "currently_online": True,
            "total_online_seconds": 0
        }

    def _create_new_player(self, player_info: Dict[str, str], current_time: float) -> Dict[str, Any]:
        """Create a new player record."""
        return self._create_player_base_data(player_info, current_time)

    def _update_player_basic_info(self, player: Dict[str, Any], player_info: Dict[str, str], current_time: float):
        """Update player's basic information."""
        player.update({
            "uid": player_info["uid"],
            "steam_id": player_info["steam_id"],
            "level": player_info["level"],
            "last_seen": self._timestamp_to_iso(current_time),
            "currently_online": True
        })

    def _update_existing_player(self, player: Dict[str, Any], player_info: Dict[str, str], current_time: float):
        """Update an existing player's information."""
        was_offline = self._is_player_offline(player)
        
        self._update_player_basic_info(player, player_info, current_time)
        
        if was_offline:
            self._update_player_session(player, current_time)

    # Player Merging Methods
    def _should_update_first_seen(self, existing_first_seen: str, new_timestamp: float) -> bool:
        """Determine if first_seen should be updated with earlier timestamp."""
        if not existing_first_seen:
            return True
        
        try:
            existing_timestamp = datetime.fromisoformat(existing_first_seen).timestamp()
            return new_timestamp < existing_timestamp
        except (ValueError, TypeError):
            return False

    def _merge_players(self, existing_player: Dict[str, Any], new_player_info: Dict[str, str], current_time: float):
        """Merge a new player entry with an existing player (handles name changes)."""
        was_offline = self._is_player_offline(existing_player)
        
        # Preserve earliest first_seen timestamp
        existing_first_seen = existing_player.get("first_seen", "")
        if self._should_update_first_seen(existing_first_seen, current_time):
            existing_player["first_seen"] = self._timestamp_to_iso(current_time)
        
        # Update other fields
        self._update_player_basic_info(existing_player, new_player_info, current_time)
        
        if was_offline:
            self._update_player_session(existing_player, current_time)

    # Player Processing Methods
    def _handle_existing_player(self, existing_player: Dict[str, Any], player_info: Dict[str, str], current_time: float):
        """Handle updating an existing player found by ID."""
        self._update_existing_player(existing_player, player_info, current_time)

    def _handle_name_collision(self, player_info: Dict[str, str], current_time: float):
        """Handle case where player has same name but different ID."""
        name_collision_player = self._find_player_by_name(player_info["name"])
        if name_collision_player:
            self._merge_players(name_collision_player, player_info, current_time)
            return True
        return False

    def _handle_new_player(self, player_info: Dict[str, str], current_time: float):
        """Handle creating a truly new player."""
        new_player = self._create_new_player(player_info, current_time)
        self.players_data["players"].append(new_player)

    def _process_single_player(self, player_info: List[str], current_time: float):
        """Process a single player from server data."""
        extracted_info = self._extract_player_info(player_info)
        if not extracted_info:
            return
        
        # Try to find existing player by ID first, then by name as fallback
        existing_player = self._find_player_by_id(extracted_info["steam_id"], extracted_info["uid"])
        
        if existing_player:
            self._handle_existing_player(existing_player, extracted_info, current_time)
        elif not self._handle_name_collision(extracted_info, current_time):
            self._handle_new_player(extracted_info, current_time)

    def _process_current_players(self, current_players: List[List[str]], current_time: float):
        """Process current players from server data."""
        for player_info in current_players:
            self._process_single_player(player_info, current_time)

    # Main Update Method
    def update_players_from_server(self, current_players: List[List[str]]):
        """Update player data from server information."""
        current_time = time.time()
        current_player_names = self._extract_current_player_names(current_players)
        
        self._update_session_time_for_online_players(current_time, current_player_names)
        self._process_current_players(current_players, current_time)
        self._save_players_data()

    # Public Query Methods
    def get_all_players(self) -> List[Dict[str, Any]]:
        """Get all players with copied data."""
        return [dict(player) for player in self.players_data["players"]]

    def get_online_players(self) -> List[Dict[str, Any]]:
        """Get currently online players."""
        return [player for player in self.get_all_players() if player["currently_online"]]

    def get_offline_players(self) -> List[Dict[str, Any]]:
        """Get currently offline players."""
        return [player for player in self.get_all_players() if not player["currently_online"]]

    def get_player_count(self) -> int:
        """Get count of online players."""
        return len(self.get_online_players())

    def get_total_player_count(self) -> int:
        """Get total count of all players."""
        return len(self.players_data["players"])

    def get_last_updated(self) -> str:
        """Get last updated timestamp."""
        return self.players_data.get("last_updated", "") 