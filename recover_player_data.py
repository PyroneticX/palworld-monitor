#!/usr/bin/env python3
"""
Player Data Recovery Script
Recovers player data from logs and restores it to recent_players.json
"""

import json
import re
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

def extract_player_from_log_line(line: str) -> Optional[Dict[str, Any]]:
    """Extract player information from a log line."""
    # Pattern to match: "Added new player to recent list: kevinnio (Level 30)"
    pattern = r'Added new player to recent list: (.+?) \(Level (\d+)\)'
    match = re.search(pattern, line)
    
    if match:
        player_name = match.group(1)
        level = match.group(2)
        
        # Create a basic player record
        current_time = datetime.now().isoformat()
        return {
            "name": player_name,
            "uid": "Unknown",  # We don't have this from logs
            "steam_id": "Unknown",  # We don't have this from logs
            "level": level,
            "first_seen": current_time,
            "last_seen": current_time,
            "currently_online": False,  # Assume offline since this is recovery
            "total_online_seconds": 0
        }
    
    return None

def recover_players_from_logs(log_file: str = "app.log") -> List[Dict[str, Any]]:
    """Recover player data from log file."""
    recovered_players = []
    
    if not os.path.exists(log_file):
        print(f"Log file {log_file} not found!")
        return recovered_players
    
    print(f"Scanning log file: {log_file}")
    
    line_count = 0
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            line_count += 1
            if "Added new player to recent list:" in line:
                print(f"Found player line at line {line_count}: {line.strip()}")
            player_data = extract_player_from_log_line(line)
            if player_data:
                # Check if we already have this player
                existing_player = None
                for existing in recovered_players:
                    if existing["name"] == player_data["name"]:
                        existing_player = existing
                        break
                
                if existing_player:
                    # Update level if it's higher
                    existing_level = int(existing_player.get("level", "0"))
                    new_level = int(player_data["level"])
                    if new_level > existing_level:
                        existing_player["level"] = str(new_level)
                else:
                    recovered_players.append(player_data)
                    print(f"Recovered player: {player_data['name']} (Level {player_data['level']})")
    
    return recovered_players

def create_backup_of_current_file():
    """Create a backup of the current recent_players.json file."""
    if os.path.exists("recent_players.json"):
        backup_name = f"recent_players_before_recovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        import shutil
        shutil.copy2("recent_players.json", backup_name)
        print(f"Created backup of current file: {backup_name}")
        return backup_name
    return None

def restore_player_data(players: List[Dict[str, Any]]):
    """Restore player data to recent_players.json."""
    data = {
        "players": players,
        "last_updated": datetime.now().isoformat()
    }
    
    with open("recent_players.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Restored {len(players)} players to recent_players.json")

def main():
    """Main recovery function."""
    print("=== Player Data Recovery Tool ===")
    print()
    
    # Create backup of current file
    backup_file = create_backup_of_current_file()
    
    # Recover players from logs
    recovered_players = recover_players_from_logs()
    
    if not recovered_players:
        print("No players found in logs!")
        return
    
    print(f"\nFound {len(recovered_players)} unique players in logs:")
    for player in recovered_players:
        print(f"  - {player['name']} (Level {player['level']})")
    
    # Ask for confirmation
    response = input(f"\nDo you want to restore these {len(recovered_players)} players to recent_players.json? (y/N): ")
    
    if response.lower() in ['y', 'yes']:
        restore_player_data(recovered_players)
        print("\nRecovery completed successfully!")
        
        if backup_file:
            print(f"Original file backed up as: {backup_file}")
    else:
        print("Recovery cancelled.")

if __name__ == "__main__":
    main() 