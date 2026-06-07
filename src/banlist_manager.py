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

import os
import logging
import traceback
from typing import List
from settings import settings


class BanlistManager:
    """Manages the Palworld server banlist.txt file."""

    def __init__(self, banlist_path=None):
        """
        Initialize the banlist manager.

        Args:
            banlist_path: Optional path to banlist.txt file. If None, will try to auto-detect.
        """
        self.banlist_path = banlist_path or self._detect_banlist_path()

    def _detect_banlist_path(self):
        """Try to detect the banlist.txt file path based on server executable path."""
        try:
            # Get the directory of the Palworld server executable
            server_exe_path = settings.palworldServerExePath
            if not server_exe_path:
                return None

            server_dir = os.path.dirname(os.path.abspath(server_exe_path))

            # Common locations for banlist.txt
            possible_paths = [
                # In server root directory
                os.path.join(server_dir, "banlist.txt"),
                # In Pal/Saved directory (Windows)
                os.path.join(
                    server_dir, "Pal", "Saved", "SaveGames", "0", "banlist.txt"
                ),
                # In Pal/Saved directory (Linux)
                os.path.join(server_dir, "Pal", "Saved", "banlist.txt"),
            ]

            # Check if any of these paths exist
            for path in possible_paths:
                if os.path.exists(path):
                    logging.info(f"Found banlist at: {path}")
                    return path

            # If none exist, use the server root directory as default
            default_path = os.path.join(server_dir, "banlist.txt")
            logging.info(f"Using default banlist path: {default_path}")
            return default_path

        except Exception as e:
            logging.error(f"Error detecting banlist path: {e}")
            logging.error(traceback.format_exc())
            return None

    def get_banned_players(self) -> List[str]:
        """
        Read and return list of banned Steam IDs from banlist.txt.

        Returns:
            List of Steam IDs (as strings)
        """
        if not self.banlist_path:
            logging.warning("Banlist path not configured, cannot read banned players")
            return []

        try:
            if not os.path.exists(self.banlist_path):
                logging.info(
                    f"Banlist file does not exist at {self.banlist_path}, returning empty list"
                )
                return []

            banned_steam_ids = []
            with open(self.banlist_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith("#"):
                        banned_steam_ids.append(line)

            logging.info(
                f"Loaded {len(banned_steam_ids)} banned players from {self.banlist_path}"
            )
            return banned_steam_ids

        except Exception as e:
            logging.error(f"Error reading banlist from {self.banlist_path}: {e}")
            logging.error(traceback.format_exc())
            return []

    def is_banned(self, steam_id: str) -> bool:
        """
        Check if a Steam ID is banned.

        Args:
            steam_id: Steam ID to check

        Returns:
            True if banned, False otherwise
        """
        banned_players = self.get_banned_players()
        return steam_id in banned_players

    def add_ban(self, steam_id: str) -> bool:
        """
        Add a Steam ID to the banlist.

        Args:
            steam_id: Steam ID to ban

        Returns:
            True if successful, False otherwise
        """
        if not self.banlist_path:
            logging.error("Banlist path not configured, cannot add ban")
            return False

        try:
            # Get existing bans
            banned_players = set(self.get_banned_players())

            # Add new ban
            if steam_id in banned_players:
                logging.info(f"Steam ID {steam_id} is already banned")
                return True

            banned_players.add(steam_id)

            # Ensure directory exists
            banlist_dir = os.path.dirname(self.banlist_path)
            if banlist_dir:  # Only create directory if path has a directory component
                os.makedirs(banlist_dir, exist_ok=True)

            # Write banlist back to file
            with open(self.banlist_path, "w", encoding="utf-8") as f:
                for banned_id in sorted(banned_players):
                    f.write(f"{banned_id}\n")

            logging.info(f"Successfully added ban for Steam ID: {steam_id}")
            return True

        except Exception as e:
            logging.error(f"Error adding ban for Steam ID {steam_id}: {e}")
            logging.error(traceback.format_exc())
            return False

    def remove_ban(self, steam_id: str) -> bool:
        """
        Remove a Steam ID from the banlist (unban).

        Args:
            steam_id: Steam ID to unban

        Returns:
            True if successful, False otherwise
        """
        if not self.banlist_path:
            logging.error("Banlist path not configured, cannot remove ban")
            return False

        try:
            # Get existing bans
            banned_players = set(self.get_banned_players())

            # Remove ban
            if steam_id not in banned_players:
                logging.info(f"Steam ID {steam_id} is not banned")
                return True

            banned_players.remove(steam_id)

            # Write banlist back to file
            with open(self.banlist_path, "w", encoding="utf-8") as f:
                for banned_id in sorted(banned_players):
                    f.write(f"{banned_id}\n")

            logging.info(f"Successfully removed ban for Steam ID: {steam_id}")
            return True

        except Exception as e:
            logging.error(f"Error removing ban for Steam ID {steam_id}: {e}")
            logging.error(traceback.format_exc())
            return False
