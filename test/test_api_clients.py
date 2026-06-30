"""
Tests for the API clients module (RestClient and RconClient).
"""

import json

import pytest
from unittest.mock import patch, MagicMock
import requests
from src.api_clients import RestClient, RconClient


@pytest.fixture
def mock_http_response():
    """Create a mock HTTP response with default values."""
    from test.support import create_mock_http_response

    return create_mock_http_response()


@pytest.fixture
def mock_rcon_console():
    """Create a mock RCON console with default values."""
    from test.support import create_mock_rcon_console

    return create_mock_rcon_console()


class TestRestClient:
    """Test suite for RestClient."""

    def test_init(self, mock_settings, mock_http_response):
        """Test RestClient can be initialized and make requests."""
        client = RestClient()
        # Test behavior: client can successfully make requests
        mock_http_response.content = b'{"success": true}'
        mock_http_response.json.return_value = {"success": True}

        with patch("requests.get", return_value=mock_http_response):
            result = client._make_get_request("test")
            assert result == {"success": True}

    def test_make_request_success(self, mock_settings, mock_http_response):
        """Test successful HTTP request returns expected data."""
        mock_http_response.content = b'{"success": true, "data": "test"}'
        mock_http_response.json.return_value = {"success": True, "data": "test"}

        with patch("requests.get", return_value=mock_http_response):
            client = RestClient()
            result = client._make_get_request("test")

            # Test behavior: request returns the expected data
            assert result == {"success": True, "data": "test"}

    def test_make_request_no_content(self, mock_settings):
        """Test HTTP request with no content."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.content = b""
        mock_response.raise_for_status.return_value = None

        with patch("requests.post", return_value=mock_response):
            client = RestClient()
            result = client._make_post_request("test")

            assert result == {}

    def test_make_request_connection_error(self, mock_settings):
        """Test failed HTTP request with connection error."""
        with patch(
            "requests.get",
            side_effect=requests.exceptions.ConnectionError("Connection failed"),
        ):
            client = RestClient()
            result = client._make_get_request("test")

            assert result is None

    def test_make_request_timeout(self, mock_settings):
        """Test HTTP request timeout."""
        with patch(
            "requests.get", side_effect=requests.exceptions.Timeout("Request timeout")
        ):
            client = RestClient()
            result = client._make_get_request("test")

            assert result is None

    def test_make_request_http_error(self, mock_settings):
        """Test HTTP request with HTTP error status."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "Server error"
        )

        with patch("requests.get", return_value=mock_response):
            client = RestClient()
            result = client._make_get_request("test")

            assert result is None

    def test_parse_players_list_from_list(self, mock_settings):
        """Test parsing players list when data is a list."""
        client = RestClient()
        players_data = [
            {"name": "Player1", "playerId": "pid1", "userId": "uid1", "level": "10"},
            {"name": "Player2", "playerId": "pid2", "userId": "uid2", "level": "15"},
        ]

        result = client._parse_players_list(players_data)

        assert len(result) == 2
        assert result[0] == ["Player1", "pid1", "uid1", "10"]
        assert result[1] == ["Player2", "pid2", "uid2", "15"]

    def test_parse_players_list_from_dict(self, mock_settings):
        """Test parsing players list when data is a dict with 'players' key."""
        client = RestClient()
        players_data = {
            "players": [
                {"name": "Player1", "playerId": "pid1", "userId": "uid1", "level": "10"}
            ]
        }

        result = client._parse_players_list(players_data)

        assert len(result) == 1
        assert result[0] == ["Player1", "pid1", "uid1", "10"]

    @pytest.mark.parametrize("empty_data", [None, [], {}])
    def test_parse_players_list_empty(self, mock_settings, empty_data):
        """Test parsing empty players list."""
        client = RestClient()
        assert client._parse_players_list(empty_data) == []

    def test_parse_players_list_missing_fields(self, mock_settings):
        """Test parsing players list with missing fields."""
        client = RestClient()
        players_data = [
            {"name": "Player1"}  # Missing other fields
        ]

        result = client._parse_players_list(players_data)

        assert len(result) == 1
        assert result[0] == ["Player1", "Unknown", "Unknown", "Unknown"]

    @pytest.mark.parametrize(
        "players_data,expected_count",
        [
            ([{"name": "P1"}, {"name": "P2"}], 2),
            ([], 0),
        ],
    )
    def test_get_player_count(
        self, mock_settings, mock_http_response, players_data, expected_count
    ):
        """Test getting player count with various scenarios."""
        mock_http_response.content = json.dumps({"players": players_data}).encode()
        mock_http_response.json.return_value = {"players": players_data}

        with patch("requests.get", return_value=mock_http_response):
            client = RestClient()
            count = client.get_player_count()

            assert count == expected_count

    def test_get_player_count_request_fails(self, mock_settings):
        """Test getting player count when request fails."""
        with patch(
            "requests.get", side_effect=requests.exceptions.RequestException("Error")
        ):
            client = RestClient()
            count = client.get_player_count()

            assert count == 0

    def test_get_player_names(self, mock_settings, mock_http_response):
        """Test getting player names."""
        player_data = [{"name": "P1", "userId": "u1", "playerId": "p1", "level": "5"}]
        mock_http_response.content = json.dumps(player_data).encode()
        mock_http_response.json.return_value = player_data

        with patch("requests.get", return_value=mock_http_response):
            client = RestClient()
            players = client.get_player_names()

            assert len(players) == 1
            assert players[0] == ["P1", "p1", "u1", "5"]

    def test_announce_message(self, mock_settings, mock_http_response):
        """Test sending an announcement succeeds."""
        mock_http_response.content = b'{"success": true}'
        mock_http_response.json.return_value = {"success": True}

        with patch("requests.post", return_value=mock_http_response):
            client = RestClient()
            # Test behavior: announcement can be sent without error
            # Method completes successfully (doesn't raise exception)
            client._announce_message("Test announcement")

    @pytest.mark.parametrize(
        "status_code,expected_result",
        [
            (200, True),
            (400, False),
            (500, False),
        ],
    )
    def test_kick_player(self, mock_settings, status_code, expected_result):
        """Test kicking a player with success and failure scenarios."""
        mock_response = MagicMock()
        mock_response.status_code = status_code

        with patch("requests.post", return_value=mock_response):
            client = RestClient()
            player = {"steam_id": "123456789", "name": "TestPlayer"}
            result = client.kick_player(player)

            assert result == expected_result

    @pytest.mark.parametrize(
        "status_code,expected_result",
        [
            (200, True),
            (400, False),
            (500, False),
        ],
    )
    def test_ban_player(self, mock_settings, status_code, expected_result):
        """Test banning a player via REST API."""
        mock_response = MagicMock()
        mock_response.status_code = status_code

        with patch("requests.post", return_value=mock_response):
            client = RestClient()
            player = {"steam_id": "123456789", "name": "TestPlayer"}
            result = client.ban_player(player)

            assert result == expected_result

    @pytest.mark.parametrize(
        "status_code,expected_result",
        [
            (200, True),
            (400, False),
            (500, False),
        ],
    )
    def test_unban_player(self, mock_settings, status_code, expected_result):
        """Test unbanning a player via REST API."""
        mock_response = MagicMock()
        mock_response.status_code = status_code

        with patch("requests.post", return_value=mock_response):
            client = RestClient()
            player = {"steam_id": "123456789", "name": "TestPlayer"}
            result = client.unban_player(player)

            assert result == expected_result


class TestRconClient:
    """Test suite for RconClient."""

    def test_init(self, mock_settings, mock_rcon_console):
        """Test RconClient can be initialized and send commands."""
        client = RconClient()
        # Test behavior: client can successfully send commands
        with patch("src.api_clients.Console", return_value=mock_rcon_console):
            result = client._send_command("ShowPlayers")
            assert result == "name,playerid,userid\nPlayer1,pid1,uid1"

    def test_send_command_success(self, mock_settings, mock_rcon_console):
        """Test successful RCON command returns expected response."""
        with patch("src.api_clients.Console", return_value=mock_rcon_console):
            client = RconClient()
            result = client._send_command("ShowPlayers")

            # Test behavior: command returns the expected response
            assert result == "name,playerid,userid\nPlayer1,pid1,uid1"

    def test_send_command_failure(self, mock_settings, mock_rcon_console):
        """Test RCON command failure."""
        mock_rcon_console.command.side_effect = Exception("Connection error")

        with patch("src.api_clients.Console", return_value=mock_rcon_console):
            client = RconClient()
            result = client._send_command("ShowPlayers")

            assert result is None

    @pytest.mark.parametrize(
        "command_response,expected_count",
        [
            ("name,playerid,userid\nPlayer1,pid1,uid1\nPlayer2,pid2,uid2", 2),
            ("name,playerid,userid", 0),  # Header only
            (None, 0),  # None response
        ],
    )
    def test_get_player_count(
        self, mock_settings, mock_rcon_console, command_response, expected_count
    ):
        """Test getting player count via RCON with various scenarios."""
        mock_rcon_console.command.return_value = command_response

        with patch("src.api_clients.Console", return_value=mock_rcon_console):
            client = RconClient()
            count = client.get_player_count()

            assert count == expected_count

    @pytest.mark.parametrize(
        "command_response,expected_players",
        [
            (
                "name,playerid,userid\nPlayer1,pid1,uid1\nPlayer2,pid2,uid2",
                [["Player1", "pid1", "uid1"], ["Player2", "pid2", "uid2"]],
            ),
            ("name,playerid,userid", []),  # Header only
        ],
    )
    def test_get_player_names(
        self, mock_settings, mock_rcon_console, command_response, expected_players
    ):
        """Test getting player names via RCON with various scenarios."""
        mock_rcon_console.command.return_value = command_response

        with patch("src.api_clients.Console", return_value=mock_rcon_console):
            client = RconClient()
            players = client.get_player_names()

            assert players == expected_players

    @pytest.mark.parametrize(
        "command_response,expected_result",
        [
            ("Player kicked successfully", True),
            (None, False),
        ],
    )
    def test_kick_player(
        self, mock_settings, mock_rcon_console, command_response, expected_result
    ):
        """Test kicking a player via RCON with success and failure scenarios."""
        mock_rcon_console.command.return_value = command_response

        with patch("src.api_clients.Console", return_value=mock_rcon_console):
            client = RconClient()
            player = {"steam_id": "123456789", "name": "TestPlayer"}
            result = client.kick_player(player)

            assert result == expected_result

    @pytest.mark.parametrize(
        "command_response,expected_result",
        [
            ("Player banned successfully", True),
            (None, False),
        ],
    )
    def test_ban_player(
        self, mock_settings, mock_rcon_console, command_response, expected_result
    ):
        """Test banning a player via RCON with success and failure scenarios."""
        mock_rcon_console.command.return_value = command_response

        with patch("src.api_clients.Console", return_value=mock_rcon_console):
            client = RconClient()
            player = {"steam_id": "123456789", "name": "TestPlayer"}
            result = client.ban_player(player)

            assert result == expected_result

    @pytest.mark.parametrize(
        "command_response,expected_result",
        [
            ("Player unbanned successfully", True),
            (None, False),
        ],
    )
    def test_unban_player(
        self, mock_settings, mock_rcon_console, command_response, expected_result
    ):
        """Test unbanning a player via RCON with success and failure scenarios."""
        mock_rcon_console.command.return_value = command_response

        with patch("src.api_clients.Console", return_value=mock_rcon_console):
            client = RconClient()
            player = {"steam_id": "123456789", "name": "TestPlayer"}
            result = client.unban_player(player)

            assert result == expected_result
