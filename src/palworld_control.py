import subprocess
import logging
import time
import threading
from settings import settings
import traceback
from player_manager import PlayerManager

class PalWorldController:
    def __init__(self, client):
        self.client = client
        self.on_server_started_callback = None
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
        self.server_startup_auto_stop_delay = settings.autoStopDelay  # Use the same delay as auto-stop
        
        # Stop event tracking
        self.triggered_time_check_stopped_event = -1
        self.is_triggered_check_stopped_event = False
        
        # Auto-stop delay tracking
        self.auto_stop_delay_thread = None
        self.auto_stop_delay_cancelled = False
        
        # Background update thread management
        self.update_thread = None
        self.update_thread_stop_event = threading.Event()
        
        # Select driver
        if settings.os.lower() == 'linux':
            from process_manager import LinuxProcessManager
            self.process_manager = LinuxProcessManager()
        else:
            from process_manager import WindowsProcessManager
            self.process_manager = WindowsProcessManager()

        # If no PID was loaded, try to detect an already running Palworld server
        self._detect_existing_server_process()


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
            if self.is_palworld_process_running():
                self._handle_server_started(source="launch")
            else:
                logging.error("Palworld server failed to launch (process not running after start).")
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

    def _detect_existing_server_process(self):
        """Detect a running Palworld server and register its PID in the process manager.
        """
        try:
            import psutil
            import os

            # If PID is already known (from PID file), skip
            if self.process_manager.launched_pid is not None:
                return

            # Only try if no PID file exists yet
            if os.path.exists(self.process_manager.pid_file_name()):
                return

            candidates = set()
            exe_path = settings.palworldServerExePath

            if exe_path:
                candidates.add(os.path.basename(exe_path).lower())

            if not candidates and not exe_path:
                return

            for proc in psutil.process_iter(attrs=['pid', 'name', 'exe', 'cmdline']):
                try:
                    info = proc.info
                    name = (info.get('name') or '').lower()
                    exe = (info.get('exe') or '').lower()
                    exe_base = os.path.basename(exe) if exe else ''
                    cmdline_list = info.get('cmdline') or []
                    cmdline = ' '.join(map(str, cmdline_list)).lower()

                    matched = False
                    if name in candidates or exe_base in candidates:
                        matched = True
                    elif exe_path:
                        low_path = exe_path.lower()
                        if exe == low_path or low_path in cmdline:
                            matched = True

                    if matched:
                        self.process_manager.set_known_pid(info['pid'])
                        logging.info(f"Detected existing Palworld server (PID {info['pid']}). Attaching controller.")
                        self._handle_server_started(source="attach")
                        return
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except Exception:
            # best-effort only
            pass

    def _handle_server_started(self, source: str = "launch"):
        """Common behavior after the server is considered started.

        Starts background updates, invokes the started callback, and timestamps the event.
        """
        if source == "launch":
            logging.info("Palworld server launched successfully.")
        elif source == "attach":
            logging.info("Attached to running Palworld server successfully.")
        else:
            logging.info("Server started.")

        # Start the update thread after successful start/attach
        self.start_server_info_update_thread()

        # Call the server started callback
        if self.on_server_started_callback:
            self.on_server_started_callback()

        # Update last started timestamp
        self.last_server_started_time = time.time()

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

    # Removed stop_server method and related logic

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
            self._update_server_info_with_players()

            if settings.autoStop and self.player_manager.get_player_count() == 0:
                self._handle_auto_stop_condition()
            else:
                self._cancel_auto_stop_delay()

            return self.current_server_info
        except Exception as e:
            logging.error(f"Error from update_current_server_info, {e}")
            logging.error(traceback.format_exc())
            return None

    def _update_server_info_with_players(self):
        self.current_server_info["running"] = self.is_palworld_process_running()
        
        current_players = self.get_player_names()
        self.current_server_info["playerCount"] = len(current_players)
        self.current_server_info["players"] = current_players

        if settings.enablePlayerTracking:
            self.player_manager.update_players_from_server(current_players)

    def _handle_auto_stop_condition(self):
        """Handle the auto-stop condition with delay."""
        # If auto-stop delay is already triggered, don't trigger again
        if self.auto_stop_delay_thread and self.auto_stop_delay_thread.is_alive():
            return
        
        # Check if enough time has passed since server startup
        current_time = time.time()
        time_since_startup = current_time - self.last_server_started_time
        
        if time_since_startup < self.server_startup_auto_stop_delay:
            remaining_time = self.server_startup_auto_stop_delay - time_since_startup
            logging.info(f"Auto-stop blocked: Server started {time_since_startup:.0f}s ago. Auto-stop will be available in {remaining_time:.0f}s.")
            return
        
        # Reset cancellation flag
        self.auto_stop_delay_cancelled = False
        logging.info(f"Auto-stop condition met. Server will stop in {settings.autoStopDelay} seconds.")
        
        # Start delay thread
        self.auto_stop_delay_thread = threading.Thread(target=self._auto_stop_delay_worker, daemon=True)
        self.auto_stop_delay_thread.start()

    def _cancel_auto_stop_delay(self):
        """Cancel the auto-stop delay if players are back online."""
        if self.auto_stop_delay_thread and self.auto_stop_delay_thread.is_alive():
            self.auto_stop_delay_cancelled = True
            logging.info("Auto-stop delay cancelled - players are back online.")

    def _auto_stop_delay_worker(self):
        """Worker thread that waits for the auto-stop delay and then stops the server."""
        try:
            time.sleep(settings.autoStopDelay)
            
            # Check if the delay was cancelled
            if not self.auto_stop_delay_cancelled:
                logging.info("Auto-stop delay completed. Stopping server.")
                # The stop_server method was removed, so this will now just log the event.
                # If a stop mechanism is needed, it should be re-added or handled differently.
                logging.info("Auto-stop delay completed. Stopping server (manual intervention required).")
        except Exception as e:
            logging.error(f"Error in auto-stop delay worker: {e}")
            logging.error(traceback.format_exc())

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
    
    def set_on_server_started_callback(self, callback):
        """Set the callback function to be called when the server is started."""
        self.on_server_started_callback = callback
    
    def get_player_manager(self):
        """Get the player manager instance."""
        return self.player_manager

    def start_server_info_update_thread(self):
        """Start a background thread that continuously updates server info."""
        if self.update_thread and self.update_thread.is_alive():
            logging.info("Server info update thread is already running.")
            return
        
        self.update_thread_stop_event.clear()
        self.update_thread = threading.Thread(target=self._server_info_update_loop, daemon=True)
        self.update_thread.start()
        logging.info("Server info update thread started.")

    def stop_server_info_update_thread(self):
        """Stop the background server info update thread."""
        if not self.update_thread or not self.update_thread.is_alive():
            return
        
        self.update_thread_stop_event.set()
        self.update_thread.join(timeout=5)
        logging.info("Server info update thread stopped.")

    def _server_info_update_loop(self):
        """Background loop that continuously updates server info."""
        while not self.update_thread_stop_event.is_set():
            try:
                self.update_current_server_info()
            except Exception as e:
                logging.error(f"Error in server info update loop: {e}")
                logging.error(traceback.format_exc())
            
            # Wait for the specified interval or until stop event is set
            if self.update_thread_stop_event.wait(settings.updateInterval):
                break

    def get_current_server_info(self):
        """Get the current server info without triggering an update."""
        return self.current_server_info