# Copyright (c) 2024 Nomomo
# Copyright (c) 2026 Kevin Perez - Modified work
#
# Permission is hereby granted, free of charge to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

"""Hardcoded constants used across the application."""

import os

# --- Palworld server ports ---
PALWORLD_SERVER_PORT = 8211
PALWORLD_REST_PORT = 8212
PALWORLD_RCON_PORT = 25575
WEB_SERVER_PORT = 8213

# --- Packet constants ---
FIRST_PACKET_PATTERN = b"\x09\x08\x00"

# --- Process names / arguments ---
PALWORLD_MAIN_PROCESS_NAME = "PalServer-Win64-Shipping-Cmd.exe"
PALWORLD_EXE_ARGUMENTS = (
    "-useperfthreads -NoAsyncLoadingThread -UseMultithreadForDS "
    "-NumberOfWorkerThreadsServer=16 -restapi"
)

# --- Session secret key file ---
SESSION_SECRET_KEY_FILE = "session_secret.key"
SESSION_SECRET_KEY_LENGTH = 64

# --- Defaults ---
DEFAULT_UPDATE_INTERVAL = 30
DEFAULT_AUTO_STOP_DELAY = 120
DEFAULT_SESSION_TIMEOUT = 3600
DEFAULT_MAX_LOGIN_ATTEMPTS = 5
DEFAULT_LOCKOUT_DURATION = 300
DEFAULT_RATE_LIMIT_REQUESTS = 100
DEFAULT_RATE_LIMIT_WINDOW = 60

# --- Socket / retry defaults ---
SOCKET_REUSEADDR = 1
SOCKET_REUSEPORT = 1
MAX_SOCKET_RETRIES = 5
SOCKET_RETRY_DELAY = 2
WAIT_FOR_PORT_TIMEOUT = 30
WAIT_FOR_PORT_POLL_INTERVAL = 1
