"""End-to-end smoke test for the Palworld Monitor autostart feature.

Starts the monitor app, sends the magic client packet via UDP, and verifies
that the Palworld server process is spawned.  No browser required.

Run with: uv run poe smoke -k autostart
"""

import socket
import time

import pytest

from src.settings import settings
from .helpers import kill_existing_palworld, is_palworld_running

pytestmark = pytest.mark.e2e


def test_autostart(app_process):
    """Send the autostart packet and verify the server starts."""
    kill_existing_palworld()
    time.sleep(2)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.sendto(
            settings.firstPacketPattern,
            (settings.palworldServerHost, settings.palworldServerPort),
        )
    finally:
        sock.close()

    deadline = time.time() + 30
    while time.time() < deadline:
        if is_palworld_running():
            return
        time.sleep(1)

    pytest.fail("Palworld server did not start after sending autostart packet")
