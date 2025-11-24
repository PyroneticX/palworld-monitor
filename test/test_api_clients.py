"""
Tests for the API clients module (RestClient and RconClient).
"""
import pytest
import sys
import os
import json
from unittest.mock import patch, MagicMock
import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api_clients import RestClient, RconClient
from test.support import create_mock_http_response, create_mock_rcon_console


@pytest.fixture
def mock_http_response():
    """Create a mock HTTP response with default values."""
    return create_mock_http_response()


@pytest.fixture
def mock_rcon_console():
    """Create a mock RCON console with default values."""
    return create_mock_rcon_console()


class TestRestClient:
    """Test suite for RestClient."""

    def test_init(self, mock_settings):
        """Test RestClient initialization."""
        client = RestClient()
        assert client.base_url == "http://localhost:8212/v1/api"
        assert client.headers["Content-Type"] == "application/json"
        assert client.auth.username == "admin"
        assert client.auth.password == "test_admin_password"

    def test_make_request_success(self, mock_settings, mock_http_response):
        """Test successful HTTP request."""
        mock_http_response.content = b'{"success": true, "data": "test"}'
        mock_http_response.json.return_value = {"success": True, "data": "test"}
        
        with patch('requests.request', return_value=mock_http_response) as mock_request:
            client = RestClient()
            result = client._make_request("GET", "test")
            
            assert result == {"success": True, "data": "test"}
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[0][0] == "GET"  # method is first positional arg
            assert "test" in call_args[0][1]  # url is second positional arg
            assert call_args[1]['timeout'] == 10

    def test_make_request_no_content(self, mock_settings):
        """Test HTTP request with no content."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.content = b''
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.request', return_value=mock_response):
            client = RestClient()
            result = client._make_request("POST", "test")
            
            assert result is None

    def test_make_request_connection_error(self, mock_settings):
        """Test failed HTTP request with connection error."""
        with patch('requests.request', 
                  side_effect=requests.exceptions.ConnectionError("Connection failed")):
            client = RestClient()
            result = client._make_request("GET", "test")
            
            assert result is None

    def test_make_request_timeout(self, mock_settings):
        """Test HTTP request timeout."""
        with patch('requests.request',
                  side_effect=requests.exceptions.Timeout("Request timeout")):
            client = RestClient()
            result = client._make_request("GET", "test")
            
            assert result is None

    def test_make_request_http_error(self, mock_settings):
        """Test HTTP request with HTTP error status."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Server error")
        
        with patch('requests.request', return_value=mock_response):
            client = RestClient()
            result = client._make_request("GET", "test")
            
            assert result is None

    def test_parse_players_list_from_list(self, mock_settings):
        """Test parsing players list when data is a list."""
        client = RestClient()
        players_data = [
            {"name": "Player1", "playerId": "pid1", "userId": "uid1", "level": "10"},
            {"name": "Player2", "playerId": "pid2", "userId": "uid2", "level": "15"}
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

    @pytest.mark.parametrize("players_data,expected_count", [
        ([{"name": "P1"}, {"name": "P2"}], 2),
        ([], 0),
    ])
    def test_get_player_count(self, mock_settings, mock_http_response, players_data, expected_count):
        """Test getting player count with various scenarios."""
        mock_http_response.content = json.dumps({"players": players_data}).encode()
        mock_http_response.json.return_value = {"players": players_data}
        
        with patch('requests.request', return_value=mock_http_response):
            client = RestClient()
            count = client.get_player_count()
            
            assert count == expected_count

    def test_get_player_count_request_fails(self, mock_settings):
        """Test getting player count when request fails."""
        with patch('requests.request',
                  side_effect=requests.exceptions.RequestException("Error")):
            client = RestClient()
            count = client.get_player_count()
            
            assert count == 0

    def test_get_player_names(self, mock_settings, mock_http_response):
        """Test getting player names."""
        player_data = [{"name": "P1", "userId": "u1", "playerId": "p1", "level": "5"}]
        mock_http_response.content = json.dumps(player_data).encode()
        mock_http_response.json.return_value = player_data
        
        with patch('requests.request', return_value=mock_http_response):
            client = RestClient()
            players = client.get_player_names()
            
            assert len(players) == 1
            assert players[0] == ["P1", "p1", "u1", "5"]

    def test_announce_message(self, mock_settings, mock_http_response):
        """Test sending an announcement."""
        with patch('requests.request', return_value=mock_http_response) as mock_request:
            client = RestClient()
            client._announce_message("Test announcement")
            
            mock_request.assert_called_once()
            call_kwargs = mock_request.call_args[1]
            assert call_kwargs['json'] == {"message": "Test announcement"}

    @pytest.mark.parametrize("response_content,expected_result", [
        (b'{"success": true}', True),
        (b'', False),
    ])
    def test_kick_player(self, mock_settings, mock_http_response, response_content, expected_result):
        """Test kicking a player with success and failure scenarios."""
        mock_http_response.content = response_content
        mock_http_response.json.return_value = {"success": True} if response_content else None
        
        with patch('requests.request', return_value=mock_http_response):
            client = RestClient()
            result = client.kick_player("123456789")
            
            assert result == expected_result

    def test_ban_player_success(self, mock_settings, mock_http_response):
        """Test successfully banning a player via REST."""
        with patch('requests.request', return_value=mock_http_response):
            client = RestClient()
            result = client.ban_player("123456789")
            
            assert result is True

    def test_ban_player_fallback_to_rcon(self, mock_settings):
        """Test ban player falls back to RCON when REST fails."""
        mock_response = MagicMock()
        mock_response.content = b''
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.request', return_value=mock_response):
            # Mock RconClient
            mock_rcon = MagicMock()
            mock_rcon.ban_player.return_value = True
            
            with patch('src.api_clients.RconClient', return_value=mock_rcon):
                client = RestClient()
                result = client.ban_player("123456789")
                
                assert result is True
                mock_rcon.ban_player.assert_called_once_with("123456789")


class TestRconClient:
    """Test suite for RconClient."""

    def test_init(self, mock_settings):
        """Test RconClient initialization."""
        client = RconClient()
        assert client.host == "localhost"
        assert client.port == 25575
        assert client.password == "test_admin_password"

    def test_send_command_success(self, mock_settings, mock_rcon_console):
        """Test successful RCON command."""
        with patch('src.api_clients.Console', return_value=mock_rcon_console) as mock_console_class:
            client = RconClient()
            result = client._send_command("ShowPlayers")
            
            assert result == "name,playerid,userid\nPlayer1,pid1,uid1"
            mock_console_class.assert_called_once_with(
                host="localhost",
                port=25575,
                password="test_admin_password"
            )
            mock_rcon_console.command.assert_called_once_with("ShowPlayers")
            mock_rcon_console.close.assert_called_once()

    def test_send_command_failure(self, mock_settings, mock_rcon_console):
        """Test RCON command failure."""
        mock_rcon_console.command.side_effect = Exception("Connection error")
        
        with patch('src.api_clients.Console', return_value=mock_rcon_console):
            client = RconClient()
            result = client._send_command("ShowPlayers")
            
            assert result is None

    @pytest.mark.parametrize("command_response,expected_count", [
        ("name,playerid,userid\nPlayer1,pid1,uid1\nPlayer2,pid2,uid2", 2),
        ("name,playerid,userid", 0),  # Header only
        (None, 0),  # None response
    ])
    def test_get_player_count(self, mock_settings, mock_rcon_console, command_response, expected_count):
        """Test getting player count via RCON with various scenarios."""
        mock_rcon_console.command.return_value = command_response
        
        with patch('src.api_clients.Console', return_value=mock_rcon_console):
            client = RconClient()
            count = client.get_player_count()
            
            assert count == expected_count

    @pytest.mark.parametrize("command_response,expected_players", [
        ("name,playerid,userid\nPlayer1,pid1,uid1\nPlayer2,pid2,uid2", [
            ["Player1", "pid1", "uid1"],
            ["Player2", "pid2", "uid2"]
        ]),
        ("name,playerid,userid", []),  # Header only
    ])
    def test_get_player_names(self, mock_settings, mock_rcon_console, command_response, expected_players):
        """Test getting player names via RCON with various scenarios."""
        mock_rcon_console.command.return_value = command_response
        
        with patch('src.api_clients.Console', return_value=mock_rcon_console):
            client = RconClient()
            players = client.get_player_names()
            
            assert players == expected_players

    @pytest.mark.parametrize("command_response,expected_result", [
        ("Player kicked successfully", True),
        (None, False),
    ])
    def test_kick_player(self, mock_settings, mock_rcon_console, command_response, expected_result):
        """Test kicking a player via RCON with success and failure scenarios."""
        mock_rcon_console.command.return_value = command_response
        
        with patch('src.api_clients.Console', return_value=mock_rcon_console):
            client = RconClient()
            result = client.kick_player("123456789")
            
            assert result == expected_result

    @pytest.mark.parametrize("command_response,expected_result", [
        ("Player banned successfully", True),
        (None, False),
    ])
    def test_ban_player(self, mock_settings, mock_rcon_console, command_response, expected_result):
        """Test banning a player via RCON with success and failure scenarios."""
        mock_rcon_console.command.return_value = command_response
        
        with patch('src.api_clients.Console', return_value=mock_rcon_console):
            client = RconClient()
            result = client.ban_player("123456789")
            
            assert result == expected_result

