from palworld_control import PalWorldController
from rcon_client import RconClient
from rest_client import RestClient
from settings import settings
from web_server import WebServer
from auto_start import AutoStartManager
from auto_stop import AutoStopManager
import threading
import logging
import traceback
import os

if __name__ != '__main__':
    exit()

try:
    # Configure logging to write messages to the console and a file
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # Log to console
            logging.FileHandler('app.log', mode='a')
        ]
    )

    # read settings if settings.json exists
    settings_path = os.path.join(os.path.dirname(__file__), "settings.json")
    settings.readSettings(settings_path)
    
    # Create instances of managers
    auto_start_manager = None
    auto_stop_manager = None

    # Choose the client based on the protocol setting
    if settings.protocol.upper() == 'REST':
        client = RestClient()
    elif settings.protocol.upper() == 'RCON':
        client = RconClient()
    else:
        logging.error(f"Invalid protocol specified in settings: {settings.protocol}")
        exit()

    palworld_controller = PalWorldController(client)

    if settings.useAutoStart:
        auto_start_manager = AutoStartManager(palworld_controller)
        auto_start_manager.listen_palworld_access()
        palworld_controller.set_on_server_stopped_callback(auto_start_manager.listen_palworld_access)

    if settings.useAutoStop:
        auto_stop_manager = AutoStopManager(palworld_controller)
        auto_stop_manager.check_event_stop_server()

    if settings.useWebServer:
        web_server = WebServer(palworld_controller)
        web_server.run()

    # Keep the main thread alive to allow daemon threads to run
    # This will exit gracefully when CTRL+C is pressed
    logging.info("Application started. Press CTRL+C to exit.")
    try:
        while True:
            threading.Event().wait(1)  # Sleep for 1 second intervals
    except KeyboardInterrupt:
        logging.info("CTRL+C received. Shutting down...")
        # Clean up auto start manager if it exists
        if auto_start_manager:
            auto_start_manager.close_palworld_port_socket()

except KeyboardInterrupt:
    logging.info("CTRL+C received during startup. Shutting down...")
except Exception as e:
    logging.error(f"Error from main routine: {e}")
    logging.error(traceback.format_exc())
