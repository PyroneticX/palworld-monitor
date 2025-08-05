from typing import List, Dict, Any, Optional
from settings import settings
import json
import os
import time

class PlayerManager:
    """Manages player data including online and offline players with timestamps."""
    
    def __init__(self):
        self.players = {}  # Single dict: {player_uid: player_data}
        self.data_file = os.path.join('data', 'players.json')
        self._load_player_data()
    
    def _load_player_data(self):
        """Load player data from JSON file."""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.players = data.get('players', {})
        except Exception as e:
            print(f"Error loading player data: {e}")
            self.players = {}
    
    def _save_player_data(self):
        """Save player data to JSON file."""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump({
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
            "uid": player_info[1] if len(player_info) > 1 else "Unknown",
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
        current_player_uids = set()
        
        # Update current online players
        for player_info in current_players:
            extracted_info = self._extract_player_info(player_info)
            if extracted_info and extracted_info['uid'] != "Unknown":
                player_uid = extracted_info['uid']
                current_player_uids.add(player_uid)
                
                # Update or add player as online
                self.players[player_uid] = {
                    **extracted_info,
                    'currently_online': True,
                    'last_online': current_time
                }
        
        # Mark players as offline if they're not in current list
        for player_uid, player_data in self.players.items():
            if player_uid not in current_player_uids:
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