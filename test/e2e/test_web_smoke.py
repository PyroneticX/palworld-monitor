"""End-to-end smoke tests for the Palworld Monitor web UI.

These tests start the full application and exercise it through a real browser.
They are marked with `e2e` and excluded from the normal unit-test run by default.
Run them with: uv run poe smoke
"""

import os
import subprocess
import sys
import time
from pathlib import Path

import psutil

import pytest
import requests
from playwright.sync_api import sync_playwright, expect, Page

from src.settings import settings

TEST_SETTINGS = Path(__file__).resolve().parent / "settings.yaml"
settings.readSettings(TEST_SETTINGS)

pytestmark = pytest.mark.e2e

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


def _kill_tree(pid):
    """Kill a process and its entire child tree."""
    try:
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(pid)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


def _free_port(port, timeout=10):
    """Kill anything listening on `port` and wait for it to free up.

    Leftover monitor apps from an interrupted/aborted previous run hold the
    web port, which makes the new app fail to bind while the /login probe hits
    the stale instance. Cleaning them up guarantees a known-good slate.
    """
    for pid in _pids_listening_on_port(port):
        _kill_tree(pid)
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not _pids_listening_on_port(port):
            return True
        time.sleep(0.25)
    return False


def _kill_existing_palworld():
    """Terminate any running Palworld server processes."""
    subprocess.run(
        ["taskkill", "/F", "/IM", "PalServer-Win64-Shipping.exe"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        ["taskkill", "/F", "/IM", "PalServer-Win64-Shipping-Cmd.exe"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(1)


def _remove_stale_pid_files():
    """Remove leftover PID files so the fresh app doesn't adopt a stale PID.

    A stale pid file can point at any live PID reassigned to an unrelated process;
    the app's is_process_running() only checks liveness, not identity, so it would
    falsely report the server as running and hide the Start button.
    """
    project_root = Path(__file__).resolve().parents[2]
    for name in ("palworld_server.win.pid", "palworld_server.linux.pid"):
        try:
            (project_root / name).unlink()
        except FileNotFoundError:
            pass


def _server_is_on(page: Page) -> bool:
    return page.locator(".status-on").is_visible()


def _server_is_off(page: Page) -> bool:
    return page.locator(".status-off").is_visible()


def _refresh_status(page: Page):
    """Click the Update Server Status button and wait for the UI to update."""
    page.click("#getStatusBtn")
    page.wait_for_timeout(1500)


def _wait_for_status(page: Page, on: bool, timeout: float = 180.0):
    """Poll the dashboard until the server status matches `on`."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        _refresh_status(page)
        if on and _server_is_on(page):
            return
        if not on and _server_is_off(page):
            return
        time.sleep(2.0)
    raise TimeoutError(f"Server did not reach status {'ON' if on else 'OFF'} in {timeout}s")


@pytest.fixture(scope="session")
def app_process():
    """Start the monitor app and tear it down after the test session."""
    web_port = settings.webServerPort
    if not _free_port(web_port):
        raise RuntimeError(f"Could not free web port {web_port} for the test app")
    _kill_existing_palworld()
    _remove_stale_pid_files()

    project_root = Path(__file__).resolve().parents[2]
    env = dict(os.environ)
    env["PALWORLD_MONITOR_SETTINGS"] = str(TEST_SETTINGS)
    # Redirect to DEVNULL: capturing to a closed/never-read PIPE can deadlock
    # the app once the OS pipe buffer fills.
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
        _kill_tree(process.pid)
        raise RuntimeError(f"App did not start in time: {last_error}")

    yield process

    _kill_tree(process.pid)
    _kill_existing_palworld()
    _remove_stale_pid_files()
    _free_port(web_port, timeout=5)


@pytest.fixture
def page():
    """Launch a browser page for the e2e test."""
    with sync_playwright() as p:
        headless = os.environ.get("SMOKE_HEADLESS", "1") != "0"
        browser = p.chromium.launch(headless=headless, slow_mo=150 if not headless else 0)
        context = browser.new_context()
        pg = context.new_page()
        # In headless Chromium, native confirm() in onclick handlers blocks
        # even when window.confirm is overridden, and page.on("dialog")
        # accept() doesn't propagate the return value back to JS. Patch
        # script.js to bypass the confirm guard.
        def _bypass_confirm(route):
            body = route.fetch().body().decode()
            body = body.replace(
                "if (confirm('Are you sure you want to stop the server?'))",
                "if (true)",
            )
            route.fulfill(body=body, content_type="application/javascript")

        pg.route("**/script.js", _bypass_confirm)
        pg.on("dialog", lambda dialog: dialog.accept())
        yield pg
        context.close()
        browser.close()


@pytest.fixture
def logged_in_page(page: Page, app_process):
    """Open the login page, sign in, and return the dashboard page."""
    page.goto(f"{BASE_URL}/login")
    expect(page.locator("text=Admin Login")).to_be_visible()

    page.fill("input[name='username']", settings.webUsername)
    page.fill("input[name='password']", settings.webPassword)
    page.click("button[type='submit']")

    expect(page.locator("text=Server Status:")).to_be_visible()
    expect(page.locator("text=Players:")).to_be_visible()
    return page


def test_login_and_dashboard_loads(logged_in_page):
    """Smoke test: sign in and verify the dashboard renders."""
    logged_in_page.wait_for_timeout(3500)
    players_info = logged_in_page.locator("#playersInfo")
    expect(players_info).to_be_visible()

    text = players_info.inner_text()
    assert "Player" in text or "No players found" in text


def test_server_lifecycle(logged_in_page):
    """Start the Palworld server, read status, then stop it through the web UI."""
    _kill_existing_palworld()

    # Make sure the UI shows the server as OFF first.
    _refresh_status(logged_in_page)
    if _server_is_on(logged_in_page):
        logged_in_page.click("#offBtn")
        _wait_for_status(logged_in_page, on=False)

    # Start the server.
    logged_in_page.click("#onBtn")
    _wait_for_status(logged_in_page, on=True, timeout=40.0)

    # Read status and player info via the REST-backed dashboard.
    time.sleep(10)
    _refresh_status(logged_in_page)
    players_info = logged_in_page.locator("#playersInfo")
    expect(players_info).to_be_visible()

    # Stop the server.
    logged_in_page.click("#offBtn")
    _wait_for_status(logged_in_page, on=False, timeout=60.0)
