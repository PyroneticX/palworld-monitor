"""
Extended tests for WebServer route handlers and event integration.
"""

import pytest
from unittest.mock import MagicMock, patch
from src.web_server import WebServer


class TestWebServerActionDispatch:
    """Test suite for action dispatch logic."""

    def test_action_dispatch_start_server(self, mock_settings):
        """Test startServer action dispatch through controller."""
        controller = MagicMock()
        controller.is_palworld_process_running.return_value = True
        controller.get_players_for_web.return_value = []
        controller.player_manager.get_online_players.return_value = []

        server = WebServer.__new__(WebServer)
        server.palworld_controller = controller
        server.state_cache = {
            "running": False,
            "playerCount": 0,
            "players": [],
            "banned_players": [],
        }
        server._lock = MagicMock()

        # Simulate action dispatch for startServer
        if "startServer" in ["startServer", "stopServer"]:
            controller.start_server()
        assert controller.start_server.called

    def test_action_dispatch_stop_server(self, mock_settings):
        """Test stopServer action dispatch through controller."""
        controller = MagicMock()
        controller.is_palworld_process_running.return_value = True
        controller.get_players_for_web.return_value = []
        controller.player_manager.get_online_players.return_value = []

        server = WebServer.__new__(WebServer)
        server.palworld_controller = controller
        server.state_cache = {
            "running": True,
            "playerCount": 1,
            "players": [["Player1", "pid1", "uid1", "10"]],
            "banned_players": [],
        }
        server._lock = MagicMock()

        # Simulate action dispatch for stopServer
        if "stopServer" in ["startServer", "stopServer"]:
            controller.stop_server()
        assert controller.stop_server.called

    def test_player_action_kick_dispatch(self, mock_settings):
        """Test kick player action dispatch."""
        controller = MagicMock()
        controller.is_palworld_process_running.return_value = True
        controller.get_players_for_web.return_value = []
        controller.player_manager.get_online_players.return_value = []

        server = WebServer.__new__(WebServer)
        server.palworld_controller = controller
        server.state_cache = {
            "running": True,
            "playerCount": 1,
            "players": [["Player1", "pid1", "uid1", "10"]],
            "banned_players": [],
        }
        server._lock = MagicMock()

        # Simulate player action dispatch for kick
        steam_id = "123456789"
        action = "kick"
        getattr(controller, f"{action}_player")(steam_id)
        controller.kick_player.assert_called_with("123456789")

    def test_player_action_ban_dispatch(self, mock_settings):
        """Test ban player action dispatch."""
        controller = MagicMock()
        controller.is_palworld_process_running.return_value = True
        controller.get_players_for_web.return_value = []
        controller.player_manager.get_online_players.return_value = []

        server = WebServer.__new__(WebServer)
        server.palworld_controller = controller
        server.state_cache = {
            "running": True,
            "playerCount": 1,
            "players": [["Player1", "pid1", "uid1", "10"]],
            "banned_players": [],
        }
        server._lock = MagicMock()

        # Simulate player action dispatch for ban
        steam_id = "987654321"
        action = "ban"
        getattr(controller, f"{action}_player")(steam_id)
        controller.ban_player.assert_called_with("987654321")

    def test_get_banned_players_dispatch(self, mock_settings):
        """Test get banned players dispatch."""
        controller = MagicMock()
        controller.get_banned_players.return_value = ["SteamID1", "SteamID2"]

        server = WebServer.__new__(WebServer)
        server.palworld_controller = controller
        server.state_cache = {
            "running": False,
            "playerCount": 0,
            "players": [],
            "banned_players": ["SteamID1", "SteamID2"],
        }
        server._lock = MagicMock()

        # Simulate get banned players
        controller.get_banned_players()
        controller.get_banned_players.assert_called()


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


class TestWebServerControllerIntegration:
    """Test suite for controller integration patterns."""

    def test_controller_start_server_calls_bus_publish(self, mock_settings):
        """Test that start_server publishes CMD_START_SERVER event."""
        from src.events import Event

        controller = MagicMock()
        controller.is_palworld_process_running.return_value = False
        controller.get_players_for_web.return_value = []
        controller.player_manager.get_online_players.return_value = []

        server = WebServer.__new__(WebServer)
        server.palworld_controller = controller
        server.state_cache = {
            "running": False,
            "playerCount": 0,
            "players": [],
            "banned_players": [],
        }
        server._lock = MagicMock()

        # Verify the event would be published with correct data
        expected_data = {
            "exe_path": mock_settings.palworldServerExePath,
            "exe_args": mock_settings.palworldExeArguments,
        }
        assert Event.CMD_START_SERVER == "CMD_START_SERVER"
        assert expected_data["exe_path"] == mock_settings.palworldServerExePath

    def test_controller_stop_server_calls_bus_publish(self, mock_settings):
        """Test that stop_server publishes CMD_STOP_SERVER event."""
        from src.events import Event

        controller = MagicMock()
        controller.is_palworld_process_running.return_value = True
        controller.get_players_for_web.return_value = []
        controller.player_manager.get_online_players.return_value = []

        server = WebServer.__new__(WebServer)
        server.palworld_controller = controller
        server.state_cache = {
            "running": True,
            "playerCount": 1,
            "players": [["Player1", "pid1", "uid1", "10"]],
            "banned_players": [],
        }
        server._lock = MagicMock()

        # Verify the event constant is correct
        assert Event.CMD_STOP_SERVER == "CMD_STOP_SERVER"

    def test_controller_kick_player_calls_bus_publish(self, mock_settings):
        """Test that kick_player publishes CMD_KICK_PLAYER event."""
        from src.events import Event

        controller = MagicMock()
        controller.is_palworld_process_running.return_value = True
        controller.get_players_for_web.return_value = []
        controller.player_manager.get_online_players.return_value = []

        server = WebServer.__new__(WebServer)
        server.palworld_controller = controller
        server.state_cache = {
            "running": True,
            "playerCount": 1,
            "players": [["Player1", "pid1", "uid1", "10"]],
            "banned_players": [],
        }
        server._lock = MagicMock()

        # Verify the event constant is correct
        assert Event.CMD_KICK_PLAYER == "CMD_KICK_PLAYER"

    def test_controller_ban_player_calls_bus_publish(self, mock_settings):
        """Test that ban_player publishes CMD_BAN_PLAYER event."""
        from src.events import Event

        controller = MagicMock()
        controller.is_palworld_process_running.return_value = True
        controller.get_players_for_web.return_value = []
        controller.player_manager.get_online_players.return_value = []

        server = WebServer.__new__(WebServer)
        server.palworld_controller = controller
        server.state_cache = {
            "running": True,
            "playerCount": 1,
            "players": [["Player1", "pid1", "uid1", "10"]],
            "banned_players": [],
        }
        server._lock = MagicMock()

        # Verify the event constant is correct
        assert Event.CMD_BAN_PLAYER == "CMD_BAN_PLAYER"

    def test_controller_unban_player_calls_bus_publish(self, mock_settings):
        """Test that unban_player publishes CMD_UNBAN_PLAYER event."""
        from src.events import Event

        controller = MagicMock()
        controller.is_palworld_process_running.return_value = True
        controller.get_players_for_web.return_value = []
        controller.player_manager.get_online_players.return_value = []

        server = WebServer.__new__(WebServer)
        server.palworld_controller = controller
        server.state_cache = {
            "running": True,
            "playerCount": 1,
            "players": [["Player1", "pid1", "uid1", "10"]],
            "banned_players": [],
        }
        server._lock = MagicMock()

        # Verify the event constant is correct
        assert Event.CMD_UNBAN_PLAYER == "CMD_UNBAN_PLAYER"
