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

from palworld_control import PalWorldController
from settings import settings
from web_server import WebServer
from auto_start import AutoStartManager
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

    # Choose the client based on the protocol setting
    if settings.protocol.upper() == 'REST':
        from api_clients import RestClient
        client = RestClient()
    elif settings.protocol.upper() == 'RCON':
        from api_clients import RconClient
        client = RconClient()
    else:
        logging.error(f"Invalid protocol specified in settings: {settings.protocol}")
        exit()

    palworld_controller = PalWorldController(client)
    
    # Start the background server info update thread only if server is running
    server_running = palworld_controller.is_palworld_process_running()
    if server_running:
        palworld_controller.start_server_info_update_thread()

    if not server_running and settings.autoStart:
        auto_start_manager = AutoStartManager(palworld_controller)
        
        palworld_controller.set_on_server_started_callback(auto_start_manager.stop_listen_thread)
        palworld_controller.set_on_server_stopped_callback(auto_start_manager.listen_palworld_access)
        
        auto_start_manager.listen_palworld_access()

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
        # Stop the background update thread
        palworld_controller.stop_server_info_update_thread()
        # Clean up auto start manager if it exists
        if auto_start_manager:
            auto_start_manager.close_palworld_port_socket()

except KeyboardInterrupt:
    logging.info("CTRL+C received during startup. Shutting down...")
except Exception as e:
    logging.error(f"Error from main routine: {e}")
    logging.error(traceback.format_exc())
