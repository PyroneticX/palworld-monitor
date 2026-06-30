"""
Tests for the AutoStartManager module.
"""

import types

import pytest
from unittest.mock import patch, MagicMock
from src.auto_start import AutoStartManager
from src.events import Event


@pytest.fixture
def mock_controller():
    """A stand-in controller fixture (unused in these tests)."""
    return None


class TestAutoStartManager:
    """Test suite for AutoStartManager."""

    def test_init_subscribes_to_server_events(self, mock_controller):
        with patch("src.auto_start.bus.subscribe") as mock_subscribe:
            manager = AutoStartManager(mock_controller)

            mock_subscribe.assert_any_call(
                Event.SERVER_STARTED, manager.stop_listen_thread
            )
            mock_subscribe.assert_any_call(
                Event.SERVER_STOPPED, manager.listen_palworld_access
            )

    def test_server_started_handler_is_stop_listen_thread(self):
        handlers = {}

        def capture_subscribe(event_type, callback):
            handlers[event_type] = callback

        with patch("src.auto_start.bus.subscribe", side_effect=capture_subscribe):
            manager = AutoStartManager(None)

        assert isinstance(handlers[Event.SERVER_STARTED], types.MethodType)
        assert handlers[Event.SERVER_STARTED].__self__ is manager
        assert (
            handlers[Event.SERVER_STARTED].__func__.__name__ == "stop_listen_thread"
        )

    def test_server_stopped_handler_is_listen_palworld_access(self):
        import types

        handlers = {}

        def capture_subscribe(event_type, callback):
            handlers[event_type] = callback

        with patch("src.auto_start.bus.subscribe", side_effect=capture_subscribe):
            manager = AutoStartManager(None)

        assert isinstance(handlers[Event.SERVER_STOPPED], types.MethodType)
        assert handlers[Event.SERVER_STOPPED].__self__ is manager
        assert (
            handlers[Event.SERVER_STOPPED].__func__.__name__ == "listen_palworld_access"
        )
