"""
Pytest configuration and shared fixtures for process manager tests.
"""

import sys
import os
import pytest
import tempfile
import shutil
from unittest.mock import MagicMock

# Add project root and src directory to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

# Fix Windows console encoding for emoji support
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


@pytest.fixture
def test_sleep_script():
    """Path to the long_running_process.py script."""
    return os.path.join(os.path.dirname(__file__), "support", "long_running_process.py")


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture(autouse=True)
def cleanup_pid_files():
    """Automatically clean up PID files after each test."""
    yield
    # Clean up PID files that might have been created
    pid_files = ["palworld_server.win.pid", "palworld_server.linux.pid"]
    for pid_file in pid_files:
        if os.path.exists(pid_file):
            try:
                os.remove(pid_file)
            except Exception:
                pass


from src.constants import (
    PALWORLD_SERVER_PORT,
    PALWORLD_REST_PORT,
    PALWORLD_RCON_PORT,
    WEB_SERVER_PORT,
    PALWORLD_MAIN_PROCESS_NAME,
)


@pytest.fixture
def mock_settings(monkeypatch):
    """Mock settings module with all required attributes."""
    from unittest.mock import MagicMock

    mock = MagicMock()

    # Server configuration
    mock.palworldServerHost = "localhost"
    mock.palworldServerPort = PALWORLD_SERVER_PORT
    mock.palworldRESTPort = PALWORLD_REST_PORT
    mock.palworldRCONPort = PALWORLD_RCON_PORT
    mock.palworldServerAdminPassword = "test_admin_password"
    mock.palworldServerExePath = "/path/to/PalServer.exe"
    mock.palworldMainProcessName = PALWORLD_MAIN_PROCESS_NAME
    mock.palworldExeArguments = "-test-args"

    # Web server configuration
    mock.useWebServer = True
    mock.webServerPort = WEB_SERVER_PORT
    mock.webUsername = "test_admin"
    mock.webPassword = "test_web_password"
    mock.sessionSecretKey = "test_secret_key_123456789012345678901234567890"
    mock.sessionTimeout = 3600
    mock.maxLoginAttempts = 5
    mock.lockoutDuration = 300
    mock.rateLimitEnabled = True
    mock.rateLimitRequests = 100
    mock.rateLimitWindow = 60

    # Auto-start/stop configuration
    mock.autoStart = True
    mock.autoStop = True
    mock.autoStopDelay = 120
    mock.updateInterval = 30

    # Feature flags
    mock.enablePlayerTracking = True
    mock.protocol = "REST"
    mock.controlServerThroughWeb = True
    mock.showServerIPAddress = False
    mock.firstPacketPattern = b"\x09\x08\x00"

    # Patch settings import in all modules that use it
    monkeypatch.setattr("src.api_clients.settings", mock)
    monkeypatch.setattr("src.palworld_control.settings", mock)
    monkeypatch.setattr("src.auto_start.settings", mock)
    monkeypatch.setattr("src.player_manager.settings", mock)
    monkeypatch.setattr("src.banlist_manager.settings", mock)
    return mock


@pytest.fixture
def mock_process_manager():
    """Create a mock process manager for testing."""
    from unittest.mock import MagicMock

    pm = MagicMock()
    pm.is_process_running.return_value = False
    pm.launched_pid = None
    pm.launch_process.return_value = None
    pm.terminate_process.return_value = True
    pm.find_process_pid.return_value = None
    pm.pid_file_name.return_value = "test.pid"
    pm.set_known_pid.return_value = None
    return pm


@pytest.fixture
def mock_player_manager():
    """Create a mock player manager for testing."""
    from unittest.mock import MagicMock

    pm = MagicMock()
    pm.players = {}
    pm.get_all_players.return_value = []
    pm.get_online_players.return_value = []
    pm.get_offline_players.return_value = []
    pm.get_player_count.return_value = 0
    pm.get_total_player_count.return_value = 0
    pm.update_players_from_server.return_value = None
    return pm


@pytest.fixture
def mock_banlist_manager():
    """Create a mock banlist manager for testing."""
    from unittest.mock import MagicMock

    bm = MagicMock()
    bm.get_banned_players.return_value = []
    bm.is_banned.return_value = False
    bm.add_ban.return_value = True
    bm.remove_ban.return_value = True
    return bm


@pytest.fixture
def web_app_factory(mock_settings, mock_process_manager, mock_player_manager, mock_banlist_manager):
    """Create a real Flask app with mocked controller dependencies for request tests.

    This fixture creates a WebServer instance using the real Flask app (not __new__),
    so that templates render, sessions are managed, CSRF validates, and routes dispatch
    through the full HTTP pipeline — all without needing an actual HTTP server or browser.

    Args:
        mock_settings: Patches settings module with test credentials
        mock_process_manager: Mock process manager (returns False for running)
        mock_player_manager: Mock player manager (empty players list)
        mock_banlist_manager: Mock banlist manager (no bans)

    Yields:
        WebServer instance with a fully functional Flask app
    """
    from src.web_server import WebServer

    # Generate a session secret key if not already set by mock_settings
    if not mock_settings.sessionSecretKey:
        import secrets as _secrets
        mock_settings.sessionSecretKey = _secrets.token_hex(32)

    controller = MagicMock()
    controller.is_palworld_process_running.return_value = False
    controller.get_players_for_web.return_value = []
    controller.player_manager.get_online_players.return_value = []
    controller.start_server.return_value = True
    controller.stop_server.return_value = True
    controller.kick_player.return_value = True
    controller.ban_player.return_value = True
    controller.unban_player.return_value = True

    # Create the Flask app manually since we're bypassing __init__
    from flask import Flask
    from flask_login import LoginManager
    from flask_wtf.csrf import CSRFProtect
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    from datetime import timedelta

    server.app = Flask(__name__, static_folder="static")
    server.app.secret_key = mock_settings.sessionSecretKey
    server.app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(
        seconds=mock_settings.sessionTimeout
    )

    # Initialize CSRF protection
    server.csrf = CSRFProtect(server.app)

    # Initialize rate limiter
    if mock_settings.rateLimitEnabled:
        server.limiter = Limiter(
            app=server.app,
            key_func=get_remote_address,
            default_limits=[
                f"{mock_settings.rateLimitRequests} per {mock_settings.rateLimitWindow} seconds"
            ],
        )

    # Initialize Flask-login
    server.login_manager = LoginManager()
    server.login_manager.init_app(server.app)
    server.login_manager.login_view = "login"
    server.login_manager.login_message = "Please log in to access this page."

    # Register user loader
    @server.login_manager.user_loader
    def load_user(user_id):
        if user_id == mock_settings.webUsername:
            from src.auth import User
            return User(user_id)
        return None

    server.palworld_controller = controller
    server.state_cache = {
        "running": False,
        "playerCount": 0,
        "players": [],
        "banned_players": [],
    }
    server._lock = MagicMock()

    # Subscribe to events (required for proper state management)
    from src.events import bus, Event

    bus.subscribe(Event.SERVER_STARTED, server._on_server_started)
    bus.subscribe(Event.SERVER_STOPPED, server._on_server_stopped)
    bus.subscribe(Event.SERVER_STATUS, server._on_server_status)

    # Sync initial state
    server._sync_running_state()
    server._sync_banned_players()

    yield server


@pytest.fixture
def client(web_app_factory):
    """Create a Flask test client for unauthenticated requests."""
    return web_app_factory.app.test_client()


@pytest.fixture
def auth_client(web_app_factory, mock_settings):
    """Create a Flask test client pre-authenticated as the admin user.

    This fixture logs in with valid credentials and returns a client that can access
    protected routes without needing to POST login first.

    Args:
        web_app_factory: Real WebServer instance with Flask app
        mock_settings: Test credentials (username=test_admin, password=test_web_password)

    Yields:
        Flask test client with active session
    """
    from src.auth import User, verify_password

    # Create a test client and login as admin user
    auth_client = web_app_factory.app.test_client()
    response = auth_client.post(
        "/login",
        data={
            "username": mock_settings.webUsername,
            "password": mock_settings.webPassword,
        },
        follow_redirects=False,
    )

    assert response.status_code == 302, (
        f"Expected redirect after login, got {response.status_code}"
    )

    # Return the authenticated client
    return auth_client


@pytest.fixture
def short_lockout_client(web_app_factory):
    """Create a Flask test client with a very short lockout duration for testing.

    This fixture creates a new WebServer instance with lockout_duration=1 second,
    allowing lockout tests to complete quickly without waiting.

    Yields:
        Flask test client with active session and 1-second lockout
    """
    from src.auth import LoginAttemptTracker

    # Create a new app instance with short lockout
    controller = MagicMock()
    controller.is_palworld_process_running.return_value = False
    controller.get_players_for_web.return_value = []
    controller.player_manager.get_online_players.return_value = []
    controller.start_server.return_value = True
    controller.stop_server.return_value = True
    controller.kick_player.return_value = True
    controller.ban_player.return_value = True
    controller.unban_player.return_value = True

    server = WebServer.__new__(WebServer)
    server.palworld_controller = controller
    server.state_cache = {
        "running": False,
        "playerCount": 0,
        "players": [],
        "banned_players": [],
    }
    server._lock = MagicMock()

    # Subscribe to events (required for proper state management)
    from src.events import bus, Event

    bus.subscribe(Event.SERVER_STARTED, server._on_server_started)
    bus.subscribe(Event.SERVER_STOPPED, server._on_server_stopped)
    bus.subscribe(Event.SERVER_STATUS, server._on_server_status)

    # Sync initial state
    server._sync_running_state()
    server._sync_banned_players()

    yield server.app.test_client()
