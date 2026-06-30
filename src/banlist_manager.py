from typing import List
import os
import logging
import threading
import traceback
from src.settings import settings
from src.events import bus, Event


class BanlistManager:
    """Manages the Palworld server banlist.txt file."""

    def __init__(self, banlist_path=None):
        """
        Initialize the banlist manager.

        Args:
            banlist_path: Optional path to banlist.txt. If None, will try to auto-detect.
        """
        self.banlist_path = banlist_path or self._detect_banlist_path()
        self._lock = threading.RLock()
        # Subscribe to ban/unlan commands
        bus.subscribe(Event.CMD_BAN_PLAYER, lambda data: self.add_ban(data["steam_id"]))
        bus.subscribe(
            Event.CMD_UNBAN_PLAYER, lambda data: self.remove_ban(data["steam_id"])
        )

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
                    logging.debug(f"Found banlist at: {path}")
                    return path

            # If none exist, use the server root directory as default
            default_path = os.path.join(server_dir, "banlist.txt")
            logging.debug(f"Using default banlist path: {default_path}")
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

        with self._lock:
            try:
                if not os.path.exists(self.banlist_path):
                    logging.debug(
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

                logging.debug(
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

        with self._lock:
            try:
                # Read existing bans into a set for membership testing
                banned_set = set(self.get_banned_players())

                if steam_id in banned_set:
                    logging.debug(f"Steam ID {steam_id} is already banned")
                    bus.publish(Event.BAN_ADDED, {"steam_id": steam_id})
                    return True

                # Append the new ban to a temp buffer instead of rewriting the whole file
                with open(self.banlist_path, "a", encoding="utf-8") as f:
                    f.write(f"{steam_id}\n")

                logging.info(f"Successfully added ban for Steam ID: {steam_id}")
                bus.publish(Event.BAN_ADDED, {"steam_id": steam_id})
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

        with self._lock:
            try:
                # Read existing lines to check membership (without loading into set)
                banned_set = set()
                for line in open(self.banlist_path, "r", encoding="utf-8"):
                    stripped = line.strip()
                    if stripped and not stripped.startswith("#"):
                        banned_set.add(stripped)

                if steam_id not in banned_set:
                    logging.debug(f"Steam ID {steam_id} is not banned")
                    bus.publish(Event.BAN_REMOVED, {"steam_id": steam_id})
                    return True

                # Remove the line directly instead of rewriting whole file
                with open(self.banlist_path, "r", encoding="utf-8") as f:
                    lines = [l.rstrip("\n") for l in f if l.strip() and not l.startswith("#")]
                lines.remove(steam_id)

                with open(self.banlist_path, "w", encoding="utf-8") as f:
                    for line in lines:
                        f.write(f"{line}\n")

                logging.info(f"Successfully removed ban for Steam ID: {steam_id}")
                bus.publish(Event.BAN_REMOVED, {"steam_id": steam_id})
                return True

            except Exception as e:
                logging.error(f"Error removing ban for Steam ID {steam_id}: {e}")
                logging.error(traceback.format_exc())
                return False
