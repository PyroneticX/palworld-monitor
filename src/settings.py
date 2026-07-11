# Copyright (c) 2024 Nomomo
# Copyright (c) 2026 Kevin Perez - Modified work
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
import shutil
import subprocess
import secrets

FIRST_PACKET_PATTERN = b"\x09\x08\x00"
PALWORLD_MAIN_PROCESS_NAME = "PalServer-Win64-Shipping-Cmd.exe"
PALWORLD_EXE_ARGUMENTS = (
    "-useperfthreads -NoAsyncLoadingThread -UseMultithreadForDS "
    "-NumberOfWorkerThreadsServer=16 -restapi"
)
PALWORLD_SERVER_PORT = 8211
PALWORLD_REST_PORT = 8212
PALWORLD_RCON_PORT = 25575
WEB_SERVER_PORT = 8213
DEFAULT_SESSION_TIMEOUT = 3600
DEFAULT_MAX_LOGIN_ATTEMPTS = 5
DEFAULT_LOCKOUT_DURATION = 300
DEFAULT_RATE_LIMIT_REQUESTS = 100
DEFAULT_RATE_LIMIT_WINDOW = 60


class Settings:
    def __init__(self):
        self.settings = {
            "palworldServerExePath": None,
            "palworldMainProcessName": PALWORLD_MAIN_PROCESS_NAME,
            "palworldExeArguments": PALWORLD_EXE_ARGUMENTS,
            "palworldServerHost": "localhost",
            "palworldServerPort": PALWORLD_SERVER_PORT,
            "firstPacketPattern": FIRST_PACKET_PATTERN,
            "palworldRESTPort": PALWORLD_REST_PORT,
            "palworldRCONPort": PALWORLD_RCON_PORT,
            "palworldServerAdminPassword": None,
            "protocol": "REST",
            "useWebServer": True,
            "webServerPort": WEB_SERVER_PORT,
            "controlServerThroughWeb": True,
            "showServerIPAddress": False,
            "autoStart": True,
            "autoStop": True,
            "autoStopDelay": 120,
            "updateInterval": 30,
            "enablePlayerTracking": True,
            "pollingRate": 5,
            "webUsername": "admin",
            "webPassword": None,
            "sessionSecretKey": None,
            "sessionTimeout": DEFAULT_SESSION_TIMEOUT,
            "maxLoginAttempts": DEFAULT_MAX_LOGIN_ATTEMPTS,
            "lockoutDuration": DEFAULT_LOCKOUT_DURATION,
            "rateLimitEnabled": True,
            "rateLimitRequests": DEFAULT_RATE_LIMIT_REQUESTS,
            "rateLimitWindow": DEFAULT_RATE_LIMIT_WINDOW,
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
        session_key_file = os.path.join(
            os.path.dirname(settings_file_path), "session_secret.key"
        )
        if os.path.exists(session_key_file):
            try:
                with open(session_key_file, "r") as f:
                    saved_key = f.read().strip()
                    if saved_key and len(saved_key) == 64:
                        self.settings["sessionSecretKey"] = saved_key
                        setattr(self, "sessionSecretKey", self.settings["sessionSecretKey"])
                        logging.debug("Loaded sessionSecretKey from session_secret.key")
                        return
            except Exception as e:
                logging.warning(f"Could not read session_secret.key: {e}")

        if not self.settings.get("sessionSecretKey"):
            self.settings["sessionSecretKey"] = secrets.token_hex(32)
            setattr(self, "sessionSecretKey", self.settings["sessionSecretKey"])
            try:
                with open(session_key_file, "w") as f:
                    f.write(self.settings["sessionSecretKey"])
                logging.info("Auto-generated sessionSecretKey and saved to session_secret.key")
            except Exception as e:
                logging.warning(f"Could not save auto-generated sessionSecretKey to file: {e}")

    def _load_nested_settings(self, data):
        """Load settings from nested YAML structure.

        Maps nested keys to expected flat keys for internal use.
        """
        mapping = {
            "palserver": {
                "exePath": "palworldServerExePath",
                "host": "palworldServerHost",
                "port": "palworldServerPort",
                "adminPassword": "palworldServerAdminPassword",
                "protocol": "protocol",
                "restPort": "palworldRESTPort",
                "rconPort": "palworldRCONPort",
                "pollingRate": "pollingRate",
                "exeArguments": "palworldExeArguments",
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

        for domain, domain_mapping in mapping.items():
            if domain in data and isinstance(data[domain], dict):
                for nested_key, flat_key in domain_mapping.items():
                    if nested_key in data[domain]:
                        flat_settings[flat_key] = data[domain][nested_key]

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

                flat_settings = self._load_nested_settings(file_data)

                for key, value in flat_settings.items():
                    self.settings[key] = value
                    setattr(self, key, value)
                print("Settings loaded successfully.")
        except FileNotFoundError:
            logging.warning(f"Settings file not found: {file_path}")
        except yaml.YAMLError as e:
            logging.warning(f"Error: Invalid YAML format in {file_path}: {e}")
        except Exception as e:
            logging.error(f"Error from readSettings: {e}")
            logging.error(traceback.format_exc())

        self._ensure_session_secret_key(file_path)

    def validate_settings(self):
        """Validate that mandatory settings are set and server executable exists.

        Raises:
            ValueError: If mandatory settings are missing or server executable doesn't exist.
        """
        errors = []

        if not self.settings.get("palworldServerExePath"):
            errors.append("palworldServerExePath is required")

        if not self.settings.get("palworldServerAdminPassword"):
            errors.append("palworldServerAdminPassword is required")

        if self.settings.get("useWebServer", True) and not self.settings.get("webPassword"):
            errors.append("webPassword is required when useWebServer is enabled")

        # Validate port ranges (1-65535) for all configured ports
        for name, value in [
            ("palworldServerPort", self.palworldServerPort),
            ("palworldRESTPort", self.palworldRESTPort),
            ("palworldRCONPort", self.palworldRCONPort),
            ("webServerPort", self.webServerPort),
        ]:
            try:
                port = int(value) if isinstance(value, str) else value
                if not 1 <= port <= 65535:
                    errors.append(f"{name} must be between 1 and 65535 (got {port})")
            except Exception:
                errors.append(f"{name} is not a valid integer: {value}")

        # Check that server executable exists
        server_exe_path = self.settings.get("palworldServerExePath")
        if server_exe_path:
            resolved = shutil.which(server_exe_path) or server_exe_path
            if not os.path.exists(resolved):
                errors.append(f"Palworld server executable does not exist at: {server_exe_path}")
            elif not os.path.isfile(resolved):
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
