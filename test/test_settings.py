"""
Tests for the Settings module.
"""
import pytest
import yaml
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.settings import Settings, FIRST_PACKET_PATTERN
from contextlib import contextmanager


class TestSettings:
    """Test suite for Settings class."""

    @contextmanager
    def _temp_server_exe(self):
        """Create a temporary server executable file for testing.

        Yields:
            str: Path to the temporary server executable file.
        """
        with tempfile.NamedTemporaryFile(delete=False) as server_exe:
            server_exe_path = server_exe.name

        try:
            yield server_exe_path
        finally:
            os.unlink(server_exe_path)

    def test_default_settings(self):
        """Test that default settings enable expected behaviors."""
        settings = Settings()

        # Test behavior: settings can be accessed via dictionary interface
        assert settings['palworldServerPort'] == 8211

        # Test behavior: critical defaults enable server functionality
        assert settings.protocol == "REST"  # Determines API client type
        assert settings.useWebServer is True  # Enables web interface
        assert settings.autoStart is True  # Enables auto-start feature
        assert settings.autoStop is True  # Enables auto-stop feature

        # Test behavior: security defaults are set
        assert settings.maxLoginAttempts == 5  # Prevents brute force
        assert settings.rateLimitEnabled is True  # Prevents abuse

        # Test behavior: first packet pattern is correctly defined
        assert settings.firstPacketPattern == FIRST_PACKET_PATTERN

    def test_getitem(self):
        """Test dictionary-like access to settings."""
        settings = Settings()
        assert settings['palworldServerPort'] == 8211

    def test_setitem(self):
        """Test setting values via dictionary-like access."""
        settings = Settings()
        settings['test_key'] = 'test_value'
        assert settings['test_key'] == 'test_value'
        assert settings.test_key == 'test_value'

    def test_read_settings_from_file(self):
        """Test reading settings from a nested YAML file."""
        settings = Settings()

        # Create a temporary settings file with required settings in nested structure
        test_settings = {
            'palserver': {
                'port': 9999,
                'exePath': '/path/to/server.exe',
                'adminPassword': 'admin123'
            },
            'web': {
                'username': 'testuser',
                'password': 'webpass123'
            },
            'security': {
                'sessionSecretKey': 'test_secret_key_123456789012345678901234567890'
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(test_settings, f)
            temp_path = f.name

        try:
            settings.readSettings(temp_path)
            assert settings.palworldServerPort == 9999
            assert settings.webUsername == 'testuser'
        finally:
            os.unlink(temp_path)

    def test_read_settings_file_not_found(self):
        """Test handling of missing settings file."""
        settings = Settings()
        original_port = settings.palworldServerPort

        # Set required settings in the settings dict to avoid validation error
        settings['palworldServerExePath'] = '/path/to/server.exe'
        settings['palworldServerAdminPassword'] = 'admin123'
        settings['webPassword'] = 'webpass123'
        settings['sessionSecretKey'] = 'test_secret_key_123456789012345678901234567890'

        # Should not raise an exception, just log
        settings.readSettings('nonexistent_file.yaml')

        # Settings should remain unchanged
        assert settings.palworldServerPort == original_port

    def test_read_settings_invalid_yaml(self):
        """Test handling of invalid YAML in settings file."""
        settings = Settings()
        original_port = settings.palworldServerPort

        # Set required settings in the settings dict to avoid validation error
        settings['palworldServerExePath'] = '/path/to/server.exe'
        settings['palworldServerAdminPassword'] = 'admin123'
        settings['webPassword'] = 'webpass123'
        settings['sessionSecretKey'] = 'test_secret_key_123456789012345678901234567890'

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write('invalid: yaml: content: [')
            temp_path = f.name

        try:
            settings.readSettings(temp_path)
            # Settings should remain unchanged
            assert settings.palworldServerPort == original_port
        finally:
            os.unlink(temp_path)

    def test_read_settings_partial_update(self):
        """Test that reading settings only updates provided keys."""
        settings = Settings()
        original_port = settings.palworldServerPort

        # Include required settings in partial nested update
        test_settings = {
            'palserver': {
                'exePath': '/path/to/server.exe',
                'adminPassword': 'admin123'
            },
            'web': {
                'password': 'webpass123'
            },
            'security': {
                'sessionSecretKey': 'test_secret_key_123456789012345678901234567890'
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(test_settings, f)
            temp_path = f.name

        try:
            settings.readSettings(temp_path)
            assert settings.palworldServerPort == original_port  # Should remain unchanged
        finally:
            os.unlink(temp_path)

    def test_get_git_hash_success(self):
        """Test getting git hash when git is available."""
        settings = Settings()

        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = 'abc123def456\n'
            mock_run.return_value = mock_result

            hash_value = settings.get_git_hash()
            assert hash_value == 'abc123def456'
            mock_run.assert_called_once()

    def test_get_git_hash_failure(self):
        """Test getting git hash when git command fails."""
        settings = Settings()

        with patch('subprocess.run', side_effect=Exception("Git not found")):
            hash_value = settings.get_git_hash()
            assert hash_value is None

    def test_first_packet_pattern(self):
        """Test that FIRST_PACKET_PATTERN is correctly defined."""
        assert isinstance(FIRST_PACKET_PATTERN, bytes)
        assert FIRST_PACKET_PATTERN == b'\x09\x08\x00'

    def test_auto_generate_session_secret_when_missing(self):
        """Test that sessionSecretKey is auto-generated when missing from settings.yaml."""
        settings = Settings()

        # Create a temporary settings file without sessionSecretKey
        test_settings = {
            'palserver': {
                'exePath': '/path/to/server.exe',
                'adminPassword': 'admin123'
            },
            'web': {
                'password': 'webpass123'
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(test_settings, f)
            temp_path = f.name

        try:
            settings.readSettings(temp_path)

            # Verify that a session secret key was generated
            assert settings.sessionSecretKey is not None
            assert isinstance(settings.sessionSecretKey, str)
            assert len(settings.sessionSecretKey) == 64  # secrets.token_hex(32) produces 64 hex chars
            # Verify it's a valid hex string
            int(settings.sessionSecretKey, 16)  # Should not raise ValueError

            # Verify the key was saved to the session_secret.key file
            session_key_file = os.path.join(os.path.dirname(temp_path), 'session_secret.key')
            assert os.path.exists(session_key_file)
            with open(session_key_file, 'r') as f:
                saved_key = f.read().strip()
            assert saved_key == settings.sessionSecretKey
            assert len(saved_key) == 64
            # Clean up
            os.unlink(session_key_file)
        finally:
            os.unlink(temp_path)

    def test_auto_generate_session_secret_when_none(self):
        """Test that sessionSecretKey is auto-generated when explicitly set to None."""
        settings = Settings()

        # Create a temporary settings file with sessionSecretKey set to None
        test_settings = {
            'palserver': {
                'exePath': '/path/to/server.exe',
                'adminPassword': 'admin123'
            },
            'web': {
                'password': 'webpass123'
            },
            'security': {
                'sessionSecretKey': None
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(test_settings, f)
            temp_path = f.name

        try:
            settings.readSettings(temp_path)

            # Verify that a session secret key was generated
            assert settings.sessionSecretKey is not None
            assert isinstance(settings.sessionSecretKey, str)
            assert len(settings.sessionSecretKey) == 64

            # Verify the key was saved to the session_secret.key file
            session_key_file = os.path.join(os.path.dirname(temp_path), 'session_secret.key')
            assert os.path.exists(session_key_file)
            with open(session_key_file, 'r') as f:
                saved_key = f.read().strip()
            assert saved_key == settings.sessionSecretKey
            # Clean up
            os.unlink(session_key_file)
        finally:
            os.unlink(temp_path)

    def test_preserve_existing_session_secret(self):
        """Test that an existing sessionSecretKey is preserved."""
        settings = Settings()

        existing_secret = 'existing_secret_key_123456789012345678901234567890123456789012345678901234567890'
        test_settings = {
            'palserver': {
                'exePath': '/path/to/server.exe',
                'adminPassword': 'admin123'
            },
            'web': {
                'password': 'webpass123'
            },
            'security': {
                'sessionSecretKey': existing_secret
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(test_settings, f)
            temp_path = f.name

        try:
            settings.readSettings(temp_path)

            # Verify that the existing secret key was preserved
            assert settings.sessionSecretKey == existing_secret

            # Verify the file still has the original key
            with open(temp_path, 'r') as f:
                saved_settings = yaml.safe_load(f)
            assert saved_settings['security']['sessionSecretKey'] == existing_secret
        finally:
            os.unlink(temp_path)

    def test_validate_settings_success(self):
        """Test that validation passes when all mandatory settings are set and server path exists."""
        settings = Settings()

        with self._temp_server_exe() as server_exe_path:
            test_settings = {
                'palserver': {
                    'exePath': server_exe_path,
                    'adminPassword': 'admin123'
                },
                'web': {
                    'password': 'webpass123'
                }
            }

            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                yaml.safe_dump(test_settings, f)
                temp_path = f.name

            try:
                settings.readSettings(temp_path)
                # Validation should pass without raising an exception
                settings.validate_settings()
            finally:
                os.unlink(temp_path)

    def test_validate_settings_missing_palworld_server_exe_path(self):
        """Test that validation fails when palworldServerExePath is missing."""
        settings = Settings()

        test_settings = {
            'server': {
                'adminPassword': 'admin123'
            },
            'web': {
                'password': 'webpass123'
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(test_settings, f)
            temp_path = f.name

        try:
            settings.readSettings(temp_path)
            with pytest.raises(ValueError, match="palworldServerExePath"):
                settings.validate_settings()
        finally:
            os.unlink(temp_path)

    def test_validate_settings_missing_admin_password(self):
        """Test that validation fails when palworldServerAdminPassword is missing."""
        settings = Settings()

        with self._temp_server_exe() as server_exe_path:
            test_settings = {
                'server': {
                    'exePath': server_exe_path
                },
                'web': {
                    'password': 'webpass123'
                }
            }

            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                yaml.safe_dump(test_settings, f)
                temp_path = f.name

            try:
                settings.readSettings(temp_path)
                with pytest.raises(ValueError, match="palworldServerAdminPassword"):
                    settings.validate_settings()
            finally:
                os.unlink(temp_path)

    def test_validate_settings_missing_web_password_when_web_server_enabled(self):
        """Test that validation fails when webPassword is missing and useWebServer is True."""
        settings = Settings()

        with self._temp_server_exe() as server_exe_path:
            test_settings = {
                'server': {
                    'exePath': server_exe_path,
                    'adminPassword': 'admin123'
                },
                'web': {
                    'enabled': True
                }
            }

            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                yaml.safe_dump(test_settings, f)
                temp_path = f.name

            try:
                settings.readSettings(temp_path)
                with pytest.raises(ValueError, match="webPassword"):
                    settings.validate_settings()
            finally:
                os.unlink(temp_path)

    def test_validate_settings_web_password_optional_when_web_server_disabled(self):
        """Test that validation passes when webPassword is missing but useWebServer is False."""
        settings = Settings()

        with self._temp_server_exe() as server_exe_path:
            test_settings = {
                'palserver': {
                    'exePath': server_exe_path,
                    'adminPassword': 'admin123'
                },
                'web': {
                    'enabled': False
                }
            }

            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                yaml.safe_dump(test_settings, f)
                temp_path = f.name

            try:
                settings.readSettings(temp_path)
                # Validation should pass without raising an exception
                settings.validate_settings()
            finally:
                os.unlink(temp_path)

    def test_validate_settings_server_path_does_not_exist(self):
        """Test that validation fails when palworldServerExePath points to a non-existent file."""
        settings = Settings()

        test_settings = {
            'palserver': {
                'exePath': '/nonexistent/path/to/server.exe',
                'adminPassword': 'admin123'
            },
            'web': {
                'password': 'webpass123'
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(test_settings, f)
            temp_path = f.name

        try:
            settings.readSettings(temp_path)
            with pytest.raises(ValueError, match="Palworld server executable does not exist"):
                settings.validate_settings()
        finally:
            os.unlink(temp_path)
