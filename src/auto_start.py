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

import socket
from settings import settings
from palworld_control import PalWorldController
import logging
import threading
import traceback
from typing import Optional
import time


class AutoStartManager:
    def __init__(self, palworld_controller: Optional[PalWorldController]):
        self.controller: Optional[PalWorldController] = palworld_controller
        self.sock = None
        self.is_aborting = False
        self.listen_thread = None

    def is_port_available(self, port):
        """Check if PalWorld server port is available."""
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except OSError:
                # SO_REUSEPORT might not be available on all systems
                pass
            test_socket.bind((settings.palworldServerHost, port))
            test_socket.close()
            return True
        except OSError:
            return False

    def open_palworld_port_socket(self):
        """Open socket before listen."""
        max_retries = 5
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                self.is_aborting = False
                palworld_server_port = settings.palworldServerPort

                if attempt == 0:
                    logging.info("Listening on Palworld Server port for new players...")
                else:
                    logging.info(
                        f"Retrying to bind to Palworld Server port... (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(1)  # Small delay before retry
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                # Set socket reuse options to handle port conflicts
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                except (OSError, AttributeError):
                    # SO_REUSEPORT might not be available on all systems
                    pass
                self.sock.bind(("0.0.0.0", palworld_server_port))
                return True
            except OSError as e:
                # Check for address already in use error (Windows: 10048, Linux: 98)
                if (
                    hasattr(e, "winerror") and e.winerror == 10048
                ):  # WSAEADDRINUSE - Address already in use
                    logging.error(
                        f"Palworld port {palworld_server_port} is still in use. Cannot bind to port."
                    )
                elif (
                    hasattr(e, "errno") and e.errno == 98
                ):  # EADDRINUSE - Address already in use (Linux)
                    logging.error(
                        f"Palworld port {palworld_server_port} is still in use. Cannot bind to port."
                    )
                else:
                    logging.error(f"OSError opening PalWorld port socket: {e}")

                if attempt < max_retries - 1:
                    logging.info(
                        f"Retrying in {retry_delay} seconds... (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(retry_delay)
                    continue
                else:
                    logging.error(traceback.format_exc())
                    self.is_aborting = True
                    return False
            except Exception as e:
                logging.error(f"Error opening PalWorld port socket: {e}")
                logging.error(traceback.format_exc())
                self.is_aborting = True
                return False

        return False

    def close_palworld_port_socket(self):
        """Close socket."""
        if self.sock is None:
            return True

        logging.info("No longer listening on Palworld Server port")
        self.is_aborting = True
        try:
            self.sock.close()
            self.sock = None
            return True
        except Exception as e:
            logging.error(f"Error closing PalWorld port socket: {e}")
            logging.error(traceback.format_exc())
            self.sock = None
            return False

    def wait_for_port_available(self, port, timeout=30):
        """Wait up to `timeout` seconds for the port to become available. Returns True if available, False if timeout."""
        start_time = time.time()
        logging.info(f"Waiting for Palworld port {port} to become available...")
        while not self.is_port_available(port):
            if time.time() - start_time > timeout:
                logging.error(
                    f"Palworld port {port} is still in use after waiting {timeout} seconds. Aborting listen."
                )
                return False
            time.sleep(1)
        return True

    def wait_for_player_connection(self):
        """Wait for a player connection packet. Returns True if detected, False otherwise."""
        while not self.is_aborting:
            if not self._should_continue_listening():
                return False

            try:
                data, _addr = self.sock.recvfrom(1024)
                if self._is_player_connection_packet(data):
                    logging.info(
                        "A player is attempting to connect. Starting Palworld Server..."
                    )
                    return True
            except OSError as e:
                # Ignore socket operation on non-socket error (Windows: 10038, Linux: 88)
                if hasattr(e, "winerror") and e.winerror == 10038:
                    return self._handle_socket_error()
                elif (
                    hasattr(e, "errno") and e.errno == 88
                ):  # ENOTSOCK - Socket operation on non-socket (Linux)
                    return self._handle_socket_error()
                logging.error(f"OSError in wait_for_player_connection: {e}")
                logging.error(traceback.format_exc())
                return self._handle_socket_error()
            except Exception as e:
                logging.error(f"Error in wait_for_player_connection: {e}")
                logging.error(traceback.format_exc())
                return self._handle_socket_error()

        return False

    def _should_continue_listening(self):
        """Check if we should continue listening for connections."""
        if self.is_aborting:
            return False
        return self.sock is not None

    def _is_player_connection_packet(self, data):
        """Check if the received data is a player connection packet."""
        return data.startswith(settings.firstPacketPattern)

    def _handle_socket_error(self):
        """Handle socket errors by returning False."""
        return False

    def listen_palworld_access_core(self):
        """Listen from PalWorld server port."""
        if self.controller is None or self.controller.is_palworld_process_running():
            return

        max_start_retries = 3
        retry_delay = 10

        for attempt in range(max_start_retries):
            if self.is_aborting:
                return

            if not self.open_palworld_port_socket():
                return

            if self.wait_for_player_connection():
                self.close_palworld_port_socket()
                time.sleep(0.5)
                if self.controller is not None:
                    self.controller.start_server()
                    time.sleep(2)
                    if self.controller.is_palworld_process_running():
                        return
                    logging.warning(
                        f"Server did not start successfully (attempt {attempt + 1}/{max_start_retries}). "
                        f"Reconnecting socket in {retry_delay}s..."
                    )
                    time.sleep(retry_delay)
                else:
                    return
            else:
                self.close_palworld_port_socket()
                return

    def listen_palworld_access(self):
        """Start listening for PalWorld access."""
        # Stop any existing listen thread
        self.stop_listen_thread()

        # Add a small delay to allow the port to be released
        time.sleep(1)

        # Start new listen thread
        self.listen_thread = threading.Thread(target=self.listen_palworld_access_core)
        self.listen_thread.daemon = (
            True  # Make thread daemon so it exits when main process exits
        )
        self.listen_thread.start()

    def stop_listen_thread(self):
        """Stop the listen thread if it's running."""
        if self.listen_thread and self.listen_thread.is_alive():
            logging.info("Stopping auto-start listen thread...")
            self.is_aborting = True
            self.close_palworld_port_socket()

            # Don't join if we're in the same thread to avoid deadlock
            if threading.current_thread() != self.listen_thread:
                self.listen_thread.join(timeout=5)
            else:
                logging.info("Skipping thread join to avoid deadlock")

            self.listen_thread = None
            logging.info("Auto-start listen thread stopped.")
