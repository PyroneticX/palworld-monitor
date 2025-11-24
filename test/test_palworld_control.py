"""
Tests for the PalWorldController module.
"""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.palworld_control import PalWorldController
from test.support import create_mock_api_client, get_controller_patches


class TestPalWorldController:
    """Test suite for PalWorldController."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock API client."""
        return create_mock_api_client()


    def test_init(self, mock_settings, mock_client, mock_process_manager,
                  mock_player_manager, mock_banlist_manager):
        """Test PalWorldController initialization."""
        patches = get_controller_patches(
            process_manager=mock_process_manager,
            player_manager=mock_player_manager,
            banlist_manager=mock_banlist_manager
        )
        with patches[0], patches[1], patches[2], patches[3]:
            controller = PalWorldController(mock_client)
            
            assert controller.client == mock_client
            assert controller.player_manager == mock_player_manager
            assert controller.banlist_manager == mock_banlist_manager
            assert controller.process_manager == mock_process_manager
            assert controller.current_server_info["running"] is False
            assert controller.current_server_info["playerCount"] == 0

    def test_is_palworld_process_running(self, mock_settings, mock_client,
                                         mock_process_manager):
        """Test checking if process is running."""
        mock_process_manager.is_process_running.return_value = True
        
        with patch('src.palworld_control.PlayerManager'), \
             patch('src.palworld_control.BanlistManager'), \
             patch('process_manager.WindowsProcessManager', return_value=mock_process_manager), \
             patch('os.path.exists', return_value=False):
            
            controller = PalWorldController(mock_client)
            assert controller.is_palworld_process_running() is True

    def test_start_server_success(self, mock_settings, mock_client, mock_process_manager):
        """Test successfully starting the server."""
        # Initially not running, then running after launch
        mock_process_manager.is_process_running.side_effect = [False, True]
        
        with patch('src.palworld_control.PlayerManager'), \
             patch('src.palworld_control.BanlistManager'), \
             patch('process_manager.WindowsProcessManager', return_value=mock_process_manager), \
             patch('os.path.exists', return_value=False), \
             patch('time.time', return_value=1000), \
             patch.object(PalWorldController, '_handle_server_started'), \
             patch('subprocess.CalledProcessError'):
            
            controller = PalWorldController(mock_client)
            controller.last_server_started_time = 0
            controller.last_server_stopped_time = 0
            
            result = controller.start_server()
            
            assert result is True
            mock_process_manager.launch_process.assert_called_once()

    def test_start_server_already_running(self, mock_settings, mock_client,
                                          mock_process_manager):
        """Test starting server when already running."""
        mock_process_manager.is_process_running.return_value = True
        
        with patch('src.palworld_control.PlayerManager'), \
             patch('src.palworld_control.BanlistManager'), \
             patch('process_manager.WindowsProcessManager', return_value=mock_process_manager), \
             patch('os.path.exists', return_value=False), \
             patch('time.time', return_value=1000):
            
            controller = PalWorldController(mock_client)
            controller.last_server_started_time = 0
            
            result = controller.start_server()
            
            assert result is False  # Should be blocked
            mock_process_manager.launch_process.assert_not_called()

    def test_start_server_too_soon_after_start(self, mock_settings, mock_client,
                                               mock_process_manager):
        """Test starting server too soon after previous start."""
        mock_process_manager.is_process_running.return_value = False
        
        with patch('src.palworld_control.PlayerManager'), \
             patch('src.palworld_control.BanlistManager'), \
             patch('process_manager.WindowsProcessManager', return_value=mock_process_manager), \
             patch('os.path.exists', return_value=False), \
             patch('time.time', return_value=1003):  # Only 3 seconds since last start
            
            controller = PalWorldController(mock_client)
            controller.last_server_started_time = 1000
            controller.server_starting_cooldown = 5
            
            result = controller.start_server()
            
            assert result is False  # Should be blocked by cooldown

    def test_start_server_too_soon_after_stop(self, mock_settings, mock_client,
                                               mock_process_manager):
        """Test starting server too soon after stop."""
        mock_process_manager.is_process_running.return_value = False
        
        with patch('src.palworld_control.PlayerManager'), \
             patch('src.palworld_control.BanlistManager'), \
             patch('process_manager.WindowsProcessManager', return_value=mock_process_manager), \
             patch('os.path.exists', return_value=False), \
             patch('time.time', return_value=1003):  # Only 3 seconds since last stop
            
            controller = PalWorldController(mock_client)
            controller.last_server_stopped_time = 1000
            controller.server_stopping_cooldown = 5
            
            result = controller.start_server()
            
            assert result is False  # Should be blocked by cooldown

    def test_start_server_process_fails(self, mock_settings, mock_client,
                                        mock_process_manager):
        """Test starting server when process launch fails."""
        mock_process_manager.is_process_running.return_value = False
        
        with patch('src.palworld_control.PlayerManager'), \
             patch('src.palworld_control.BanlistManager'), \
             patch('process_manager.WindowsProcessManager', return_value=mock_process_manager), \
             patch('os.path.exists', return_value=False), \
             patch('time.time', return_value=1000):
            
            controller = PalWorldController(mock_client)
            controller.last_server_started_time = 0
            controller.last_server_stopped_time = 0
            
            result = controller.start_server()
            
            assert result is True  # Method returns True even if process doesn't start
            mock_process_manager.launch_process.assert_called_once()

    def test_stop_server_success(self, mock_settings, mock_client, mock_process_manager):
        """Test successfully stopping the server."""
        mock_process_manager.is_process_running.return_value = True
        mock_process_manager.terminate_process.return_value = True
        
        with patch('src.palworld_control.PlayerManager'), \
             patch('src.palworld_control.BanlistManager'), \
             patch('process_manager.WindowsProcessManager', return_value=mock_process_manager), \
             patch('os.path.exists', return_value=False), \
             patch('time.time', return_value=1000), \
             patch('threading.Thread'):
            
            controller = PalWorldController(mock_client)
            controller.last_server_stopped_time = 0
            
            controller.stop_server()
            
            mock_process_manager.terminate_process.assert_called()

    def test_stop_server_not_running(self, mock_settings, mock_client, mock_process_manager):
        """Test stopping server when not running."""
        mock_process_manager.is_process_running.return_value = False
        
        with patch('src.palworld_control.PlayerManager'), \
             patch('src.palworld_control.BanlistManager'), \
             patch('process_manager.WindowsProcessManager', return_value=mock_process_manager), \
             patch('os.path.exists', return_value=False), \
             patch('threading.Thread'):
            
            controller = PalWorldController(mock_client)
            controller.stop_server()
            
            # stop_server still attempts termination even when not running
            # Verify it updates server info and attempts termination
            assert controller.current_server_info["running"] is False
            assert controller.current_server_info["playerCount"] == 0
            mock_process_manager.terminate_process.assert_called()

    def test_get_current_server_info(self, mock_settings, mock_client, mock_process_manager):
        """Test getting current server info."""
        with patch('src.palworld_control.PlayerManager'), \
             patch('src.palworld_control.BanlistManager'), \
             patch('process_manager.WindowsProcessManager', return_value=mock_process_manager), \
             patch('os.path.exists', return_value=False):
            
            controller = PalWorldController(mock_client)
            controller.current_server_info = {
                "running": True,
                "playerCount": 2,
                "players": [["Player1"], ["Player2"]]
            }
            
            info = controller.get_current_server_info()
            
            assert info["running"] is True
            assert info["playerCount"] == 2
            assert len(info["players"]) == 2

    def test_update_current_server_info(self, mock_settings, mock_client, mock_process_manager,
                                        mock_player_manager):
        """Test updating current server info."""
        mock_client.get_player_names.return_value = [
            ["Player1", "pid1", "uid1", "10"],
            ["Player2", "pid2", "uid2", "15"]
        ]
        mock_process_manager.is_process_running.return_value = True
        
        with patch('src.palworld_control.PlayerManager', return_value=mock_player_manager), \
             patch('src.palworld_control.BanlistManager'), \
             patch('process_manager.WindowsProcessManager', return_value=mock_process_manager), \
             patch('os.path.exists', return_value=False):
            
            controller = PalWorldController(mock_client)
            info = controller.update_current_server_info()
            
            assert info["running"] is True
            assert info["playerCount"] == 2
            mock_client.get_player_names.assert_called_once()

    def test_update_current_server_info_server_not_running(self, mock_settings, mock_client,
                                                           mock_process_manager):
        """Test updating server info when server is not running."""
        mock_process_manager.is_process_running.return_value = False
        
        with patch('src.palworld_control.PlayerManager'), \
             patch('src.palworld_control.BanlistManager'), \
             patch('process_manager.WindowsProcessManager', return_value=mock_process_manager), \
             patch('os.path.exists', return_value=False):
            
            controller = PalWorldController(mock_client)
            info = controller.update_current_server_info()
            
            assert info["running"] is False
            assert info["playerCount"] == 0

    def test_kick_player(self, mock_settings, mock_client, mock_process_manager):
        """Test kicking a player."""
        mock_client.kick_player.return_value = True
        
        with patch('src.palworld_control.PlayerManager'), \
             patch('src.palworld_control.BanlistManager'), \
             patch('process_manager.WindowsProcessManager', return_value=mock_process_manager), \
             patch('os.path.exists', return_value=False):
            
            controller = PalWorldController(mock_client)
            result = controller.kick_player("123456789")
            
            assert result is True
            mock_client.kick_player.assert_called_once_with("123456789")

    def test_ban_player(self, mock_settings, mock_client, mock_process_manager,
                       mock_banlist_manager):
        """Test banning a player."""
        mock_client.ban_player.return_value = True
        mock_banlist_manager.add_ban.return_value = True
        
        with patch('src.palworld_control.PlayerManager'), \
             patch('src.palworld_control.BanlistManager', return_value=mock_banlist_manager), \
             patch('process_manager.WindowsProcessManager', return_value=mock_process_manager), \
             patch('os.path.exists', return_value=False):
            
            controller = PalWorldController(mock_client)
            result = controller.ban_player("123456789")
            
            assert result is True
            mock_client.ban_player.assert_called_once_with("123456789")
            mock_banlist_manager.add_ban.assert_called_once_with("123456789")

    def test_set_on_server_started_callback(self, mock_settings, mock_client,
                                            mock_process_manager):
        """Test setting server started callback."""
        callback = MagicMock()
        
        with patch('src.palworld_control.PlayerManager'), \
             patch('src.palworld_control.BanlistManager'), \
             patch('process_manager.WindowsProcessManager', return_value=mock_process_manager), \
             patch('os.path.exists', return_value=False):
            
            controller = PalWorldController(mock_client)
            controller.set_on_server_started_callback(callback)
            
            assert controller.on_server_started_callback == callback

    def test_set_on_server_stopped_callback(self, mock_settings, mock_client,
                                            mock_process_manager):
        """Test setting server stopped callback."""
        callback = MagicMock()
        
        with patch('src.palworld_control.PlayerManager'), \
             patch('src.palworld_control.BanlistManager'), \
             patch('process_manager.WindowsProcessManager', return_value=mock_process_manager), \
             patch('os.path.exists', return_value=False):
            
            controller = PalWorldController(mock_client)
            controller.set_on_server_stopped_callback(callback)
            
            assert controller.on_server_stopped_callback == callback

    def test_detect_existing_server_process(self, mock_settings, mock_client,
                                            mock_process_manager):
        """Test detecting existing server process."""
        mock_process_manager.launched_pid = None
        mock_process_manager.find_process_pid.return_value = 12345
        
        with patch('src.palworld_control.PlayerManager'), \
             patch('src.palworld_control.BanlistManager'), \
             patch('process_manager.WindowsProcessManager', return_value=mock_process_manager), \
             patch('os.path.exists', return_value=False), \
             patch.object(PalWorldController, '_handle_server_started'):
            
            controller = PalWorldController(mock_client)
            
            mock_process_manager.find_process_pid.assert_called_once_with("palserver")
            mock_process_manager.set_known_pid.assert_called_once_with(12345)

    def test_detect_existing_server_process_with_pid(self, mock_settings, mock_client,
                                                     mock_process_manager):
        """Test detecting existing server when PID already known."""
        mock_process_manager.launched_pid = 12345
        
        with patch('src.palworld_control.PlayerManager'), \
             patch('src.palworld_control.BanlistManager'), \
             patch('process_manager.WindowsProcessManager', return_value=mock_process_manager), \
             patch('os.path.exists', return_value=False):
            
            controller = PalWorldController(mock_client)
            
            # Should not try to find process if PID already known
            mock_process_manager.find_process_pid.assert_not_called()

