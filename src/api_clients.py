# Copyright (c) 2024 Nomomo
# Copyright (c) 2024 Kevin Perez - Modified work
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
from abc import ABC
from requests.auth import HTTPBasicAuth
from settings import settings
from rcon import Console


class PalworldApiClient(ABC):
    """Base class for clients that perform player actions (kick, ban, unban)."""

    def _validate_and_extract_player_info(self, player):
        """Validate player object and extract steam_id and name for logging.

        Args:
            player: Player dict object with steam_id and name

        Returns:
            tuple: (steam_id, player_name) or (None, None) if invalid
        """
        if not isinstance(player, dict):
            logging.error("Player must be a dict with steam_id")
            return None, None

        steam_id = player.get("steam_id")
        if not steam_id:
            logging.error("Player object missing steam_id")
            return None, None

        player_name = player.get("name", "")

        return steam_id, player_name


class RestClient(PalworldApiClient):
    """REST API client for communicating with PalWorld server."""

    def __init__(self):
        self.base_url = (
            f"http://{settings.palworldServerHost}:{settings.palworldRESTPort}/v1/api"
        )
        self.headers = {"Content-Type": "application/json"}
        self.auth = HTTPBasicAuth("admin", settings.palworldServerAdminPassword)

    def _make_get_request(self, endpoint, data=None):
        """Make HTTP GET request to the API.

        Args:
            endpoint: API endpoint (e.g., 'players')
            data: Optional dictionary containing request data (default: None)

        Returns:
            dict or None: Response JSON or None on error
        """
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(
                url, headers=self.headers, json=data, auth=self.auth, timeout=10
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
            data: Optional dictionary containing:
                - Request payload (for HTTP request body)
                - For player actions: 'steam_id', 'player_info', 'action_name' keys for logging
                - For other requests: any payload data

        Returns:
            For player actions (when data contains 'action_name'): bool - True if successful, False otherwise
            For other requests: dict or None - Response JSON or None on error
        """
        # Extract player action metadata for logging
        action_name = data.get("action_name") if data else None
        steam_id = data.get("steam_id") if data else None
        player_info = data.get("player_info") if data else None

        try:
            url = f"{self.base_url}/{endpoint}"

            response = requests.post(
                url, headers=self.headers, json=data, auth=self.auth, timeout=10
            )

            # Handle player action requests (return bool)
            if action_name is not None:
                if response.status_code == 200:
                    logging.info(
                        f"Successfully {action_name}ed player{player_info} (Steam ID: {steam_id})"
                    )
                    return True
                else:
                    response_text = (
                        response.text.strip() if response.text else "No response body"
                    )
                    logging.error(
                        f"Failed to {action_name} player{player_info} (Steam ID: {steam_id}, status: {response.status_code}, response: {response_text})"
                    )
                    return False

            # Handle other requests (return JSON or None)
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as e:
            if action_name is not None:
                logging.error(
                    f"Unexpected error {action_name}ing player{player_info} (Steam ID: {steam_id}): {e}"
                )
            else:
                logging.error(f"Error making POST request to {endpoint}: {e}")
            if action_name is not None:
                logging.error(traceback.format_exc())
            return False if action_name is not None else None
        except Exception as e:
            if action_name is not None:
                logging.error(
                    f"Unexpected error {action_name}ing player{player_info} (Steam ID: {steam_id}): {e}"
                )
            else:
                logging.error(f"Unexpected error in POST request to {endpoint}: {e}")
            logging.error(traceback.format_exc())
            return False if action_name is not None else None

    def _get_players_data(self):
        return self._make_get_request("players")

    def _parse_players_list(self, players_data):
        players = []
        if not players_data:
            return players
        if isinstance(players_data, list):
            player_list = players_data
        elif isinstance(players_data, dict) and "players" in players_data:
            player_list = players_data["players"]
        else:
            return players
        for player in player_list:
            if isinstance(player, dict):
                player_info = [
                    player.get("name", "Unknown"),
                    player.get("playerId", "Unknown"),
                    player.get("userId", "Unknown"),
                    player.get("level", "Unknown"),
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
        self._make_post_request("announce", announce_data)

    def kick_player(self, player):
        """Kick a player by their Steam ID.

        Args:
            player: Player dict object with steam_id and name

        Returns:
            bool: True if successful, False otherwise
        """
        steam_id, player_name = self._validate_and_extract_player_info(player)
        if steam_id is None:
            return False

        player_info = f" {player_name}" if player_name else ""
        data = {"steam_id": steam_id, "player_info": player_info, "action_name": "kick"}
        return self._make_post_request("kick", data)

    def ban_player(self, player):
        """Ban a player by their Steam ID.

        Args:
            player: Player dict object with steam_id and name

        Returns:
            bool: True if successful, False otherwise
        """
        steam_id, player_name = self._validate_and_extract_player_info(player)
        if steam_id is None:
            return False

        player_info = f" {player_name}" if player_name else ""
        data = {"steam_id": steam_id, "player_info": player_info, "action_name": "ban"}
        return self._make_post_request("ban", data)

    def unban_player(self, player):
        """Unban a player by their Steam ID.

        Args:
            player: Player dict object with steam_id and name

        Returns:
            bool: True if successful, False otherwise
        """
        steam_id, player_name = self._validate_and_extract_player_info(player)
        if steam_id is None:
            return False

        player_info = f" {player_name}" if player_name else ""
        data = {
            "steam_id": steam_id,
            "player_info": player_info,
            "action_name": "unban",
        }
        return self._make_post_request("unban", data)


class RconClient(PalworldApiClient):
    """RCON client for communicating with PalWorld server."""

    def __init__(self):
        self.host = settings.palworldServerHost
        self.port = settings.palworldRCONPort
        self.password = settings.palworldServerAdminPassword

    def _send_command(self, command):
        try:
            console = Console(host=self.host, port=self.port, password=self.password)
            response = console.command(command)
            console.close()
            return response
        except Exception:
            logging.error(f"Error from send_rcon_command. command={command}")
            logging.error(traceback.format_exc())
            return None

    def _send_command_with_error_details(self, command):
        """Send RCON command and return both response and error details."""
        try:
            console = Console(host=self.host, port=self.port, password=self.password)
            response = console.command(command)
            console.close()
            return response, None
        except Exception as e:
            error_details = str(e)
            logging.error(
                f"Error from send_rcon_command. command={command}, error: {error_details}"
            )
            logging.error(traceback.format_exc())
            return None, error_details

    def get_player_count(self):
        try:
            show_players, error_details = self._send_command_with_error_details(
                "ShowPlayers"
            )
            if show_players is None:
                error_info = f", error: {error_details}" if error_details else ""
                logging.error(f"Failed to get player count{error_info}")
                return 0
            split_text = show_players.splitlines()
            return len(split_text) - 1
        except Exception as e:
            logging.error(f"Error getting player count: {e}")
            logging.error(traceback.format_exc())
            return 0

    def get_player_names(self):
        try:
            show_players, error_details = self._send_command_with_error_details(
                "ShowPlayers"
            )
            if show_players is None:
                error_info = f", error: {error_details}" if error_details else ""
                logging.error(f"Failed to get player names{error_info}")
                return []
            split_text = show_players.splitlines()
            player_count = len(split_text) - 1
            if player_count >= 1:
                players = []
                for i in range(player_count):
                    players.append(split_text[i + 1].split(","))
                return players
            else:
                return []
        except Exception as e:
            logging.error(f"Error getting player names: {e}")
            logging.error(traceback.format_exc())
            return []

    def kick_player(self, player):
        """Kick a player by their Steam ID.

        Args:
            player: Player dict object with steam_id and name

        Returns:
            bool: True if successful, False otherwise
        """
        steam_id, player_name = self._validate_and_extract_player_info(player)
        if steam_id is None:
            return False

        player_info = f" {player_name}" if player_name else ""
        try:
            command = f"KickPlayer {steam_id}"
            result, error_details = self._send_command_with_error_details(command)

            if result is not None:
                logging.info(
                    f"Successfully kicked player{player_info} (Steam ID: {steam_id})"
                )
                return True
            else:
                error_info = f", error: {error_details}" if error_details else ""
                logging.error(
                    f"Failed to kick player{player_info} (Steam ID: {steam_id}){error_info}"
                )
                return False
        except Exception as e:
            logging.error(
                f"Error kicking player{player_info} (Steam ID: {steam_id}): {e}"
            )
            logging.error(traceback.format_exc())
            return False

    def ban_player(self, player):
        """Ban a player by their Steam ID.

        Args:
            player: Player dict object with steam_id and name

        Returns:
            bool: True if successful, False otherwise
        """
        steam_id, player_name = self._validate_and_extract_player_info(player)
        if steam_id is None:
            return False

        player_info = f" {player_name}" if player_name else ""
        try:
            command = f"BanPlayer {steam_id}"
            result, error_details = self._send_command_with_error_details(command)

            if result is not None:
                logging.info(
                    f"Successfully banned player{player_info} (Steam ID: {steam_id})"
                )
                return True
            else:
                error_info = f", error: {error_details}" if error_details else ""
                logging.error(
                    f"Failed to ban player{player_info} (Steam ID: {steam_id}){error_info}"
                )
                return False
        except Exception as e:
            logging.error(
                f"Error banning player{player_info} (Steam ID: {steam_id}): {e}"
            )
            logging.error(traceback.format_exc())
            return False

    def unban_player(self, player):
        """Unban a player by their Steam ID.

        Args:
            player: Player dict object with steam_id and name

        Returns:
            bool: True if successful, False otherwise
        """
        steam_id, player_name = self._validate_and_extract_player_info(player)
        if steam_id is None:
            return False

        player_info = f" {player_name}" if player_name else ""
        try:
            command = f"UnbanPlayer {steam_id}"
            result, error_details = self._send_command_with_error_details(command)

            if result is not None:
                logging.info(
                    f"Successfully unbanned player{player_info} (Steam ID: {steam_id})"
                )
                return True
            else:
                error_info = f", error: {error_details}" if error_details else ""
                logging.error(
                    f"Failed to unban player{player_info} (Steam ID: {steam_id}){error_info}"
                )
                return False
        except Exception as e:
            logging.error(
                f"Error unbanning player{player_info} (Steam ID: {steam_id}): {e}"
            )
            logging.error(traceback.format_exc())
            return False
