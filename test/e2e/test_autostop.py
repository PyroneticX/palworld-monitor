"""End-to-end smoke test for the Palworld Monitor autostop feature.

Run with: uv run poe smoke -k autostop
"""

import os
import subprocess
import sys
import time
from pathlib import Path

import psutil
import pytest

from .helpers import run_monitor_app

pytestmark = pytest.mark.e2e


DUMMY_SCRIPT = str(Path(__file__).resolve().parent / "dummy" / "PalServer-Dummy.py")


@pytest.fixture(scope="session")
def running_dummy():
    """Start the dummy process before the app so the detection loop finds it."""
    env = {**os.environ, "DUMMY_PLAYER_COUNT": "0"}
    proc = subprocess.Popen(
        [sys.executable, DUMMY_SCRIPT],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )
    time.sleep(0.5)
    yield proc
    try:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)
    except Exception:
        pass


@pytest.fixture(scope="session")
def app_process(running_dummy):
    """Start the monitor app after the dummy is already running."""
    with run_monitor_app() as process:
        yield process


def test_autostop(running_dummy, app_process):
    deadline = time.time() + 60
    while time.time() < deadline:
        try:
            proc = psutil.Process(running_dummy.pid)
            if not proc.is_running():
                return
        except psutil.NoSuchProcess:
            return
        time.sleep(1)
    pytest.fail("Auto-stop did not kill the dummy PalServer within 60 s")
