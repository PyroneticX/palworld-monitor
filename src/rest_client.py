import requests
import logging
import traceback
from requests.auth import HTTPBasicAuth
from settings import settings


class RestClient:
    """REST API client for communicating with PalWorld server."""
    
    def __init__(self):
        """
        Initialize REST client with connection parameters.
        """
        self.host = settings.palworldServerHost
        self.port = settings.palworldRESTPort
        self.password = settings.palworldAdminPassword
        self.base_url = f"http://{self.host}:{self.port}/v1/api"
        self.headers = {
            "Content-Type": "application/json"
        }
        self.auth = HTTPBasicAuth("admin", self.password)
    
    def _make_request(self, method, endpoint, data=None):
        """
        Make an HTTP request to the REST API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            data: Request data for POST requests
            
        Returns:
            Response JSON data or None if error occurred
        """
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
        """
        Get players data from the server.
        
        Returns:
            Players data or None if error occurred
        """
        return self._make_request("GET", "players")
    
    def _parse_players_list(self, players_data):
        """
        Parse players data into a standardized list format.
        
        Args:
            players_data: Raw players data from API
            
        Returns:
            List of player information (each player as a list of data)
        """
        players = []
        
        if not players_data:
            return players
            
        # Handle different response formats
        if isinstance(players_data, list):
            player_list = players_data
        elif isinstance(players_data, dict) and 'players' in players_data:
            player_list = players_data['players']
        else:
            return players
        
        # Extract player info for each player
        for player in player_list:
            if isinstance(player, dict):
                player_info = [
                    player.get('name', 'Unknown'),
                    player.get('playerId', 'Unknown'),  # Player UID is in playerId field
                    player.get('userId', 'Unknown'),  # Steam ID is in userId field
                    player.get('level', 'Unknown')
                ]
                players.append(player_info)
        
        return players
    
    def get_player_count(self):
        """
        Get the current player count from the server.
        
        Returns:
            Number of players currently on the server
        """
        try:
            players_data = self._get_players_data()
            if not players_data:
                return 0
            
            # Parse players list to get count
            players_list = self._parse_players_list(players_data)
            return len(players_list)
        except Exception as e:
            logging.error(f"Error getting player count: {e}")
            logging.error(traceback.format_exc())
            return 0
    
    def get_player_names(self):
        """
        Get the current player names from the server.
        
        Returns:
            List of player information (each player as a list of data)
        """
        try:
            players_data = self._get_players_data()
            return self._parse_players_list(players_data)
        except Exception as e:
            logging.error(f"Error getting player names: {e}")
            logging.error(traceback.format_exc())
            return []
    
    def shutdown_server(self, delay_seconds, message="Server is shutting down"):
        """
        Send shutdown command to the server using REST API.
        
        Args:
            delay_seconds: Delay before shutdown in seconds
            message: Shutdown message to display to players
            
        Returns:
            Server response or None if an error occurred
        """
        try:
            if delay_seconds < 1.0:
                delay_seconds = 1.0
            
            # First announce the shutdown message
            if message:
                self._announce_message(message)
            
            # Send shutdown request
            shutdown_data = {
                "waittime": delay_seconds,
                "message": message
            }
            return self._make_request("POST", "shutdown", shutdown_data)
        except Exception as e:
            logging.error(f"Error shutting down server: {e}")
            logging.error(traceback.format_exc())
            return None
    
    def _announce_message(self, message):
        """
        Announce a message to all players.
        
        Args:
            message: Message to announce
        """
        announce_data = {"message": message}
        self._make_request("POST", "announce", announce_data) 