import logging
import traceback
import schedule
import time
import threading
from settings import Settings

STOP_SERVER_VARIABLES = {
    "stopEventTriggeredTime": 1.0E+100,
    "isRunningStopwatchToStopServer": False,
    "leftTimeToStopServer": -1
}

class AutoStopManager:
    def __init__(self, palworld_controller):
        self.controller = palworld_controller

    def check_event_stop_server_core(self):
        """Check server stop every minute if there are no players"""
        try:
            if not self.controller.is_palworld_process_running():
                STOP_SERVER_VARIABLES["isRunningStopwatchToStopServer"] = False
                return

            if self.controller.is_stop_event_running():
                return        
            
            current_server_info = self.controller.update_current_server_info()
            if current_server_info is None:
                logging.error("An error occurred while updating the current server, and as a result, the stop server event cannot be triggered.")
                STOP_SERVER_VARIABLES["isRunningStopwatchToStopServer"] = False
                return
            player_count = current_server_info["playerCount"]
            if player_count > 0:
                STOP_SERVER_VARIABLES["isRunningStopwatchToStopServer"] = False
                return
            
            # check time
            current_time = time.time()
            if not STOP_SERVER_VARIABLES["isRunningStopwatchToStopServer"]:
                STOP_SERVER_VARIABLES["stopEventTriggeredTime"] = time.time()     # save triggered time
                STOP_SERVER_VARIABLES["isRunningStopwatchToStopServer"] = True    # save flag

            server_auto_stop_seconds = Settings.ServerAutoStopSeconds
            passed_time = current_time - STOP_SERVER_VARIABLES["stopEventTriggeredTime"]
            if passed_time >= server_auto_stop_seconds:
                self.controller.stop_server(delay_seconds=1)
               
                STOP_SERVER_VARIABLES["stopEventTriggeredTime"] = time.time() # to prevent call stopServer multiple times
                STOP_SERVER_VARIABLES["leftTimeToStopServer"] = 0.0
            else:
                STOP_SERVER_VARIABLES["leftTimeToStopServer"] = int(server_auto_stop_seconds - passed_time)

        except Exception as e:
            logging.error(f"Error from checkEventStopServerCore: {e}")
            logging.error(traceback.format_exc())
            return None

    def run_schedule(self):
        """Run the scheduled tasks"""
        server_auto_stop_check_interval = Settings.ServerAutoStopCheckInterval
        while True:
            schedule.run_pending()
            time.sleep(server_auto_stop_check_interval * 0.1)

    def check_event_stop_server(self):
        """Start the auto-stop server monitoring"""

        # manually start once
        self.check_event_stop_server_core()

        server_auto_stop_check_interval = int(Settings.ServerAutoStopCheckInterval)
        schedule.every(server_auto_stop_check_interval).seconds.do(self.check_event_stop_server_core)

        thread = threading.Thread(target=self.run_schedule)
        thread.daemon = True  # Make thread daemon so it exits when main process exits
        thread.start()

    def get_left_time_to_stop_server(self):
        """Get the remaining time before server stops"""
        return STOP_SERVER_VARIABLES["leftTimeToStopServer"]

    def is_running_stopwatch_to_stop_server(self):
        """Check if the stopwatch for server stop is running"""
        return STOP_SERVER_VARIABLES["isRunningStopwatchToStopServer"]
