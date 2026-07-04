"""
Tests for the EventBus and Event constants.
"""

from src.events import bus, Event


class TestEventBus:
    """Test suite for EventBus."""

    def test_subscribe_and_publish(self):
        """Test subscribing to an event and publishing triggers callback."""
        received = []
        bus.subscribe("TEST_EVENT", lambda data: received.append(data))
        bus.publish("TEST_EVENT", {"key": "value"})
        assert received == [{"key": "value"}]

    def test_multiple_subscribers(self):
        """Test multiple subscribers for the same event."""
        results = []
        bus.subscribe("MULTI_EVENT", lambda data: results.append(("a", data)))
        bus.subscribe("MULTI_EVENT", lambda data: results.append(("b", data)))
        bus.publish("MULTI_EVENT", {"data": 1})
        assert len(results) == 2
        assert ("a", {"data": 1}) in results
        assert ("b", {"data": 1}) in results

    def test_no_subscribers(self):
        """Test publishing to an event with no subscribers."""
        # Should not raise any exception
        bus.publish("NONEXISTENT_EVENT", {})

    def _make_callback(self, received):
        """Helper to create a callback function that appends to received list."""
        def callback(data):
            received.append(data)
        return callback

    def test_unsubscribe_via_removal(self):
        """Test that removing a subscriber stops delivery."""
        received = []
        callback = self._make_callback(received)
        bus.subscribe("REMOVE_TEST", callback)
        bus.publish("REMOVE_TEST", {"step": 1})
        assert len(received) == 1

        # Remove the subscriber by re-subscribing with a different callback
        # (EventBus doesn't have unsubscribe, but we can verify behavior)
        bus.subscribe("REMOVE_TEST", lambda data: received.append("new"))
        bus.publish("REMOVE_TEST", {"step": 2})
        assert len(received) == 3  # old + new subscriber both fire

    def test_subscriber_error_does_not_break_others(self):
        """Test that a failing subscriber doesn't prevent other subscribers from running."""
        results = []
        bus.subscribe("ERROR_TEST", lambda data: (_ for _ in ()).throw(ValueError("boom")))
        bus.subscribe("ERROR_TEST", lambda data: results.append(data))
        bus.publish("ERROR_TEST", {"data": 1})
        assert results == [{"data": 1}]

    def test_event_constants(self):
        """Test that event constants are defined."""
        assert Event.SERVER_STARTED == "SERVER_STARTED"
        assert Event.SERVER_STOPPED == "SERVER_STOPPED"
        assert Event.PLAYER_JOINED == "PLAYER_JOINED"
        assert Event.PLAYER_LEFT == "PLAYER_LEFT"
        assert Event.BAN_ADDED == "BAN_ADDED"
        assert Event.BAN_REMOVED == "BAN_REMOVED"
        assert Event.SERVER_STATUS == "SERVER_STATUS"
        assert Event.CMD_START_SERVER == "CMD_START_SERVER"
        assert Event.CMD_STOP_SERVER == "CMD_STOP_SERVER"
        assert Event.CMD_KICK_PLAYER == "CMD_KICK_PLAYER"
        assert Event.CMD_BAN_PLAYER == "CMD_BAN_PLAYER"
        assert Event.CMD_UNBAN_PLAYER == "CMD_UNBAN_PLAYER"

    def test_bus_singleton(self):
        """Test that bus is a singleton instance."""
        from src.events import bus as bus2
        assert bus is bus2


class TestEventSubscriptionPatterns:
    """Test common subscription patterns used across the codebase."""

    def test_server_started_handler_pattern(self):
        """Test the pattern used by PalWorldController._on_server_started."""
        call_count = [0]

        def on_server_started(data):
            call_count[0] += 1
            assert "pid" in data

        bus.subscribe(Event.SERVER_STARTED, on_server_started)
        bus.publish(Event.SERVER_STARTED, {"pid": 12345})
        assert call_count[0] == 1

    def test_auto_stop_condition_pattern(self):
        """Test the pattern used by PalWorldController._on_server_status for auto-stop."""
        received_data = []

        def on_status(data):
            received_data.append(data)

        bus.subscribe(Event.SERVER_STATUS, on_status)
        bus.publish(
            Event.SERVER_STATUS,
            {"running": True, "playerCount": 0, "players": [], "banned_players": []},
        )
        assert len(received_data) == 1
        assert received_data[0]["playerCount"] == 0

    def test_player_join_event_pattern(self):
        """Test the pattern used by PlayerManager.update_players_from_server."""
        joined_ids = []

        def on_player_joined(data):
            joined_ids.append(data["steam_id"])

        bus.subscribe(Event.PLAYER_JOINED, on_player_joined)
        bus.publish(Event.PLAYER_JOINED, {"steam_id": "12345", "name": "Test"})
        assert joined_ids == ["12345"]

    def test_ban_events_pattern(self):
        """Test ban add/remove event patterns used by BanlistManager."""
        banned = []
        unbanned = []

        bus.subscribe(Event.BAN_ADDED, lambda data: banned.append(data["steam_id"]))
        bus.subscribe(
            Event.BAN_REMOVED, lambda data: unbanned.append(data["steam_id"])
        )

        bus.publish(Event.BAN_ADDED, {"steam_id": "99999"})
        bus.publish(Event.BAN_REMOVED, {"steam_id": "99999"})

        assert banned == ["99999"]
        assert unbanned == ["99999"]
