import requests
import logging
import traceback
from requests.auth import HTTPBasicAuth
from settings import settings
from rcon import Console

class RestClient:
    """REST API client for communicating with PalWorld server."""
    def __init__(self):
        self.base_url = f"http://{settings.palworldServerHost}:{settings.palworldRESTPort}/v1/api"
        self.headers = {
            "Content-Type": "application/json"
        }
        self.auth = HTTPBasicAuth("admin", settings.palworldServerAdminPassword)

    def _make_request(self, method, endpoint, data=None):
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.request(
                method,
                url,
                headers=self.headers,
                json=data,
                auth=self.auth,
                timeout=10
            )
            response.raise_for_status()
            return response.json() if response.content else None
        except requests.exceptions.RequestException as e:
            logging.error(f"Error making {method} request to {endpoint}: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error in {method} request to {endpoint}: {e}")
            logging.error(traceback.format_exc())
            return None

    def _get_players_data(self):
        return self._make_request("GET", "players")

    def _parse_players_list(self, players_data):
        players = []
        if not players_data:
            return players
        if isinstance(players_data, list):
            player_list = players_data
        elif isinstance(players_data, dict) and 'players' in players_data:
            player_list = players_data['players']
        else:
            return players
        for player in player_list:
            if isinstance(player, dict):
                player_info = [
                    player.get('name', 'Unknown'),
                    player.get('playerId', 'Unknown'),
                    player.get('userId', 'Unknown'),
                    player.get('level', 'Unknown')
                ]
                players.append(player_info)
        return players

    def get_player_count(self):
        try:
            players_data = self._get_players_data()
            if not players_data:
                return 0
            players_list = self._parse_players_list(players_data)
            return len(players_list)
        except Exception as e:
            logging.error(f"Error getting player count: {e}")
            logging.error(traceback.format_exc())
            return 0

    def get_player_names(self):
        try:
            players_data = self._get_players_data()
            return self._parse_players_list(players_data)
        except Exception as e:
            logging.error(f"Error getting player names: {e}")
            logging.error(traceback.format_exc())
            return []

    def _announce_message(self, message):
        announce_data = {"message": message}
        self._make_request("POST", "announce", announce_data)

    def kick_player(self, steam_id):
        """Kick a player by their Steam ID."""
        try:
            kick_data = {"userid": steam_id}
            result = self._make_request("POST", "kick", kick_data)
            if result:
                logging.info(f"Successfully kicked player with Steam ID: {steam_id}")
                return True
            else:
                logging.error(f"Failed to kick player with Steam ID: {steam_id}")
                return False
        except Exception as e:
            logging.error(f"Error kicking player {steam_id}: {e}")
            logging.error(traceback.format_exc())
            return False

    def ban_player(self, steam_id):
        """Ban a player by their Steam ID using REST API."""
        try:
            # Try REST API ban endpoint first (similar structure to kick)
            ban_data = {"userid": steam_id}
            result = self._make_request("POST", "ban", ban_data)
            if result is not None:
                logging.info(f"Successfully banned player with Steam ID: {steam_id}")
                return True
            else:
                # Fallback to RCON if REST API doesn't work
                logging.warning(f"REST API ban failed, falling back to RCON for Steam ID: {steam_id}")
                rcon_client = RconClient()
                return rcon_client.ban_player(steam_id)
        except Exception as e:
            logging.error(f"Error banning player {steam_id}: {e}")
            logging.error(traceback.format_exc())
            # Try RCON as fallback
            try:
                rcon_client = RconClient()
                return rcon_client.ban_player(steam_id)
            except Exception as e2:
                logging.error(f"RCON fallback also failed: {e2}")
                return False


class RconClient:
    """RCON client for communicating with PalWorld server."""
    def __init__(self):
        self.host = settings.palworldServerHost
        self.port = settings.palworldRCONPort
        self.password = settings.palworldServerAdminPassword

    def _send_command(self, command):
        try:
            console = Console(
                host=self.host,
                port=self.port,
                password=self.password
            )
            response = console.command(command)
            console.close()
            return response
        except Exception as e:
            logging.error(f"Error from send_rcon_command. command={command}")
            logging.error(traceback.format_exc())
            return None

    def get_player_count(self):
        try:
            show_players = self._send_command("ShowPlayers")
            if show_players is None:
                return 0
            split_text = show_players.splitlines()
            return len(split_text) - 1
        except Exception as e:
            logging.error(f"Error getting player count: {e}")
            logging.error(traceback.format_exc())
            return 0

    def get_player_names(self):
        try:
            show_players = self._send_command("ShowPlayers")
            if show_players is None:
                return []
            split_text = show_players.splitlines()
            player_count = len(split_text) - 1
            if player_count >= 1:
                players = []
                for i in range(player_count):
                    players.append(split_text[i + 1].split(','))
                return players
            else:
                return []
        except Exception as e:
            logging.error(f"Error getting player names: {e}")
            logging.error(traceback.format_exc())
            return []

    def kick_player(self, steam_id):
        """Kick a player by their Steam ID using RCON."""
        try:
            command = f"KickPlayer {steam_id}"
            result = self._send_command(command)
            if result is not None:
                logging.info(f"Successfully kicked player with Steam ID: {steam_id}")
                return True
            else:
                logging.error(f"Failed to kick player with Steam ID: {steam_id}")
                return False
        except Exception as e:
            logging.error(f"Error kicking player {steam_id}: {e}")
            logging.error(traceback.format_exc())
            return False

    def ban_player(self, steam_id):
        """Ban a player by their Steam ID using RCON."""
        try:
            command = f"BanPlayer {steam_id}"
            result = self._send_command(command)
            if result is not None:
                logging.info(f"Successfully banned player with Steam ID: {steam_id}")
                return True
            else:
                logging.error(f"Failed to ban player with Steam ID: {steam_id}")
                return False
        except Exception as e:
            logging.error(f"Error banning player {steam_id}: {e}")
            logging.error(traceback.format_exc())
            return False