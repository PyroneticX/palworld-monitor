"""
Tests for the PalWorldController module.
"""

import pytest
from unittest.mock import patch, MagicMock
from src.palworld_control import PalWorldController
from test.support import create_mock_api_client
from src.events import bus, Event
import time

class TestPalWorldController:
    """Test suite for PalWorldController."""

    @pytest.fixture
    def mock_client(self):
        return create_mock_api_client()

    def test_init(
        self,
        mock_settings,
        mock_client,
        mock_process_manager,
        mock_player_manager,
        mock_banlist_manager,
    ):
        controller = PalWorldController(
            client=mock_client,
            process_manager=mock_process_manager,
            player_manager=mock_player_manager,
            banlist_manager=mock_banlist_manager,
        )

        assert controller.is_palworld_process_running() is False
        info = controller.current_server_info
        assert info["running"] is False
        assert info["playerCount"] == 0

    def test_is_palworld_process_running(
        self, mock_settings, mock_client, mock_process_manager
    ):
        mock_process_manager.is_process_running.return_value = True
        controller = PalWorldController(client=mock_client, process_manager=mock_process_manager)
        assert controller.is_palworld_process_running() is True

    @patch("src.events.bus.publish")
    def test_start_server_success(self, mock_publish, mock_settings, mock_client, mock_process_manager):
        mock_process_manager.is_process_running.return_value = False
        with patch("os.path.exists", return_value=False), patch("time.time", return_value=1000):
            controller = PalWorldController(client=mock_client, process_manager=mock_process_manager)
            controller.last_server_started_time = 0
            result = controller.start_server()
            assert result is True
            mock_publish.assert_any_call(Event.CMD_START_SERVER, {
                'exe_path': mock_settings.palworldServerExePath,
                'exe_args': mock_settings.palworldExeArguments
            })

    def test_start_server_already_running(self, mock_settings, mock_client, mock_process_manager):
        mock_process_manager.is_process_running.return_value = True
        with patch("os.path.exists", return_value=False), patch("time.time", return_value=1000):
            controller = PalWorldController(client=mock_client, process_manager=mock_process_manager)
            result = controller.start_server()
            assert result is False

    @patch("src.events.bus.publish")
    def test_stop_server_success(self, mock_publish, mock_settings, mock_client, mock_process_manager):
        mock_process_manager.is_process_running.return_value = True
        with patch("os.path.exists", return_value=False), patch("time.time", return_value=1000), patch("threading.Thread"):
            controller = PalWorldController(client=mock_client, process_manager=mock_process_manager)
            controller.last_server_stopped_time = 0
            result = controller.stop_server()
            assert result is True
            mock_publish.assert_any_call(Event.CMD_STOP_SERVER, {})

    def test_stop_server_not_running(self, mock_settings, mock_client, mock_process_manager):
        mock_process_manager.is_process_running.return_value = False
        with patch("os.path.exists", return_value=False), patch("threading.Thread"):
            controller = PalWorldController(client=mock_client, process_manager=mock_process_manager)
            controller.stop_server()
            assert controller.current_server_info["running"] is False

    def test_get_current_server_info(self, mock_settings, mock_client, mock_process_manager):
        controller = PalWorldController(client=mock_client, process_manager=mock_process_manager)
        controller.current_server_info = {"running": True, "playerCount": 2, "players": [["P1"], ["P2"]]}
        assert controller.current_server_info["running"] is True

    def test_update_current_server_info(self, mock_settings, mock_client, mock_process_manager, mock_player_manager):
        mock_client.get_player_names.return_value = [["P1", "p1", "u1", "10"], ["P2", "p2", "u2", "15"]]
        mock_process_manager.is_process_running.return_value = True
        controller = PalWorldController(client=mock_client, process_manager=mock_process_manager, player_manager=mock_player_manager)
        info = controller.update_current_server_info()
        assert info["running"] is True
        assert info["playerCount"] == 2

    def test_update_current_server_info_server_not_running(self, mock_settings, mock_client, mock_process_manager):
        mock_process_manager.is_process_running.return_value = False
        controller = PalWorldController(client=mock_client, process_manager=mock_process_manager)
        info = controller.update_current_server_info()
        assert info["running"] is False

    @patch("src.events.bus.publish")
    def test_kick_player(self, mock_publish, mock_settings, mock_client, mock_process_manager, mock_player_manager):
        controller = PalWorldController(client=mock_client, process_manager=mock_process_manager, player_manager=mock_player_manager)
        result = controller.kick_player("123")
        assert result is True
        mock_publish.assert_any_call(Event.CMD_KICK_PLAYER, {"steam_id": "123"})

    @patch("src.events.bus.publish")
    def test_ban_player(self, mock_publish, mock_settings, mock_client, mock_process_manager, mock_player_manager, mock_banlist_manager):
        controller = PalWorldController(client=mock_client, process_manager=mock_process_manager, player_manager=mock_player_manager, banlist_manager=mock_banlist_manager)
        result = controller.ban_player("123")
        assert result is True
        mock_publish.assert_any_call(Event.CMD_BAN_PLAYER, {"steam_id": "123"})

    @patch("src.events.bus.publish")
    def test_unban_player(self, mock_publish, mock_settings, mock_client, mock_process_manager, mock_player_manager, mock_banlist_manager):
        controller = PalWorldController(client=mock_client, process_manager=mock_process_manager, player_manager=mock_player_manager, banlist_manager=mock_banlist_manager)
        result = controller.unban_player("123")
        assert result is True
        mock_publish.assert_any_call(Event.CMD_UNBAN_PLAYER, {"steam_id": "123"})

    def test_get_server_status_is_running(self, mock_settings, mock_client, mock_process_manager):
        mock_process_manager.is_process_running.return_value = True
        controller = PalWorldController(client=mock_client, process_manager=mock_process_manager)
        assert controller.is_palworld_process_running() is True

    def test_stop_server_command_emitted(self, mock_settings, mock_client, mock_process_manager):
        mock_process_manager.is_process_running.return_value = True
        controller = PalWorldController(client=mock_client, process_manager=mock_process_manager)
        controller.last_server_stopped_time = 0
        with patch("src.events.bus.publish") as mock_publish:
            result = controller.stop_server()
            assert result is True
            mock_publish.assert_any_call(Event.CMD_STOP_SERVER, {})

    def test_server_info_attribute_access(self, mock_settings, mock_client, mock_process_manager):
        controller = PalWorldController(client=mock_client, process_manager=mock_process_manager)
        assert "running" in controller.current_server_info
        assert "playerCount" in controller.current_server_info
        assert "players" in controller.current_server_info
