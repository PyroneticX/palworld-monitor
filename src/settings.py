import json
import logging
import traceback

# This is what a Palworld client first sends to the server when it connects.
FIRST_PACKET_PATTERN = b'\x09\x08\x00'

class Settings:
    def __init__(self):
        self.settings = {
            # Operating system type: 'windows' or 'linux'
            'os': 'windows',
            # Path to the Palworld server executable
            'palworldServerExePath': None,
            'palworldMainProcessName': 'PalServer-Win64-Shipping-Cmd.exe',
            # Default arguments for the server executable
            'palworldExeArguments': "-useperfthreads -NoAsyncLoadingThread -UseMultithreadForDS -NumberOfWorkerThreadsServer=16",
            # IP address for the Palworld server
            'palworldServerHost': "127.0.0.1",
            # Port for the Palworld server
            'palworldServerPort': 8211,
            # Initial packet pattern sent by Palworld client
            'firstPacketPattern': FIRST_PACKET_PATTERN,
            # Port for the REST API
            'palworldRESTPort': 8212,
            # Port for the RCON interface
            'palworldRCONPort': 25575,
            # Admin password for the server
            'palworldAdminPassword': "password",
            # Protocol used for server communication
            'protocol': "REST",
            # Whether to enable the web server
            'useWebServer': True,
            # Host for the web server
            'webServerHost': "127.0.0.1",
            # Port for the web server
            'webServerPort': 8213,
            # Show action button in UI
            'showAction': True,
            # Show server ON button in UI
            'showServerOnBtn': True,
            # Show server OFF button in UI
            'showServerOffBtn': True,
            # Show update server status button in UI
            'showUpdateServerStatusBtn': True,
            # Show server IP address in UI
            'showServerIPAddress': False,
            # Enable auto-start for the server
            'useAutoStart': True,
            # Enable auto-stop for the server
            'useAutoStop': True,
            # Seconds before auto-stopping the server
            'ServerAutoStopSeconds': 120,
            # Interval (seconds) to check for auto-stop condition
            'ServerAutoStopCheckInterval': 30,
            # Message shown when server is auto-stopping
            'ServerAutoStopMessage': "Server is shutting down...",
            # Enable player tracking feature
            'enablePlayerTracking': True
        }
        for key, value in self.settings.items():
            setattr(self, key, value)

    def __getitem__(self, key):
        return self.settings[key]

    def __setitem__(self, key, value):
        self.settings[key] = value
        setattr(self, key, value)

    def readSettings(self, file_path):
        try:
            with open(file_path, 'r') as file:
                json_data = json.load(file)
                for key, value in json_data.items():
                    self.settings[key] = value
                    setattr(self, key, value)
                print("Settings loaded successfully.")
        except FileNotFoundError:
            logging.info(f"Error: File {file_path} not found.")
        except json.JSONDecodeError:
            logging.warn(f"Error: Invalid JSON format in {file_path}.")
        except Exception as e:
            logging.error(f"Error from readSettings: {e}")
            logging.error(traceback.format_exc())

        # Validation: ensure no setting is None
        missing = [k for k, v in self.settings.items() if v is None]
        if missing:
            raise ValueError(f"The following settings areq REQUIRED: {missing}")

settings = Settings()
