"""
Extended tests for AutoStartManager covering packet detection and socket handling.
"""

import pytest
from unittest.mock import MagicMock, patch
from src.auto_start import AutoStartManager


class TestAutoStartPacketDetection:
    """Test suite for _is_player_connection_packet."""

    def test_valid_player_packet(self, mock_settings):
        """Test detection of a valid player connection packet."""
        manager = AutoStartManager(None)
        # The first packet from Palworld clients starts with \x09\x08\x00
        assert manager._is_player_connection_packet(b"\x09\x08\x00") is True

    def test_invalid_packet(self, mock_settings):
        """Test rejection of non-player packets."""
        manager = AutoStartManager(None)
        assert manager._is_player_connection_packet(b"\x00\x00\x00") is False

    def test_empty_data(self, mock_settings):
        """Test handling of empty data."""
        manager = AutoStartManager(None)
        assert manager._is_player_connection_packet(b"") is False

    def test_partial_match(self, mock_settings):
        """Test that partial matches to the pattern are rejected."""
        # Only first byte matches but not the full pattern
        manager = AutoStartManager(None)
        assert manager._is_player_connection_packet(b"\x09\x00\x00") is False

    def test_longer_valid_packet(self, mock_settings):
        """Test detection of a longer valid packet (with payload after header)."""
        manager = AutoStartManager(None)
        # Valid header followed by random data
        assert manager._is_player_connection_packet(b"\x09\x08\x00" + b"\x01" * 50) is True

    def test_random_garbage_rejected(self, mock_settings):
        """Test that random garbage data is rejected."""
        import os
        manager = AutoStartManager(None)
        # Random bytes are unlikely to match the pattern
        assert manager._is_player_connection_packet(os.urandom(100)) is False


class TestAutoStartSocketHandling:
    """Test suite for socket-related methods."""

    def test_close_palworld_port_socket_no_sock(self, mock_settings):
        """Test closing when no socket exists."""
        manager = AutoStartManager(None)
        result = manager.close_palworld_port_socket()
        assert result is True  # No-op should succeed

    def test_wait_for_player_connection_with_packet(self, mock_settings):
        """Test wait_for_player_connection with a valid packet."""
        manager = AutoStartManager(None)
        # Set up a mock socket that will receive data
        mock_sock = MagicMock()
        mock_sock.recvfrom.return_value = (b"\x09\x08\x00", ("127.0.0.1", 8211))

        with patch.object(manager, "_is_player_connection_packet", return_value=True):
            manager.sock = mock_sock
            result = manager.wait_for_player_connection()
            assert result is True

    def test_wait_for_player_connection_socket_none(self, mock_settings):
        """Test wait_for_player_connection when socket is None."""
        manager = AutoStartManager(None)
        manager.sock = None
        result = manager.wait_for_player_connection()
        assert result is False

    def test_wait_for_player_connection_aborting(self, mock_settings):
        """Test wait_for_player_connection when aborting."""
        manager = AutoStartManager(None)
        manager.is_aborting = True
        result = manager.wait_for_player_connection()
        assert result is False

    def test_listen_palworld_access_core_server_running(self, mock_settings):
        """Test listen_palworld_access_core when server is already running."""
        controller = MagicMock()
        controller.is_palworld_process_running.return_value = True
        manager = AutoStartManager(controller)
        # Should return immediately without trying to open socket
        result = manager.listen_palworld_access_core()
        assert result is None  # Returns None (no explicit return)

    def test_listen_palworld_access_starts_thread(self, mock_settings):
        """Test that listen_palworld_access starts a new thread."""
        controller = MagicMock()
        controller.is_palworld_process_running.return_value = False
        manager = AutoStartManager(controller)
        # Should start a listen thread
        manager.listen_palworld_access()
        assert manager.listen_thread is not None
        assert manager.listen_thread.is_alive()

    def test_stop_listen_thread(self, mock_settings):
        """Test stopping the listen thread."""
        controller = MagicMock()
        controller.is_palworld_process_running.return_value = False
        manager = AutoStartManager(controller)
        manager.listen_palworld_access()
        # Stop the thread
        manager.stop_listen_thread()
        assert manager.listen_thread is None

    def test_wait_for_player_connection_os_error(self, mock_settings):
        """Test wait_for_player_connection with socket error."""
        manager = AutoStartManager(None)
        mock_sock = MagicMock()
        mock_sock.recvfrom.side_effect = OSError("Socket error")
        manager.sock = mock_sock
        result = manager.wait_for_player_connection()
        assert result is False

    def test_wait_for_player_connection_generic_error(self, mock_settings):
        """Test wait_for_player_connection with generic exception."""
        manager = AutoStartManager(None)
        mock_sock = MagicMock()
        mock_sock.recvfrom.side_effect = Exception("Generic error")
        manager.sock = mock_sock
        result = manager.wait_for_player_connection()
        assert result is False

    def test_listen_palworld_access_core_socket_failure(self, mock_settings):
        """Test listen_palworld_access_core when socket opening fails."""
        controller = MagicMock()
        controller.is_palworld_process_running.return_value = False
        manager = AutoStartManager(controller)

        # Mock open_palworld_port_socket to fail
        with patch.object(manager, "open_palworld_port_socket", return_value=False):
            result = manager.listen_palworld_access_core()
            assert result is None  # Returns None on failure

    def test_listen_palworld_access_core_start_failure(self, mock_settings):
        """Test listen_palworld_access_core when server start fails."""
        controller = MagicMock()
        controller.is_palworld_process_running.return_value = False
        manager = AutoStartManager(controller)

        # Mock wait_for_player_connection to return True (player detected)
        with patch.object(manager, "wait_for_player_connection", return_value=True):
            with patch("time.sleep", return_value=None):
                result = manager.listen_palworld_access_core()
                # Should attempt to start server
                assert controller.start_server.called

    def test_listen_palworld_access_core_success(self, mock_settings):
        """Test listen_palworld_access_core successful flow."""
        controller = MagicMock()
        controller.is_palworld_process_running.return_value = False
        manager = AutoStartManager(controller)

        # Mock wait_for_player_connection to return True (player detected)
        with patch.object(manager, "wait_for_player_connection", return_value=True):
            with patch("time.sleep", return_value=None):
                result = manager.listen_palworld_access_core()
                assert controller.start_server.called


class TestAutoStartAbortFlow:
    """Test suite for abort and cleanup flows."""

    def test_is_aborting_flag_set_on_close(self, mock_settings):
        """Test that close_palworld_port_socket sets is_aborting flag."""
        manager = AutoStartManager(None)
        manager.close_palworld_port_socket()
        assert manager.is_aborting is True

    def test_listen_palworld_access_stops_existing_thread(self, mock_settings):
        """Test that listen_palworld_access stops any existing thread first."""
        controller = MagicMock()
        controller.is_palworld_process_running.return_value = False
        manager = AutoStartManager(controller)

        # Start a thread
        manager.listen_palworld_access()
        assert manager.listen_thread is not None

        # Starting again should stop the old one and start a new one
        manager.listen_palworld_access()
        assert manager.listen_thread is not None
        
        # Clean up the thread
        manager.stop_listen_thread()

    def test_wait_for_player_connection_returns_false_on_aborted(self, mock_settings):
        """Test that wait_for_player_connection returns False when aborted."""
        manager = AutoStartManager(None)
        manager.is_aborting = True
        result = manager.wait_for_player_connection()
        assert result is False
