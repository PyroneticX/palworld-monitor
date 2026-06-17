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

import yaml
import logging
import traceback
import os
import subprocess
import secrets

# This is what a Palworld client first sends to the server when it connects.
FIRST_PACKET_PATTERN = b"\x09\x08\x00"


class Settings:
    def __init__(self):
        self.settings = {
            # Path to the Palworld server executable
            "palworldServerExePath": None,
            "palworldMainProcessName": "PalServer-Win64-Shipping-Cmd.exe",
            # Default arguments for the server executable
            "palworldExeArguments": "-useperfthreads -NoAsyncLoadingThread -UseMultithreadForDS -NumberOfWorkerThreadsServer=16 -restapi",
            # IP address for the Palworld server
            "palworldServerHost": "localhost",
            # Port for the Palworld server
            "palworldServerPort": 8211,
            # Initial packet pattern sent by Palworld client
            "firstPacketPattern": FIRST_PACKET_PATTERN,
            # Port for the REST API
            "palworldRESTPort": 8212,
            # Port for the RCON interface
            "palworldRCONPort": 25575,
            # Admin password for the Palworld server (used for REST/RCON communication)
            "palworldServerAdminPassword": None,
            # Protocol used for server communication
            "protocol": "REST",
            # WhetherPto enable the web server
            "useWebServer": True,
            # Port for the web server
            "webServerPort": 8213,
            # Enable server control through web interface (combines all button controls)
            "controlServerThroughWeb": True,
            # Show server IP address in UI
            "showServerIPAddress": False,
            # Enable auto-start for the server
            "autoStart": True,
            # Enable auto-stop for the server
            "autoStop": True,
            # Seconds before auto-stopping the server
            "autoStopDelay": 120,
            # Interval (seconds) to check for auto-stop condition
            "updateInterval": 30,
            # Enable player tracking feature
            "enablePlayerTracking": True,
            # Web interface username
            "webUsername": "admin",
            # Web interface password (separate from Palworld server password)
            "webPassword": None,
            # Secret key for session encryption (auto-generated if not provided)
            "sessionSecretKey": None,
            # Session timeout in seconds (default: 1 hour)
            "sessionTimeout": 3600,
            # Maximum failed login attempts before lockout
            "maxLoginAttempts": 5,
            # Lockout duration in seconds after max failed attempts (default: 5 minutes)
            "lockoutDuration": 300,
            # Enable rate limiting for requests
            "rateLimitEnabled": True,
            # Maximum requests per window
            "rateLimitRequests": 100,
            # Rate limit window in seconds
            "rateLimitWindow": 60,
        }
        for key, value in self.settings.items():
            setattr(self, key, value)

    def __getitem__(self, key):
        return self.settings[key]

    def __setitem__(self, key, value):
        self.settings[key] = value
        setattr(self, key, value)

    def _ensure_session_secret_key(self, settings_file_path):
        """Ensure a session secret key exists, loading from file or generating new one.

        Args:
            settings_file_path: Path to the settings file (used to locate session_secret.key)
        """
        # First check if we have a saved session key file
        session_key_file = os.path.join(
            os.path.dirname(settings_file_path), "session_secret.key"
        )
        if os.path.exists(session_key_file):
            try:
                with open(session_key_file, "r") as f:
                    saved_key = f.read().strip()
                    if saved_key and len(saved_key) == 64:
                        self.settings["sessionSecretKey"] = saved_key
                        setattr(
                            self, "sessionSecretKey", self.settings["sessionSecretKey"]
                        )
                        logging.info("Loaded sessionSecretKey from session_secret.key")
                        return
            except Exception as e:
                logging.warning(f"Could not read session_secret.key: {e}")

        # Generate new key if missing or invalid
        if not self.settings.get("sessionSecretKey"):
            self.settings["sessionSecretKey"] = secrets.token_hex(32)
            setattr(self, "sessionSecretKey", self.settings["sessionSecretKey"])

            # Save the generated key to a separate file (preserves settings.yaml comments)
            try:
                with open(session_key_file, "w") as f:
                    f.write(self.settings["sessionSecretKey"])
                logging.info(
                    "Auto-generated sessionSecretKey and saved to session_secret.key"
                )
            except Exception as e:
                logging.warning(
                    f"Could not save auto-generated sessionSecretKey to file: {e}"
                )

    def _load_nested_settings(self, data):
        """Load settings from nested YAML structure.

        Maps nested keys to expected flat keys for internal use.
        """
        # Mapping from nested structure to flat keys
        mapping = {
            "palserver": {
                "exePath": "palworldServerExePath",
                "host": "palworldServerHost",
                "port": "palworldServerPort",
                "adminPassword": "palworldServerAdminPassword",
                "protocol": "protocol",
                "restPort": "palworldRESTPort",
                "rconPort": "palworldRCONPort",
            },
            "web": {
                "enabled": "useWebServer",
                "port": "webServerPort",
                "username": "webUsername",
                "password": "webPassword",
                "controlServer": "controlServerThroughWeb",
                "showServerIP": "showServerIPAddress",
            },
            "features": {
                "playerTracking": "enablePlayerTracking",
                "autoStart": "autoStart",
                "autoStop": "autoStop",
            },
            "autoStop": {
                "stopDelay": "autoStopDelay",
                "updateInterval": "updateInterval",
            },
            "security": {
                "sessionSecretKey": "sessionSecretKey",
                "sessionTimeout": "sessionTimeout",
                "maxLoginAttempts": "maxLoginAttempts",
                "lockoutDuration": "lockoutDuration",
                "rateLimitEnabled": "rateLimitEnabled",
                "rateLimitRequests": "rateLimitRequests",
                "rateLimitWindow": "rateLimitWindow",
            },
        }

        flat_settings = {}

        # Process nested structure
        for domain, domain_mapping in mapping.items():
            if domain in data and isinstance(data[domain], dict):
                for nested_key, flat_key in domain_mapping.items():
                    if nested_key in data[domain]:
                        flat_settings[flat_key] = data[domain][nested_key]

        # Include any top-level keys that might exist (like sessionSecretKey if moved)
        for key, value in data.items():
            if key not in mapping and isinstance(value, (str, int, bool, type(None))):
                flat_settings[key] = value

        return flat_settings

    def readSettings(self, file_path):
        try:
            with open(file_path, "r") as file:
                file_data = yaml.safe_load(file)
                if file_data is None:
                    file_data = {}

                # Load settings from nested structure
                flat_settings = self._load_nested_settings(file_data)

                # Update settings with flattened values
                for key, value in flat_settings.items():
                    self.settings[key] = value
                    setattr(self, key, value)
                print("Settings loaded successfully.")
        except FileNotFoundError:
            logging.info(f"Error: File {file_path} not found.")
        except yaml.YAMLError as e:
            logging.warning(f"Error: Invalid YAML format in {file_path}: {e}")
        except Exception as e:
            logging.error(f"Error from readSettings: {e}")
            logging.error(traceback.format_exc())

        # Load or generate session secret key
        self._ensure_session_secret_key(file_path)

    def validate_settings(self):
        """Validate that mandatory settings are set and server executable exists.

        Raises:
            ValueError: If mandatory settings are missing or server executable doesn't exist.
        """
        errors = []

        # Check mandatory settings
        if not self.settings.get("palworldServerExePath"):
            errors.append("palworldServerExePath is required")

        if not self.settings.get("palworldServerAdminPassword"):
            errors.append("palworldServerAdminPassword is required")

        # Check webPassword only if web server is enabled
        if self.settings.get("useWebServer", True) and not self.settings.get(
            "webPassword"
        ):
            errors.append("webPassword is required when useWebServer is enabled")

        # Check that server executable exists
        server_exe_path = self.settings.get("palworldServerExePath")
        if server_exe_path:
            if not os.path.exists(server_exe_path):
                errors.append(
                    f"Palworld server executable does not exist at: {server_exe_path}"
                )
            elif not os.path.isfile(server_exe_path):
                errors.append(f"Palworld server path is not a file: {server_exe_path}")

        if errors:
            error_message = "Settings validation failed:\n" + "\n".join(
                f"  - {error}" for error in errors
            )
            raise ValueError(error_message)

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
