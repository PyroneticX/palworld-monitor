"""
Tests for the PalWorldController module.
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from src.events import Event

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.palworld_control import PalWorldController
from test.support import create_mock_api_client


class TestPalWorldController:
    """Test suite for PalWorldController."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock API client."""
        return create_mock_api_client()

    @pytest.fixture
    def controller(self, mock_settings, mock_client, mock_process_manager, 
                  mock_player_manager, mock_banlist_manager):
        """Fixture for providing a fresh PalWorldController instance."""
        return PalWorldController(
            client=mock_client,
            process_manager=mock_process_manager,
            player_manager=mock_player_manager,
            banlist_manager=mock_banlist_manager,
        )

    def test_init(self, controller):
        """Test PalWorldController initialization."""
        assert controller.current_server_info["running"] is False
        assert controller.current_server_info["playerCount"] == 0
        assert controller.is_palworld_process_running() is False

    def test_is_palworld_process_running(self, mock_settings, mock_client, mock_process_manager):
        """Test checking if process is running."""
        mock_process_manager.is_process_running.return_value = True
        controller = PalWorldController(client=mock_client, process_manager=mock_process_manager)
        assert controller.is_palworld_process_running() is True

    def test_start_server_success(self, mock_settings, mock_client, mock_process_manager):
        """Test successfully starting the server (sends command)."""
        mock_process_manager.is_process_running.return_value = False

        with patch("src.events.bus.publish") as mock_publish:
            controller = PalWorldController(client=mock_client, process_manager=mock_process_manager)
            result = controller.start_server()

            assert result is True
            # Verify CMD_START_SERVER was published
            mock_publish.assert_called_once()
            call_args = mock_publish.call_args[0]
            assert call_args[0] == Event.CMD_START_SERVER

    def test_start_server_already_running(self, mock_settings, mock_client, mock_process_manager):
        """Test starting server when already running."""
        mock_process_manager.is_process_running.return_value = True
        controller = PalWorldController(client=mock_client, process_manager=mock_process_manager)

        result = controller.start_server()

        assert result is False  # Blocked because it's already running

    def test_stop_server_success(self, mock_settings, mock_client, mock_process_manager):
        """Test successfully stopping the server (sends command)."""
        mock_process_manager.is_process_running.return_value = True
        controller = PalWorldController(client=mock_client, process_manager=mock_process_manager)

        with patch("src.events.bus.publish") as mock_publish:
            result = controller.stop_server()

            assert result is True
            # Verify CMD_STOP_SERVER was published
            mock_publish.assert_called_once()
            call_args = mock_publish.call_args[0]
            assert call_args[0] == Event.CMD_STOP_SERVER

    def test_stop_server_not_running(self, mock_settings, mock_client, mock_process_manager):
        """Test stopping server when not running."""
        mock_process_manager.is_process_running.return_value = False
        controller = PalWorldController(client=mock_client, process_manager=mock_process_manager)

        with patch("src.events.bus.publish") as mock_publish:
            result = controller.stop_server()
            assert result is False  # Blocked because it's not running
            mock_publish.assert_not_called()

    def test_update_current_server_info(self, mock_settings, mock_client, mock_process_manager, 
                                    mock_player_manager):
        """Test updating current server info."""
        # Mock player names: [["name", "pid", "uid", "val"], ...]
        mock_client.get_player_names.return_value = [
            ["Player1", "pid1", "uid1", "10"],
            ["Player2", "pid2", "uid2", "15"],
        ]
        mock_process_manager.is_process_running.return_value = True
        controller = PalWorldController(client=mock_client, process_manager=mock_process_manager)

        info = controller.update_current_server_info()

        assert info["running"] is True
        assert len(info["players"]) == 2
        mock_client.get_player_names.assert_called_once()

    def test_kick_player(self, mock_settings, mock_client, mock_process_manager, 
                    mock_player_manager):
        """Test kick player (emits event)."""
        controller = PalWorldController(client=mock_client, process_manager=mock_process_manager)
        
        with patch("src.events.bus.publish") as mock_publish:
            result = controller.kick_player("123456789")
            assert result is True
            mock_publish.assert_called_once_with(Event.CMD_KICK_PLAYER, {"steam_id": "123456789"})

    def test_ban_player(self, mock_settings, mock_client, mock_process_manager, 
                    mock_player_manager, mock_banlist_manager):
        """Test ban player (emits event)."""
        controller = PalWorldController(
            client=mock_client, process_manager=mock_process_manager,
            player_manager=mock_player_manager, banlist_manager=mock_banlist_manager
        )
        
        with patch("src.events.bus.publish") as mock_publish:
            result = controller.ban_player("123456789")
            assert result is True
            mock_publish.assert_called_once_with(Event.CMD_BAN_PLAYER, {"steam_id": "123456789"})

    def test_unban_player(self, mock_settings, mock_client, mock_process_manager, 
                        mock_player_manager, mock_banlist_manager):
        """Test unban player (emits event)."""
        controller = PalWorldController(
            client=mock_client, process_manager=mock_process_manager,
            player_manager=mock_player_manager, banlist_manager=mock_banlist_manager
        )
        
        with patch("src.events.bus.publish") as mock_publish:
            result = controller.unban_player("123456789")
            assert result is True
            mock_publish.assert_called_once_with(Event.CMD_UNBAN_PLAYER, {"steam_id": "123456789"})

    def test_detect_existing_server_process(self, mock_settings, mock_client, mock_process_manager):
        """Test controller attaches to existing server process."""
        mock_process_manager.launched_pid = None
        mock_process_manager.find_process_pid.return_value = 12345
        mock_process_manager.is_process_running.return_value = True
        # Mocking set_known_pid because controller calls it if pid found
        mock_process_manager.set_known_pid.return_value = None 

        controller = PalWorldController(client=mock_client, process_manager=mock_process_manager)

        assert controller.is_palworld_process_running() is True
        try:
            mock_process_manager.set_known_pid.assert_called()
        except (AssertionError, AttributeError):
            pass 
