"""
Factory functions for creating mock objects used across tests.
"""

from unittest.mock import MagicMock


def create_mock_http_response(
    status_code=200, content=b'{"success": true}', json_data=None, raise_for_status=None
):
    """Create a mock HTTP response object.

    Args:
        status_code: HTTP status code (default: 200)
        content: Response content bytes (default: b'{"success": true}')
        json_data: JSON data to return from json() method (default: {"success": True})
        raise_for_status: Exception to raise from raise_for_status() (default: None)

    Returns:
        MagicMock configured as an HTTP response
    """
    response = MagicMock()
    response.status_code = status_code
    response.content = content
    response.json.return_value = json_data or {"success": True}
    response.raise_for_status.return_value = raise_for_status
    return response


def create_mock_rcon_console(command_response=None, close_return=None):
    """Create a mock RCON console object.

    Args:
        command_response: Response to return from command() method
                         (default: "name,playerid,userid\\nPlayer1,pid1,uid1")
        close_return: Return value for close() method (default: None)

    Returns:
        MagicMock configured as an RCON console
    """
    console = MagicMock()
    console.command.return_value = (
        command_response or "name,playerid,userid\nPlayer1,pid1,uid1"
    )
    console.close.return_value = close_return
    return console


def create_mock_api_client():
    """Create a mock API client with default return values.

    Returns:
        MagicMock configured as an API client
    """
    mock = MagicMock()
    mock.get_player_count.return_value = 0
    mock.get_player_names.return_value = []
    mock.kick_player.return_value = True
    mock.ban_player.return_value = True
    mock.unban_player.return_value = True
    return mock
