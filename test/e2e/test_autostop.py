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
import requests

from src.settings import settings
from .helpers import (
    TEST_SETTINGS,
    free_port,
    kill_existing_palworld,
    kill_tree,
    remove_stale_pid_files,
)

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
    web_port = settings.webServerPort
    base_url = f"http://localhost:{web_port}"
    if not free_port(web_port):
        raise RuntimeError(f"Could not free web port {web_port} for the test app")
    kill_existing_palworld()
    remove_stale_pid_files()

    project_root = Path(__file__).resolve().parents[2]
    env = dict(os.environ)
    env["PALWORLD_MONITOR_SETTINGS"] = str(TEST_SETTINGS)
    process = subprocess.Popen(
        [sys.executable, "-m", "src.main"],
        cwd=project_root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )

    deadline = time.time() + 30
    last_error = None
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"App process exited early with code {process.returncode}")
        try:
            resp = requests.get(f"{base_url}/login", timeout=1)
            if resp.status_code == 200:
                break
        except Exception as exc:
            last_error = exc
        time.sleep(0.5)
    else:
        kill_tree(process.pid)
        raise RuntimeError(f"App did not start in time: {last_error}")

    yield process

    kill_tree(process.pid)
    kill_existing_palworld()
    remove_stale_pid_files()
    free_port(web_port, timeout=5)


def test_autostop(running_dummy, app_process):
    deadline = time.time() + 45
    while time.time() < deadline:
        try:
            proc = psutil.Process(running_dummy.pid)
            if not proc.is_running():
                return
        except psutil.NoSuchProcess:
            return
        time.sleep(1)
    pytest.fail("Auto‑stop did not kill the dummy PalServer within 45 s")
