import psutil
import subprocess
import logging
import time
import threading
from settings import settings
import traceback
from player_manager import PlayerManager
from process_manager import WindowsProcessManager, LinuxProcessManager


class PalWorldController:
    def __init__(self, client):
        self.client = client
        self.on_server_stopped_callback = None

        # Initialize player manager
        self.player_manager = PlayerManager()

        # Server state information
        self.current_server_info = {
            "running": False,
            "playerCount": 0,
            "players": []
        }
        
        # Server control flags and timestamps
        self.is_palworld_server_starting = False
        self.server_starting_cooldown = 5  # seconds
        self.last_server_started_time = 0
        self.server_stopping_cooldown = 5  # seconds
        self.last_server_stopped_time = 0
        
        # Stop event tracking
        self.triggered_time_check_stopped_event = -1
        self.is_triggered_check_stopped_event = False
        
        # Select driver
        if settings.os.lower() == 'linux':
            self.process_manager = LinuxProcessManager()
        else:
            self.process_manager = WindowsProcessManager()


    def is_palworld_process_running(self):
        """Check if the PalWorld server process is currently running."""
        return self.process_manager.is_process_running()

    def start_server(self):
        """Start the PalWorld server with various safety checks."""
        logging.info("Palworld server is commanded to start")
        palworld_exe_path = settings.palworldServerExePath
        current_time = time.time()

        if self._should_block_start(current_time):
            return False

        return_val = True
        try:
            self._launch_process(palworld_exe_path)
        except subprocess.CalledProcessError as e:
            logging.error(f"Error occurred while executing the Palworld executable file : {e}")
            return_val = False
        finally:
            self.is_palworld_server_starting = False
            self.last_server_started_time = time.time()

        return return_val

    def _should_block_start(self, current_time):
        if self.is_palworld_process_running():
            logging.warning("The attempt to start the Palworld server was made, but it is already running.")
            return True
        if self.is_palworld_server_starting:
            logging.warning("Palworld Server is already starting.")
            return True
        if current_time - self.last_server_started_time < self.server_starting_cooldown:
            logging.warning("Tried to start the server too quickly multiple times. This attempt will be ignored.")
            return True
        if current_time - self.last_server_stopped_time < self.server_stopping_cooldown:
            logging.warning("You attempted to restart the server too quickly shortly after trying to stop it. This attempt will be ignored.")
            return True
        if self.is_stop_event_running():
            logging.warning("Stop event is running. starting server is ignored")
            return True
        return False

    def _launch_process(self, palworld_exe_path):
        self.is_palworld_server_starting = True
        self.process_manager.launch_process(palworld_exe_path, settings.palworldExeArguments)

    def terminate_process(self):
        """Terminate the launched server process by PID."""
        self.process_manager.terminate_launched_process()

    def check_is_stopped_palworld_process_core(self, timeout=60):
        """Check if the PalWorld process has been terminated."""
        self.triggered_time_check_stopped_event = time.time()
        while True:
            if not self.is_palworld_process_running():
                break

            current_time = time.time()
            if current_time - self.triggered_time_check_stopped_event > timeout:
                break
            
            time.sleep(1)
        self.is_triggered_check_stopped_event = False
        if self.on_server_stopped_callback:
            self.on_server_stopped_callback()

    def is_stop_event_running(self):
        """Check if a stop event is currently running."""
        return self.is_triggered_check_stopped_event

    def stop_server(self, delay_seconds, force=False):
        """Stop the PalWorld server with optional force termination."""
        logging.info("Palworld server is commanded to shutdown")

        if not self.is_triggered_check_stopped_event:
            self.is_triggered_check_stopped_event = True
            thread = threading.Thread(target=self.check_is_stopped_palworld_process_core)
            thread.start()

        if force:
            self.terminate_process()
        else:
            if self._should_block_stop():
                return
            delay_seconds = self._sanitize_delay(delay_seconds)
            self.client.shutdown_server(delay_seconds, settings.ServerAutoStopMessage)
        self.last_server_stopped_time = time.time()

    def _should_block_stop(self):
        if not self.is_palworld_process_running():
            logging.error("An attempt to stop the Palworld server was made, but it was not running.")
            return True
        current_time = time.time()
        if current_time - self.last_server_stopped_time < self.server_stopping_cooldown:
            logging.warning("You attempted to restart the server too quickly shortly after trying to stop it. This attempt will be ignored.")
            return True
        return False

    def _sanitize_delay(self, delay_seconds):
        return max(delay_seconds, 1.0)

    def update_current_server_info(self):
        """Update and return current server information including player count and player names."""
        try:
            if self._should_clear_server_info():
                self._clear_server_info()
                return self.current_server_info
            self._update_server_info_with_players()
            return self.current_server_info
        except Exception as e:
            logging.error(f"Error from update_current_server_info, {e}")
            logging.error(traceback.format_exc())
            return None

    def _should_clear_server_info(self):
        current_time = time.time()
        return (
            not self.is_palworld_process_running() or
            self.is_triggered_check_stopped_event or
            (current_time - self.last_server_stopped_time < self.server_stopping_cooldown)
        )

    def _clear_server_info(self):
        self.current_server_info["running"] = False
        self.current_server_info["playerCount"] = 0
        self.current_server_info["players"] = []
        if getattr(settings, 'enablePlayerTracking', True):
            self.player_manager.update_players_from_server([])

    def _update_server_info_with_players(self):
        self.current_server_info["running"] = True
        current_players = self.get_player_names()
        self.current_server_info["playerCount"] = len(current_players)
        self.current_server_info["players"] = current_players
        if getattr(settings, 'enablePlayerTracking', True):
            self.player_manager.update_players_from_server(current_players)

    def get_player_count(self):
        """Get the current player count from the server."""
        return self.client.get_player_count()

    def get_player_names(self):
        """Get the current player names from the server."""
        return self.client.get_player_names()

    def get_server_status(self):
        """Get the current server status."""
        if not self.is_palworld_process_running():
            return False
        return True

    def set_on_server_stopped_callback(self, callback):
        """Set the callback function to be called when the server is stopped."""
        self.on_server_stopped_callback = callback
    
    def get_player_manager(self):
        """Get the player manager instance."""
        return self.player_manager