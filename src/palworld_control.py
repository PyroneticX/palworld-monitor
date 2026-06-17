# Copyright (c 2024 Nomomo
# Copyright (c) 2024 Kevin Perez - Modified work

import logging
import time
import threading
from src.settings import settings
from src.player_manager import PlayerManager
from src.banlist_manager import BanlistManager
from src.events import bus, Event
import os
import platform

class PalWorldController:
    def __init__(self, client, process_manager=None, player_manager=None, banlist_manager=None):
        self.client = client
        self.player_manager = player_manager if player_manager is not None else PlayerManager()
        self.banlist_manager = banlist_manager if banlist_manager is not None else BanlistManager()
        
        if process_manager is not None:
            self.process_manager = process_manager
        else:
            self.process_manager = self._create_process_manager()

        self.current_server_info = {"running": False, "playerCount": 0, "players": []}
        self.is_palworld_server_starting = False
        self.server_starting_cooldown = 5
        self.last_server_started_time = 0
        self.server_stopping_cooldown = 5
        self.last_server_stopped_time = 0
        self.server_startup_auto_stop_delay = settings.autoStopDelay

        self._auto_mode_cancelled = False
        self.update_thread = None
        self.update_thread_stop_event = threading.Event()
        self.auto_stop_delay_thread = None

        self._setup_subscriptions()
        self._detect_existing_server_process()

    def _create_process_manager(self):
        detected_os = platform.system()
        if detected_os.lower() == "linux":
            from src.process_manager import LinuxProcessManager
            return LinuxProcessManager()
        else:
            from src.process_manager import WindowsProcessManager
            return WindowsProcessManager()

    def _setup_subscriptions(self):
        bus.subscribe(Event.SERVER_STARTED, self._on_server_started)
        bus.subscribe(Event.SERVER_STOPPED, self._on_server_stopped)
        bus.subscribe(Event.PLAYER_JOINED, self._on_player_update)
        bus.subscribe(Event.PLAYER_LEFT, self._on_player_update)
        bus.subscribe(Event.BAN_ADDED, self._on_ban_update)
    def _on_server_started(self, data):
        self.last_server_started_time = time.time()
        self.is_palworld_server_starting = False
        logging.info(f"Controller: Server started event received (PID: {data.get('pid')})")
        self.start_server_info_update_thread()

    def _on_server_stopped(self, data):
        self.last_server_stopped_time = time.time()
        logging.info("Controller: Server stopped event received")
        self.stop_server_info_update_thread()

    def _on_player_update(self, data):
        pass

    def _on_ban_update(self, data):
        pass

    def is_palworld_process_running(self):
        return self.process_manager.is_process_running()

    def start_server(self):
        logging.info("Palworld server start command received")
        current_time = time.time()
        if self._should_block_start(current_time):
            return False
        try:
            bus.publish(Event.CMD_START_SERVER, {
                'exe_path': settings.palworldServerExePath,
                'exe_args': settings.palworldExeArguments
            })
            self.is_palworld_server_starting = True
            return True
        except Exception as e:
            logging.error(f"Error issuing start command: {e}")
            return False

    def _should_block_start(self, current_time):
        if self.is_palworld_process_running():
            logging.warning("The attempt to start the Palworld server was made, but it is already running.")
            return True
        if self.is_palworld_server_starting:
            logging.warning("Palworld Server is already starting.")
            return True
        if current_time - self.last_server_started_time < self.server_starting_cooldown:
            logging.warning("Tried to start the server too quickly multiple times.")
            return True
        if current_time - self.last_server_stopped_time < self.server_stopping_cooldown:
            logging.warning("You attempted to restart the server too quickly after trying to stop it.")
            return True
        return False

    def _detect_existing_server_process(self):
        try:
            if not self.process_manager.launched_pid and not os.path.exists(self.process_manager.pid_file_name()):
                pid = self.process_manager.find_process_pid("palserver")
                if pid:
                    self.process_manager.set_known_pid(pid)
        except Exception:
            pass

    def stop_server(self,):
        logging.info("Palworld server stop command received")
        if self._should_block_stop():
            return False
        self._cancel_auto_stop_delay()
        try:
            bus.publish(Event.CMD_STOP_SERVER, {})
            return True
        except Exception as e:
            logging.error(f"Error issuing stop command: {e}")
            return False

    def _should_block_stop(self):
        if not self.is_palworld_process_running():
            logging.error("An attempt to stop the Palworld server was made, but it was not running.")
            return True
        current_time = time.time()
        if current_time - self.last_server_stopped_time < self.server_stopping_cooldown:
            logging.warning("You attempted to restart the server too Quickly after trying to stop it.")
            return True
        return False

    def update_current_server_info(self):
        try:
            self._update_server_info_with_players()
            if settings.autoStop and self.player_manager.get_player_count() == 0:
                self._handle_auto_stop_condition()
            else:
                self._cancel_auto_stop_delay()
            return self.current_server_info
        except Exception as e:
            logging.error(f"Error in update: {e}")
            return None

    def _update_server_info_with_players(self):
        self.current_server_info["running"] = self.is_palworld_process_running()
        players = self.get_player_names()
        self.current_server_info["playerCount"] = len(players)
        self.current_server_info["players"] = players
        if settings.enablePlayerTracking:
            self.player_manager.update_players_from_server(players)

    def _handle_auto_stop_condition(self):
        if self.auto_stop_delay_thread and self.auto_stop_delay_thread.is_alive():
            return
        if time.time() - self.last_server_started_time < self.server_startup_auto_stop_delay:
            remaining = self.server_startup_auto_stop_delay - (time.time() - self.last_server_started_time)
            logging.info(f"Auto-stop startup guard active, {remaining:.0f}s remaining")
            return
        logging.info("Auto-stop condition met, starting delay thread")
        self._auto_mode_cancelled = False
        self.auto_stop_delay_thread = threading.Thread(target=self._auto_stop_delay_worker, daemon=True)
        self.auto_stop_delay_thread.start()

    def _cancel_auto_stop_delay(self):
        if self.auto_stop_delay_thread and self.auto_stop_delay_thread.is_alive():
            logging.info("Auto-stop cancelled (players detected)")
            self._auto_mode_cancelled = True

    def _auto_stop_delay_worker(self):
        logging.info(f"Auto-stop delay started, stopping in {settings.autoStopDelay}s")
        time.sleep(settings.autoStopDelay)
        if self._auto_mode_cancelled:
            logging.info("Auto-stop cancelled during sleep")
            return
        logging.info("Auto-stop delay elapsed, stopping server")
        self.stop_server()

    def get_player_count(self): return self.client.get_player_count()
    def get_player_names(self): return self.client.get_player_names()
    def get_players_for_web(self): return self.player_manager.get_all_players()

    def kick_player(self, steam_id):
        try:
            bus.publish(Event.CMD_KICK_PLAYER, {"steam_id": steam_id})
            return True
        except Exception as e:
            logging.error(f"Error kicking {steam_id}: {e}")
            return False

    def ban_player(self, steam_id):
        try:
            bus.publish(Event.CMD_BAN_PLAYER, {"steam_id": steam_id})
            return True
        except Exception as e:
            logging.error(f"Error banning {steam_id}: {e}")
            return False

    def unban_player(self, steam_id):
        try:
            bus.publish(Event.CMD_UNBAN_PLAYER, {"steam_id": steam_id})
            return True
        except Exception as e:
            logging.error(f"Error unbanning {steam_id}: {e}")
            return False

    def get_banned_players(self): return self.banlist_manager.get_banned_players()
    def is_player_banned(self, steam_id): return self.banlist_manager.is_banned(steam_id)

    def start_server_info_update_thread(self):
        if not (self.update_thread and self.update_thread.is_alive()):
            self.update_thread_stop_event.clear()
            self.update_thread = threading.Thread(target=self._server_info_update_loop, daemon=True)
            self.update_thread.start()

    def stop_server_info_update_thread(self):
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread_stop_event.set()
            self.update_thread.join(timeout=5)

    def _server_info_update_loop(self):
        while not self.update_thread_stop_event.is_set():
            try:
                self.update_current_server_info()
            except Exception as e:
                logging.error(f"Update loop error: {e}")
            if self.update_thread_stop_event.wait(settings.updateInterval):
                break

    def get_current_server_for_web(self):
        return self.current_server_info
