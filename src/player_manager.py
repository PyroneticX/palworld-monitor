from typing import List, Dict, Any, Optional
from settings import settings
import json
import os
import time

class PlayerManager:
    """Manages player data including online and offline players with timestamps."""
    
    def __init__(self):
        self.players = {}  # Single dict: {steam_id: player_data}
        self.data_file = os.path.join('data', 'players.json')
        self.version = 1
        self._load_player_data()
    
    def _load_player_data(self):
        """Load player data from JSON file. Migrate if needed."""
        try:
            data = self._load_raw_player_data()
            if data is None:
                self.players = {}
                return
            if self._is_migration_needed(data):
                self.players = self._migrate_uid_to_steamid(data)
                self._save_player_data()
            else:
                self.players = data.get('players', {})
        except Exception as e:
            print(f"Error loading player data: {e}")
            self.players = {}

    def _load_raw_player_data(self) -> Optional[dict]:
        """Load and return raw player data from file, or None if not found."""
        if not os.path.exists(self.data_file):
            return None
        with open(self.data_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _is_migration_needed(self, data: dict) -> bool:
        """Return True if migration from uid to steam_id is needed."""
        file_version = data.get('version')
        return not file_version or file_version < 1

    def _migrate_uid_to_steamid(self, data: dict) -> dict:
        """Migrate player data from uid-keyed to steam_id-keyed dict."""
        old_players = data.get('players', {})
        new_players = {}
        for player in old_players.values():
            steam_id = player.get('steam_id')
            if steam_id and steam_id != 'Unknown':
                player.pop('uid', None)
                new_players[steam_id] = player
        return new_players

    def _save_player_data(self):
        """Save player data to JSON file with versioning."""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'version': self.version,
                    'players': self.players
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving player data: {e}")

    def _extract_player_info(self, player_info: List[str]) -> Optional[Dict[str, str]]:
        """Extract player information from server data."""
        if len(player_info) < 4:
            return None
        return {
            "name": player_info[0],
            # 'uid' is ignored for storage, but can be included for compatibility if needed
            "steam_id": player_info[2] if len(player_info) > 2 else "Unknown",
            "level": player_info[3] if len(player_info) > 3 else "Unknown"
        }

    def update_players_from_server(self, current_players: List[List[str]]):
        """Update player data from server information - tracks online/offline status."""
        if not settings.enablePlayerTracking:
            self.players = {}
            self._save_player_data()
            return
        current_time = time.time()
        current_player_steam_ids = set()
        # Update current online players
        for player_info in current_players:
            extracted_info = self._extract_player_info(player_info)
            if extracted_info and extracted_info['steam_id'] != "Unknown":
                steam_id = extracted_info['steam_id']
                current_player_steam_ids.add(steam_id)
                # Update or add player as online
                self.players[steam_id] = {
                    **extracted_info,
                    'currently_online': True,
                    'last_online': current_time
                }
        # Mark players as offline if they're not in current list
        for steam_id, player_data in self.players.items():
            if steam_id not in current_player_steam_ids:
                player_data['currently_online'] = False
        self._save_player_data()

    def get_all_players(self) -> List[Dict[str, Any]]:
        """Get all players (online and offline) with their status."""
        return [dict(player_data) for player_data in self.players.values()]

    def get_online_players(self) -> List[Dict[str, Any]]:
        """Get currently online players."""
        return [dict(player_data) for player_data in self.players.values() if player_data.get('currently_online', False)]

    def get_offline_players(self) -> List[Dict[str, Any]]:
        """Get currently offline players with last online timestamps."""
        return [dict(player_data) for player_data in self.players.values() if not player_data.get('currently_online', False)]

    def get_player_count(self) -> int:
        """Get count of online players."""
        return len([p for p in self.players.values() if p.get('currently_online', False)])

    def get_total_player_count(self) -> int:
        """Get total count of all players (online + offline)."""
        return len(self.players) 