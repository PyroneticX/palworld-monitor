# Copyright (c) 2024 Nomomo
# Copyright (c) 2026 Kevin Perez - Modified work
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

import requests
import logging
import traceback
from requests.auth import HTTPBasicAuth
from src.settings import settings
from rcon import Console


class RestClient:
    """REST API client for communicating with PalWorld server."""

    def __init__(self):
        self.base_url = (
            f"http://{settings.palworldServerHost}:{settings.palworldRESTPort}/v1/api"
        )
        self.headers = {"Content-Type": "application/json"}
        self.auth = HTTPBasicAuth("admin", settings.palworldServerAdminPassword)

    def _make_get_request(self, endpoint):
        """Make HTTP GET request to the API.

        Args:
            endpoint: API endpoint (e.g., 'players')

        Returns:
            dict or None: Response JSON or None on error
        """
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(
                url, headers=self.headers, auth=self.auth, timeout=10
            )
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as e:
            logging.error(f"Error making GET request to {endpoint}: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error in GET request to {endpoint}: {e}")
            logging.error(traceback.format_exc())
            return None

    def _make_post_request(self, endpoint, data=None):
        """Make HTTP POST request to the API.

        Args:
            endpoint: API endpoint (e.g., 'announce', 'kick', 'ban', 'unban')
            data: Optional request payload dictionary

        Returns:
            bool for player actions, dict or None otherwise
        """
        if data is None:
            data = {}
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.post(
                url, headers=self.headers, json=data, auth=self.auth, timeout=10
            )
            # Handle no-content responses (204)
            if not response.content:
                return {}
            if response.status_code == 200:
                return True
            logging.error(f"Failed to {endpoint} (status: {response.status_code})")
            return False
        except requests.exceptions.RequestException as e:
            logging.error(f"Error making POST request to {endpoint}: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error in POST request to {endpoint}: {e}")
            logging.error(traceback.format_exc())
            return False

    def _get_players_data(self):
        """Fetch players data from the API.

        Returns:
            dict or None: Response JSON or None on error
        """
        return self._make_get_request("players")

    def _parse_players_list(self, players_data):
        """Parse player list from API response."""
        try:
            if not isinstance(players_data, (list, dict)):
                return []
            if isinstance(players_data, dict):
                players_data = players_data.get("players", [])
            keys = ("name", "playerId", "userId", "level")
            return [[str(p.get(k, "Unknown")) for k in keys] for p in players_data]
        except Exception as e:
            logging.error(f"Error parsing player list: {e}")
            logging.error(traceback.format_exc())
            return []

    def get_player_count(self):
        """Get count of online players.

        Returns:
            int: Number of players or 0 on error
        """
        try:
            players_data = self._get_players_data()
            if not players_data:
                return 0
            return len(self._parse_players_list(players_data))
        except Exception as e:
            logging.error(f"Error getting player count: {e}")
            logging.error(traceback.format_exc())
            return 0

    def get_player_names(self):
        """Get names of online players.

        Returns:
            list or None: Player names or None on error
        """
        try:
            players_data = self._get_players_data()
            if not players_data:
                return []
            return self._parse_players_list(players_data)
        except Exception as e:
            logging.error(f"Error getting player names: {e}")
            logging.error(traceback.format_exc())
            return []

    def _announce_message(self, message):
        """Send an announcement to the server.

        Args:
            message: Message text to announce
        """
        self._make_post_request("announce", {"message": message})

    def kick_player(self, player):
        """Kick a player by their Steam ID.

        Args:
            player: Player dict with steam_id and name

        Returns:
            bool: True if successful, False otherwise
        """
        return self._make_post_request("kick", {"steam_id": player.get("steam_id"), "action_name": "kick"})

    def ban_player(self, player):
        """Ban a player by their Steam ID.

        Args:
            player: Player dict with steam_id and name

        Returns:
            bool: True if successful, False otherwise
        """
        return self._make_post_request("ban", {"steam_id": player.get("steam_id"), "action_name": "ban"})

    def unban_player(self, player):
        """Unban a player by their Steam ID.

        Args:
            player: Player dict with steam_id and name

        Returns:
            bool: True if successful, False otherwise
        """
        return self._make_post_request("unban", {"steam_id": player.get("steam_id"), "action_name": "unban"})


class RconClient:
    """RCON client for communicating with PalWorld server."""

    def __init__(self):
        self.host = settings.palworldServerHost
        self.port = settings.palworldRCONPort
        self.password = settings.palworldServerAdminPassword

    def _send_command(self, command):
        """Send an RCON command and return the response.

        Args:
            command: Command string to execute on server

        Returns:
            str or None: Response text or None on error
        """
        try:
            console = Console(host=self.host, port=self.port, password=self.password)
            response = console.command(command)
            console.close()
            return response
        except Exception:
            logging.error(f"Error from send_rcon_command. command={command}")
            logging.error(traceback.format_exc())
            return None

    def _send_show_players(self):
        """Send ShowPlayers RCON command and parse results.

        Returns:
            tuple: (player_list, error_details) or (None, error_details) on failure
        """
        try:
            console = Console(host=self.host, port=self.port, password=self.password)
            response = console.command("ShowPlayers")
            console.close()
            return response.splitlines(), None
        except Exception as e:
            logging.error(f"Error from send_rcon_command. command=ShowPlayers, error: {e}")
            logging.error(traceback.format_exc())
            return None, str(e)

    def get_player_count(self):
        """Get count of online players via RCON.

        Returns:
            int: Number of players or 0 on error
        """
        try:
            show_players, error_details = self._send_show_players()
            if show_players is None:
                error_info = f", error: {error_details}" if error_details else ""
                logging.error(f"Failed to get player count{error_info}")
                return 0
            split_text = show_players
            return len(split_text) - 1
        except Exception as e:
            logging.error(f"Error getting player count: {e}")
            logging.error(traceback.format_exc())
            return 0

    def get_player_names(self):
        """Get online players via RCON.

        Returns:
            list: Each entry is [name, playerId, userId]
        """
        try:
            show_players, error_details = self._send_show_players()
            if show_players is None or len(show_players) <= 1:
                return []
            # Skip header line (name,playerid,userid), split rest by comma
            players = [line.split(",") for line in show_players[1:]]
            return players
        except Exception as e:
            logging.error(f"Error getting player names: {e}")
            logging.error(traceback.format_exc())
            return []

    def _rcon_action(self, command_prefix, steam_id, player_name=""):
        """Send an RCON action command and log the result."""
        try:
            result, error_details = self._send_show_players()
            if result is not None:
                logging.info(f"Successfully {command_prefix.lower()} player {player_name} (Steam ID: {steam_id})")
                return True
            else:
                error_info = f", error: {error_details}" if error_details else ""
                logging.error(f"Failed to {command_prefix.lower()} player {player_name} (Steam ID: {steam_id}){error_info}")
                return False
        except Exception as e:
            logging.error(f"Error {command_prefix.lower()}ing player {player_name} (Steam ID: {steam_id}): {e}")
            logging.error(traceback.format_exc())
            return False

    def kick_player(self, steam_id, player_name=""):
        return self._rcon_action("KickPlayer", steam_id, player_name)

    def ban_player(self, steam_id, player_name=""):
        return self._rcon_action("BanPlayer", steam_id, player_name)

    def unban_player(self, steam_id, player_name=""):
        return self._rcon_action("UnbanPlayer", steam_id, player_name)
