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

import json
import logging
import traceback
import os
import subprocess
import secrets

# This is what a Palworld client first sends to the server when it connects.
FIRST_PACKET_PATTERN = b'\x09\x08\x00'

class Settings:
    def __init__(self):
        self.settings = {
            # Path to the Palworld server executable
            'palworldServerExePath': None,
            'palworldMainProcessName': 'PalServer-Win64-Shipping-Cmd.exe',
            # Default arguments for the server executable
            'palworldExeArguments': "-useperfthreads -NoAsyncLoadingThread -UseMultithreadForDS -NumberOfWorkerThreadsServer=16",
            # IP address for the Palworld server
            'palworldServerHost': "localhost",
            # Port for the Palworld server
            'palworldServerPort': 8211,
            # Initial packet pattern sent by Palworld client
            'firstPacketPattern': FIRST_PACKET_PATTERN,
            # Port for the REST API
            'palworldRESTPort': 8212,
            # Port for the RCON interface
            'palworldRCONPort': 25575,
            # Admin password for the Palworld server (used for REST/RCON communication)
            'palworldServerAdminPassword': None,
            # Protocol used for server communication
            'protocol': "REST",
            # WhetherPto enable the web server
            'useWebServer': True,
            # Port for the web server
            'webServerPort': 8213,
            # Enable server control through web interface (combines all button controls)
            'controlServerThroughWeb': True,
            # Show server IP address in UI
            'showServerIPAddress': False,
            # Enable auto-start for the server
            'autoStart': True,
            # Enable auto-stop for the server
            'autoStop': True,
            # Seconds before auto-stopping the server
            'autoStopDelay': 120,
            # Interval (seconds) to check for auto-stop condition
            'updateInterval': 30,
            # Enable player tracking feature
            'enablePlayerTracking': True,
            # Web interface username
            'webUsername': 'admin',
            # Web interface password (separate from Palworld server password)
            'webPassword': None,
            # Secret key for session encryption (auto-generated if not provided)
            'sessionSecretKey': None,
            # Session timeout in seconds (default: 1 hour)
            'sessionTimeout': 3600,
            # Maximum failed login attempts before lockout
            'maxLoginAttempts': 5,
            # Lockout duration in seconds after max failed attempts (default: 5 minutes)
            'lockoutDuration': 300,
            # Enable rate limiting for requests
            'rateLimitEnabled': True,
            # Maximum requests per window
            'rateLimitRequests': 100,
            # Rate limit window in seconds
            'rateLimitWindow': 60
        }
        for key, value in self.settings.items():
            setattr(self, key, value)

    def __getitem__(self, key):
        return self.settings[key]

    def __setitem__(self, key, value):
        self.settings[key] = value
        setattr(self, key, value)

    def readSettings(self, file_path):
        file_data = None
        file_loaded = False
        
        try:
            with open(file_path, 'r') as file:
                file_data = json.load(file)
                file_loaded = True
                for key, value in file_data.items():
                    self.settings[key] = value
                    setattr(self, key, value)
                print("Settings loaded successfully.")
        except FileNotFoundError:
            logging.info(f"Error: File {file_path} not found.")
        except json.JSONDecodeError:
            logging.warning(f"Error: Invalid JSON format in {file_path}.")
        except Exception as e:
            logging.error(f"Error from readSettings: {e}")
            logging.error(traceback.format_exc())

        # Auto-generate sessionSecretKey if missing or None
        if not self.settings.get('sessionSecretKey'):
            self.settings['sessionSecretKey'] = secrets.token_hex(32)
            setattr(self, 'sessionSecretKey', self.settings['sessionSecretKey'])
            
            # Save the generated key back to the settings file
            try:
                with open(file_path, 'r') as file:
                    file_data = json.load(file)
                file_data['sessionSecretKey'] = self.settings['sessionSecretKey']
                with open(file_path, 'w') as file:
                    json.dump(file_data, file, indent=4)
                logging.info("Auto-generated sessionSecretKey and saved to settings.json")
            except Exception as e:
                logging.warning(f"Could not save auto-generated sessionSecretKey to file: {e}")

        # Validation: ensure no setting is None (excluding sessionSecretKey which is auto-generated)
        missing = [k for k, v in self.settings.items() if v is None]
        if missing:
            raise ValueError(f"The following settings areq REQUIRED: {missing}")

    def get_git_hash(self):
        """Return the current git commit hash.
        Tries to use `git rev-parse HEAD`. If git is not available or the command fails,
        returns None.
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.path.dirname(__file__),
                check=True,
            )
            return result.stdout.strip()
        except Exception:
            return None

settings = Settings()
