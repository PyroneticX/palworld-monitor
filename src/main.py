# Copyright (c) 2024 Nomomo
# Copyright (c) 2024 Kevin Perez - Modified work

from src.palworld_control import PalWorldController
from src.settings import settings
from src.web_server import WebServer
from src.auto_start import AutoStartManager
import threading
import logging
import traceback
import os

if __name__ != "__main__":
    exit()

try:
    log_level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)

    # Configure logging to write messages to the console and a file
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),  # Log to console
            logging.FileHandler("app.log", mode="w"),
        ],
    )

    # read settings if settings.yaml exists
    settings_path = os.path.join(os.path.dirname(__file__), "settings.yaml")
    settings.readSettings(settings_path)

    # Validate settings at startup
    try:
        settings.validate_settings()
    except ValueError as e:
        logging.error(e)
        logging.error("Please fix the settings and try with valid configuration.")
        exit(1)

    # Create instances of managers
    auto_start_manager = None

    # Choose the client based on the protocol setting
    if settings.protocol.upper() == "REST":
        from src.api_clients import RestClient
        client = RestClient()
    elif settings.protocol.upper() == "RCON":
        from src.api_clients import RconClient
        client = RconClient()
    else:
        logging.error(f"Invalid protocol specified in settings: {settings.protocol}")
        exit()

    palworld_controller = PalWorldController(client)

    # Start the background server info update thread only if server is running
    server_running = palworld_controller.is_palworld_process_running()
    if server_running:
        palworld_controller.start_server_info_update_thread()

    if settings.autoStart:
        auto_start_manager = AutoStartManager(palworld_controller)

        if not server_running:
            auto_start_manager.listen_palworld_access()
    if settings.useWebServer:
        web_server = WebServer(palworld_controller)
        web_server.run()

    # Keep the main thread alive to allow daemon threads to run
    logging.info("Application started. Press CTRL+C to exit.")
    try:
        while True:
            threading.Event().wait(1)  # Sleep for 1 second intervals
    except KeyboardInterrupt:
        logging.info("CTRL+C received. Shutting down...")
        # Stop the background update thread
        palworld_controller.stop_server_info_update_thread()
        # Clean up auto start manager if it exists
        if auto_start_manager:
            auto_start_manager.close_palworld_port_socket()

except KeyboardInterrupt:
    logging.info("CTRL+C received during startup. Shutting down...")
except Exception as e:
    logging.error(f"Error from src.main routine: {e}")
    logging.error(traceback.format_exc())

if __name__ != "__main__":
    exit()
