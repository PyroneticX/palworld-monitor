from rcon import Console
import logging
import traceback
from settings import Settings


class RconClient:
    """RCON client for communicating with PalWorld server."""
    
    def __init__(self, host=None, port=None, password=None):
        """
        Initialize RCON client with connection parameters.
        
        Args:
            host: RCON host (defaults to Settings.palworldRCONHost)
            port: RCON port (defaults to Settings.palworldRCONPort)
            password: RCON password (defaults to Settings.palworldAdminPassword)
        """
        self.host = host or Settings.palworldRCONHost
        self.port = port or Settings.palworldRCONPort
        self.password = password or Settings.palworldAdminPassword
    
    def _send_command(self, command):
        """
        Send an RCON command to the PalWorld server.
        
        Args:
            command: The RCON command to send
            
        Returns:
            The server response or None if an error occurred
        """
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
        """
        Get the current player count from the server.
        
        Returns:
            Number of players currently on the server
        """
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
        """
        Get the current player names from the server.
        
        Returns:
            List of player information (each player as a list of data)
        """
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
    
    def shutdown_server(self, delay_seconds, message="Server is shutting down"):
        """
        Send shutdown command to the server.
        
        Args:
            delay_seconds: Delay before shutdown in seconds
            message: Shutdown message to display to players
            
        Returns:
            Server response or None if an error occurred
        """
        if delay_seconds < 1.0:
            delay_seconds = 1.0
        return self._send_command(f"Shutdown {delay_seconds} {message}") 