import threading
from unittest.mock import MagicMock, ANY, patch
import pytest
from src.web_server import WebServer


class TestWebServer:
    """Test suite for WebServer."""

    @pytest.fixture
    def web_server(self, mock_process_manager, mock_player_manager):
        """Create a WebServer instance without running full Flask init."""
        controller = MagicMock()
        controller.process_manager = mock_process_manager
        controller.player_manager = mock_player_manager
        controller.is_palworld_process_running.return_value = False
        server = WebServer.__new__(WebServer)
        server.palworld_controller = controller
        server.state_cache = {
            "running": False,
            "playerCount": 0,
            "players": [],
            "banned_players": [],
        }
        server._lock = threading.Lock()
        return server

    def test_sync_running_state_sets_cache_from_controller(self, web_server):
        web_server.palworld_controller.is_palworld_process_running.return_value = True

        web_server._sync_running_state()

        assert web_server.state_cache["running"] is True

    def test_sync_running_state_reflects_server_stopped(self, web_server):
        web_server.state_cache["running"] = True
        web_server.palworld_controller.is_palworld_process_running.return_value = False

        web_server._sync_running_state()

        assert web_server.state_cache["running"] is False

    def test_sync_banned_players_loads_existing_bans(self, web_server):
        web_server.palworld_controller.get_banned_players.return_value = [
            "SteamID1",
            "SteamID2",
        ]

        web_server._sync_banned_players()

        assert web_server.state_cache["banned_players"] == ["SteamID1", "SteamID2"]

    def test_server_status_event_updates_cache(self, web_server):
        web_server._on_server_status(
            {
                "running": True,
                "playerCount": 2,
                "players": ["P1", "P2"],
                "banned_players": ["SteamID1"],
            }
        )
        assert web_server.state_cache["running"] is True
        assert web_server.state_cache["playerCount"] == 2
        assert web_server.state_cache["players"] == ["P1", "P2"]
        assert web_server.state_cache["banned_players"] == ["SteamID1"]

    def test_init_subscribes_to_server_status(
        self, mock_process_manager, mock_player_manager
    ):
        from src.events import Event

        controller = MagicMock()
        controller.process_manager = mock_process_manager
        controller.player_manager = mock_player_manager
        controller.is_palworld_process_running.return_value = False
        controller.get_banned_players.return_value = []

        with patch("src.events.bus.subscribe") as mock_subscribe:
            WebServer(controller)

        mock_subscribe.assert_any_call(Event.SERVER_STATUS, ANY)
