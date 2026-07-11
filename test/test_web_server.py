"""
Extended tests for WebServer route handlers and event integration.
"""

from unittest.mock import MagicMock
from src.web_server import WebServer

class TestWebServerEventHandlers:
    """Test suite for event handler methods."""

    def test_on_server_started_updates_cache(self, mock_settings):
        """Test that SERVER_STARTED event updates running state."""
        server = WebServer.__new__(WebServer)
        server.palworld_controller = MagicMock()
        server.state_cache = {
            "running": False,
            "playerCount": 0,
            "players": [],
            "banned_players": [],
        }
        server._lock = MagicMock()

        server._on_server_started({"pid": 12345})
        assert server.state_cache["running"] is True

    def test_on_server_stopped_clears_players(self, mock_settings):
        """Test that SERVER_STOPPED event clears player list."""
        server = WebServer.__new__(WebServer)
        server.palworld_controller = MagicMock()
        server.state_cache = {
            "running": True,
            "playerCount": 2,
            "players": [["P1", "p1", "u1", "10"], ["P2", "p2", "u2", "15"]],
            "banned_players": [],
        }
        server._lock = MagicMock()

        server._on_server_stopped({"pid": 12345})
        assert server.state_cache["running"] is False
        assert server.state_cache["players"] == []
        assert server.state_cache["playerCount"] == 0

    def test_on_server_status_updates_all_fields(self, mock_settings):
        """Test that SERVER_STATUS event updates all cached fields."""
        server = WebServer.__new__(WebServer)
        server.palworld_controller = MagicMock()
        server.state_cache = {
            "running": False,
            "playerCount": 0,
            "players": [],
            "banned_players": [],
        }
        server._lock = MagicMock()
        server._sse_lock = MagicMock()
        server._sse_clients = []

        server._on_server_status(
            {
                "running": True,
                "playerCount": 3,
                "players": [["P1", "p1", "u1", "10"], ["P2", "p2", "u2", "15"], ["P3", "p3", "u3", "20"]],
                "banned_players": ["SteamID1"],
            }
        )

        assert server.state_cache["running"] is True
        assert server.state_cache["playerCount"] == 3
        assert len(server.state_cache["players"]) == 3
        assert "SteamID1" in server.state_cache["banned_players"]

    def test_sync_running_state_sets_cache_from_controller(self, mock_settings):
        """Test that _sync_running_state updates cache from controller."""
        server = WebServer.__new__(WebServer)
        server.palworld_controller = MagicMock()
        server.palworld_controller.is_palworld_process_running.return_value = True
        server.state_cache = {
            "running": False,
            "playerCount": 0,
            "players": [],
            "banned_players": [],
        }
        server._lock = MagicMock()

        server._sync_running_state()
        assert server.state_cache["running"] is True

    def test_sync_banned_players_loads_existing_bans(self, mock_settings):
        """Test that _sync_banned_players loads existing bans."""
        server = WebServer.__new__(WebServer)
        server.palworld_controller = MagicMock()
        server.palworld_controller.get_banned_players.return_value = ["SteamID1", "SteamID2"]
        server.state_cache = {
            "running": False,
            "playerCount": 0,
            "players": [],
            "banned_players": [],
        }
        server._lock = MagicMock()

        server._sync_banned_players()
        assert server.state_cache["banned_players"] == ["SteamID1", "SteamID2"]


