"""End-to-end smoke tests for the Palworld Monitor web UI.

These tests start the full application and exercise it through a real browser.
They are marked with `e2e` and excluded from the normal unit-test run by default.
Run them with: uv run poe smoke
"""

import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests
from playwright.sync_api import sync_playwright, expect

from src.settings import settings

settings.readSettings(Path(__file__).resolve().parents[2] / "src" / "settings.yaml")

pytestmark = pytest.mark.e2e

BASE_URL = "http://localhost:8213"


@pytest.fixture(scope="session")
def app_process():
    """Start the monitor app and tear it down after the test session."""
    project_root = Path(__file__).resolve().parents[2]
    process = subprocess.Popen(
        [sys.executable, "-m", "src.main"],
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    # Wait for the web server to become ready
    deadline = time.time() + 30
    last_error = None
    while time.time() < deadline:
        try:
            response = requests.get(f"{BASE_URL}/login", timeout=1)
            if response.status_code == 200:
                break
        except requests.RequestException as exc:
            last_error = exc
        time.sleep(0.5)
    else:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        raise RuntimeError(f"App did not start in time: {last_error}")

    yield process

    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


@pytest.fixture
def page():
    """Launch a browser page for the e2e test."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        pg = context.new_page()
        yield pg
        context.close()
        browser.close()


@pytest.fixture
def logged_in_page(page, app_process):
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
    logged_in_page.wait_for_timeout(3500)  # let JS refresh player status
    players_info = logged_in_page.locator("#playersInfo")
    expect(players_info).to_be_visible()

    text = players_info.inner_text()
    assert "Player" in text or "No players found" in text
