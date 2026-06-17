"""
Tests for the AutoStartManager module.
"""

import pytest
from unittest.mock import MagicMock, patch
from src.auto_start import AutoStartManager
from src.events import Event


class TestAutoStartManager:
    """Test suite for AutoStartManager."""

    @pytest.fixture
    def mock_controller(self, mock_process_manager):
        """Create a mock PalWorldController."""
        controller = MagicMock()
        controller.process_manager = mock_process_manager
        controller.is_palworld_process_running.return_value = False
        return controller

    def test_init_subscribes_to_server_events(self, mock_controller, mock_settings):
        with patch("src.auto_start.bus.subscribe") as mock_subscribe:
            manager = AutoStartManager(mock_controller)

            mock_subscribe.assert_any_call(Event.SERVER_STARTED, manager.stop_listen_thread)
            mock_subscribe.assert_any_call(Event.SERVER_STOPPED, manager.listen_palworld_access)

    def test_server_started_handler_is_stop_listen_thread(self, mock_controller, mock_settings):
        handlers = {}

        def capture_subscribe(event_type, callback):
            handlers[event_type] = callback

        with patch("src.auto_start.bus.subscribe", side_effect=capture_subscribe):
            manager = AutoStartManager(mock_controller)

        assert handlers[Event.SERVER_STARTED].__self__ is manager
        assert handlers[Event.SERVER_STARTED].__func__ is AutoStartManager.stop_listen_thread

    def test_server_stopped_handler_is_listen_palworld_access(self, mock_controller, mock_settings):
        handlers = {}

        def capture_subscribe(event_type, callback):
            handlers[event_type] = callback

        with patch("src.auto_start.bus.subscribe", side_effect=capture_subscribe):
            manager = AutoStartManager(mock_controller)

        assert handlers[Event.SERVER_STOPPED].__self__ is manager
        assert handlers[Event.SERVER_STOPPED].__func__ is AutoStartManager.listen_palworld_access
