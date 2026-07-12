"""
Tests for LGSMProcessManager.

These are unit tests that mock subprocess/psutil calls rather than
launching a real LGSM script.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from src.process_manager import LGSMProcessManager


@pytest.fixture
def manager():
    m = LGSMProcessManager()
    m.launched_pid = None
    # Keep the tests fast: real timeouts default to 30s.
    m.STARTUP_TIMEOUT = 0.2
    m.STARTUP_POLL_INTERVAL = 0.01
    m.SHUTDOWN_VERIFY_TIMEOUT = 0.2
    m.SHUTDOWN_VERIFY_POLL_INTERVAL = 0.01
    return m


class TestLGSMProcessManager:
    def test_pid_file_name(self, manager):
        assert manager.pid_file_name() == "palworld_server.lgsm.pid"

    @patch("src.events.bus.publish")
    @patch("src.process_manager.subprocess.run")
    def test_launch_process_success(self, mock_run, mock_publish, manager):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        manager.find_process_pid = MagicMock(return_value=4242)

        manager.launch_process("/home/gameserver/pwserver/pwserver", "")

        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        assert args[0] == ["/home/gameserver/pwserver/pwserver", "start"]
        assert manager.launched_pid == 4242
        assert manager._exe_path == "/home/gameserver/pwserver/pwserver"
        mock_publish.assert_any_call("SERVER_STARTED", {"pid": 4242})

        # PID file should have been written
        assert os.path.exists(manager.pid_file_name())
        with open(manager.pid_file_name(), "r") as f:
            assert f.read().strip() == "4242"
        os.remove(manager.pid_file_name())

    @patch("src.events.bus.publish")
    @patch("src.process_manager.subprocess.run")
    def test_launch_process_start_command_fails(self, mock_run, mock_publish, manager):
        mock_run.side_effect = Exception("script not found")
        manager.find_process_pid = MagicMock(return_value=4242)

        manager.launch_process("/does/not/exist", "")

        assert manager.launched_pid is None
        mock_publish.assert_not_called()

    @patch("src.events.bus.publish")
    @patch("src.process_manager.subprocess.run")
    def test_launch_process_no_pid_found(self, mock_run, mock_publish, manager):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        manager.find_process_pid = MagicMock(return_value=None)

        manager.launch_process("/home/gameserver/pwserver/pwserver", "")

        assert manager.launched_pid is None
        mock_publish.assert_not_called()

    @patch("src.events.bus.publish")
    @patch("src.process_manager.psutil.pid_exists")
    @patch("src.process_manager.subprocess.run")
    def test_terminate_process_success(self, mock_run, mock_pid_exists, mock_publish, manager):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        mock_pid_exists.return_value = False
        manager.launched_pid = 4242
        manager._exe_path = "/home/gameserver/pwserver/pwserver"
        manager._save_pid_to_file(4242)

        result = manager.terminate_process()

        assert result is True
        assert manager.launched_pid is None
        assert not os.path.exists(manager.pid_file_name())
        mock_run.assert_called_once()
        args, _kwargs = mock_run.call_args
        assert args[0] == ["/home/gameserver/pwserver/pwserver", "stop"]
        mock_publish.assert_any_call("SERVER_STOPPED", {"pid": 4242})

    @patch("src.process_manager.subprocess.run")
    def test_terminate_process_stop_command_fails(self, mock_run, manager):
        mock_run.side_effect = Exception("boom")
        manager.launched_pid = 4242
        manager._exe_path = "/home/gameserver/pwserver/pwserver"

        result = manager.terminate_process()

        assert result is False
        # State is left untouched so a retry is possible.
        assert manager.launched_pid == 4242

    @patch("src.process_manager.psutil.pid_exists")
    @patch("src.process_manager.subprocess.run")
    def test_terminate_process_still_running_after_timeout(
        self, mock_run, mock_pid_exists, manager
    ):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        mock_pid_exists.return_value = True
        manager.launched_pid = 4242
        manager._exe_path = "/home/gameserver/pwserver/pwserver"

        result = manager.terminate_process()

        assert result is False
        assert manager.launched_pid == 4242

    def test_terminate_process_with_no_pid(self, manager):
        manager.launched_pid = None
        assert manager.terminate_process() is False

    @patch("src.process_manager.psutil.pid_exists")
    @patch("src.process_manager.subprocess.run")
    def test_terminate_process_falls_back_to_settings_exe_path(
        self, mock_run, mock_pid_exists, manager
    ):
        """If the manager never launched the server itself in this process
        (e.g. monitor restarted and re-attached to an already-running LGSM
        server), it should still know how to stop it via settings."""
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        mock_pid_exists.return_value = False
        manager.launched_pid = 4242
        manager._exe_path = None

        with patch(
            "src.process_manager.settings.palworldServerExePath",
            "/home/gameserver/pwserver/pwserver",
        ):
            result = manager.terminate_process()

        assert result is True
        args, _kwargs = mock_run.call_args
        assert args[0] == ["/home/gameserver/pwserver/pwserver", "stop"]
