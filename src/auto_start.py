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
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            test_socket.bind((settings.palworldServerHost, port))
            test_socket.close()
            return True
        except OSError:
            return False

    def open_palworld_port_socket(self):
        """Open socket before listen."""
        try:  
            self.is_aborting = False
            palworld_server_ip = settings.palworldServerHost
            palworld_server_port = settings.palworldServerPort
            
            logging.info("Listening on Palworld Server port for new players...")
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind((palworld_server_ip, palworld_server_port))
            return True
        except OSError as e:
            if e.winerror == 10048:  # WSAEADDRINUSE - Address already in use
                logging.error(f"Palworld port {palworld_server_port} is still in use. Cannot bind to port.")
            else:
                logging.error(f"OSError opening PalWorld port socket: {e}")
            logging.error(traceback.format_exc())
            self.is_aborting = True
            return False
        except Exception as e:
            logging.error(f"Error opening PalWorld port socket: {e}")
            logging.error(traceback.format_exc())
            self.is_aborting = True
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
                logging.error(f"Palworld port {port} is still in use after waiting {timeout} seconds. Aborting listen.")
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
                    logging.info("A player is attempting to connect. Starting Palworld Server...")
                    return True
            except OSError as e:
                # Ignore WinError 10038 (socket operation on non-socket) as it's expected when closing
                if hasattr(e, 'winerror') and e.winerror == 10038:
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
        from process_manager import OSProcessManager
        if self.controller is None or self.controller.is_palworld_process_running():
            return

        if not self.wait_for_port_available(settings.palworldServerPort):
            return

        if not self.open_palworld_port_socket():
            return

        if self.wait_for_player_connection():
            self.close_palworld_port_socket()
            if self.controller is not None:
                self.controller.start_server()

    def listen_palworld_access(self):
        """Start listening for PalWorld access."""
        # Stop any existing listen thread
        self.stop_listen_thread()
        
        # Start new listen thread
        self.listen_thread = threading.Thread(target=self.listen_palworld_access_core)
        self.listen_thread.daemon = True  # Make thread daemon so it exits when main process exits
        self.listen_thread.start()

    def stop_listen_thread(self):
        """Stop the listen thread if it's running."""
        if self.listen_thread and self.listen_thread.is_alive():
            logging.info("Stopping auto-start listen thread...")
            self.is_aborting = True
            self.close_palworld_port_socket()
            self.listen_thread.join(timeout=5)
            self.listen_thread = None
            logging.info("Auto-start listen thread stopped.")

        #TODO: If the server did not start successfully, reconnect the socket after a certain period of time.