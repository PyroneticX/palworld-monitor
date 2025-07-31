import socket
from settings import Settings
from palWorldControl import PalWorldController
import logging
import threading
import traceback
from typing import Optional

class AutoStartManager:
    def __init__(self, palworld_controller: Optional[PalWorldController]):
        self.controller: Optional[PalWorldController] = palworld_controller
        self.sock = None
        self.is_break = False

    def is_port_available(self, port):
        """Check if PalWorld server port is available."""
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.bind(("localhost", port))
            test_socket.close()
            return True
        except OSError:
            return False

    def open_palworld_port_socket(self):
        """Open socket before listen."""
        try:  
            self.is_break = False
            palworld_server_ip = Settings.palworldServerIP
            palworld_server_port = Settings.palworldServerPort
            
            logging.info("Listening on Palworld Server port for new players")
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind((palworld_server_ip, palworld_server_port))
            return True
        except Exception as e:
            logging.error(f"Error opening PalWorld port socket: {e}")
            logging.error(traceback.format_exc())
            self.is_break = True
            return False

    def close_palworld_port_socket(self):
        """Close socket."""
        logging.info("No longer listening on Palworld Server port")
        self.is_break = True
        try:
            if self.sock is None:
                return
            
            self.sock.close()
            self.sock = None
            return True
        except Exception as e:
            logging.error(f"Error closing PalWorld port socket: {e}")
            logging.error(traceback.format_exc())
            self.sock = None
            return False

    def listen_palworld_access_core(self):
        """Listen from PalWorld server port."""
        if self.controller is None or self.controller.is_palworld_process_running():
            return

        if not self.is_port_available(Settings.palworldServerPort):
            return
        
        if not self.open_palworld_port_socket():
            logging.error(f"Unable to open a socket to wait for the Palworld connection packet.")
            return

        is_server_started = False

        while True:
            try:
                if self.is_break:
                    self.close_palworld_port_socket()
                    break

                if self.sock is None:
                    break

                data, addr = self.sock.recvfrom(1024)
                hex_data = " ".join(format(byte, "02X") for byte in data)

                if data.startswith(Settings.firstPacketPattern):
                    logging.info("A player is attempting to connect. Starting Palworld Server...")
                    is_server_started = True
                    break
            except OSError as e:
                # Silently ignore WinError 10038 (not a socket)
                if hasattr(e, 'winerror') and e.winerror == 10038:
                    pass
                else:
                    logging.error(f"OSError in listen_palworld_access_core: {e}")
                    logging.error(traceback.format_exc())
            except Exception as e:
                logging.error(f"Error in listen_palworld_access_core: {e}")
                logging.error(traceback.format_exc())
                
        if is_server_started:
            self.close_palworld_port_socket()
            if self.controller is not None:
                self.controller.start_server()

    def listen_palworld_access(self):
        """Start listening for PalWorld access."""
        thread = threading.Thread(target=self.listen_palworld_access_core)
        thread.daemon = True  # Make thread daemon so it exits when main process exits
        thread.start()

        #TODO: If the server did not start successfully, reconnect the socket after a certain period of time.