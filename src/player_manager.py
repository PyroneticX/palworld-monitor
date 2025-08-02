from typing import List, Dict, Any, Optional
from settings import Settings
import json
import os
import time
from datetime import datetime


class PlayerManager:
    """Manages player data including online and offline players with timestamps."""
    
    def __init__(self):
        self.online_players = []  # List of currently online players only
        self.offline_players = {}  # Dict of offline players with last online timestamps
        self.data_file = os.path.join('data', 'players.json')
        self._load_player_data()
    
    def _load_player_data(self):
        """Load player data from JSON file."""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.offline_players = data.get('offline_players', {})
        except Exception as e:
            print(f"Error loading player data: {e}")
            self.offline_players = {}
    
    def _save_player_data(self):
        """Save player data to JSON file."""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'offline_players': self.offline_players
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving player data: {e}")

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

    def update_players_from_server(self, current_players: List[List[str]]):
        """Update player data from server information - tracks online/offline status."""
        # Check if player tracking is enabled
        if not getattr(Settings, 'enablePlayerTracking', True):
            self.online_players = []
            return
        
        current_time = time.time()
        current_player_names = set()
        
        # Process current online players
        new_online_players = []
        for player_info in current_players:
            extracted_info = self._extract_player_info(player_info)
            if extracted_info:
                new_online_players.append(extracted_info)
                current_player_names.add(extracted_info['name'])
        
        # Update offline players - move players who went offline to offline list
        for player in self.online_players:
            if player['name'] not in current_player_names:
                # Player went offline, add to offline list with timestamp
                self.offline_players[player['name']] = {
                    'name': player['name'],
                    'uid': player['uid'],
                    'steam_id': player['steam_id'],
                    'level': player['level'],
                    'last_online': current_time
                }
        
        # Update online players list
        self.online_players = new_online_players
        
        # Remove players who came back online from offline list
        for player_name in current_player_names:
            if player_name in self.offline_players:
                del self.offline_players[player_name]
        
        # Save updated data
        self._save_player_data()

    def get_all_players(self) -> List[Dict[str, Any]]:
        """Get all players (online and offline) with their status."""
        all_players = []
        
        # Add online players
        for player in self.online_players:
            player_copy = dict(player)
            player_copy['currently_online'] = True
            player_copy['last_online'] = time.time()
            all_players.append(player_copy)
        
        # Add offline players
        for player_data in self.offline_players.values():
            player_copy = dict(player_data)
            player_copy['currently_online'] = False
            all_players.append(player_copy)
        
        return all_players

    def get_online_players(self) -> List[Dict[str, Any]]:
        """Get currently online players."""
        return [dict(player) for player in self.online_players]

    def get_offline_players(self) -> List[Dict[str, Any]]:
        """Get currently offline players with last online timestamps."""
        offline_list = []
        for player_data in self.offline_players.values():
            offline_list.append(dict(player_data))
        return offline_list

    def get_player_count(self) -> int:
        """Get count of online players."""
        return len(self.online_players)

    def get_total_player_count(self) -> int:
        """Get total count of all players (online + offline)."""
        return len(self.online_players) + len(self.offline_players) 