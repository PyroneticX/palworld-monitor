"""Shared helpers and constants for e2e smoke tests."""

import subprocess
import time
from pathlib import Path

import psutil

from src.settings import settings

TEST_SETTINGS = Path(__file__).resolve().parent / "settings.yaml"
settings.readSettings(TEST_SETTINGS)

BASE_URL = "http://localhost:8213"


def _pids_listening_on_port(port):
    """Return PIDs of processes listening on the given TCP port."""
    pids = set()
    try:
        for conn in psutil.net_connections(kind="tcp"):
            if conn.status == psutil.CONN_LISTEN and conn.laddr.port == port:
                if conn.pid:
                    pids.add(conn.pid)
    except (psutil.AccessDenied, Exception):
        pass
    return pids


def kill_tree(pid):
    """Kill a process and its entire child tree."""
    try:
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(pid)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=15,
        )
    except Exception:
        pass


def free_port(port, timeout=10):
    """Kill anything listening on `port` and wait for it to free up."""
    for pid in _pids_listening_on_port(port):
        kill_tree(pid)
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not _pids_listening_on_port(port):
            return True
        time.sleep(0.25)
    return False


def kill_existing_palworld():
    """Terminate any running Palworld server processes."""
    subprocess.run(
        ["taskkill", "/F", "/IM", "PalServer-Win64-Shipping.exe"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=15,
    )
    subprocess.run(
        ["taskkill", "/F", "/IM", "PalServer-Win64-Shipping-Cmd.exe"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=15,
    )
    time.sleep(1)


def remove_stale_pid_files():
    """Remove leftover PID files so the fresh app doesn't adopt a stale PID."""
    project_root = Path(__file__).resolve().parents[2]
    for name in ("palworld_server.win.pid", "palworld_server.linux.pid"):
        try:
            (project_root / name).unlink()
        except FileNotFoundError:
            pass


def is_palworld_running():
    """Check if any Palworld server process is running."""
    for proc in psutil.process_iter(["name", "cmdline"]):
        try:
            name = (proc.info["name"] or "").lower()
            cmdline = proc.info["cmdline"] or []
            if "palserver" in name:
                return True
            if any("palserver" in (arg or "").lower() for arg in cmdline):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False
