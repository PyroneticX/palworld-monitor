"""
Pytest configuration and shared fixtures for the entire test suite.
"""

import sys
import os
import pytest
import tempfile
import shutil

# Add project root and src directory to path (once, at module level)
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
    pid_files = ["palworld_server.win.pid", "palworld_server.linux.pid"]
    for pid_file in pid_files:
        if os.path.exists(pid_file):
            try:
                os.remove(pid_file)
            except Exception:
                pass


@pytest.fixture
def mock_settings():
    """Shared settings fixture with all required attributes."""
    from unittest.mock import MagicMock

    mock = MagicMock()
    mock.palworldServerHost = "localhost"
    mock.palworldServerPort = 8211
    mock.palworldRESTPort = 8212
    mock.palworldRCONPort = 25575
    mock.palworldServerAdminPassword = "test_admin_password"
    mock.palworldServerExePath = "/path/to/PalServer.exe"
    mock.palworldMainProcessName = "PalServer-Win64-Shipping-Cmd.exe"
    mock.palworldExeArguments = "-test-args"
    mock.useWebServer = True
    mock.webServerPort = 8213
    mock.webUsername = "test_admin"
    mock.webPassword = "test_web_password"
    mock.sessionSecretKey = (
        "test_secret_key_123456789012345678901234567890"
    )
    mock.sessionTimeout = 3600
    mock.maxLoginAttempts = 5
    mock.lockoutDuration = 300
    mock.rateLimitEnabled = True
    mock.rateLimitRequests = 100
    mock.rateLimitWindow = 60
    mock.autoStart = True
    mock.autoStop = True
    mock.autoStopDelay = 120
    mock.updateInterval = 30
    mock.enablePlayerTracking = True
    mock.protocol = "REST"
    mock.controlServerThroughWeb = True
    mock.showServerIPAddress = False
    mock.firstPacketPattern = b"\x09\x08\x00"

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
