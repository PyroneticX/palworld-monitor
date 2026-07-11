"""Shared fixtures for e2e smoke tests."""

import os
import subprocess
import sys
import time

import pytest
import requests

from .helpers import (
    BASE_URL,
    TEST_SETTINGS,
    _pids_listening_on_port,
    free_port,
    kill_existing_palworld,
    kill_tree,
    remove_stale_pid_files,
)
from src.settings import settings


@pytest.fixture(scope="session")
def app_process():
    """Start the monitor app and tear it down after the test session."""
    web_port = settings.webServerPort
    if not free_port(web_port):
        raise RuntimeError(f"Could not free web port {web_port} for the test app")
    kill_existing_palworld()
    remove_stale_pid_files()

    project_root = os.path.join(os.path.dirname(__file__), "..", "..")
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
            response = requests.get(f"{BASE_URL}/login", timeout=1)
            if response.status_code == 200:
                break
        except requests.RequestException as exc:
            last_error = exc
        time.sleep(0.5)
    else:
        kill_tree(process.pid)
        raise RuntimeError(f"App did not start in time: {last_error}")

    yield process

    kill_tree(process.pid)
    try:
        process.wait(timeout=5)
    except Exception:
        pass
    kill_existing_palworld()
    remove_stale_pid_files()
    free_port(web_port, timeout=5)
    # Also free the dummy PalServer REST port in case the app didn't
    # cleanly shut down the dummy subprocess.
    for pid in _pids_listening_on_port(settings.palworldRESTPort):
        kill_tree(pid)
